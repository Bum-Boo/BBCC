from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Optional, Set, Tuple

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from ..backend.base import InputBackend
from ..backend.models import BackendState, RawControllerState
from ..domain.controls import (
    CONTROL_DISPLAY_NAMES,
    LEFT_STICK_DOWN,
    LEFT_STICK_LEFT,
    LEFT_STICK_RIGHT,
    LEFT_STICK_UP,
    RIGHT_STICK_DOWN,
    RIGHT_STICK_LEFT,
    RIGHT_STICK_RIGHT,
    RIGHT_STICK_UP,
    canonicalize_control_id,
)
from ..domain.profiles import (
    MAX_PRESET_COUNT,
    MIN_PRESET_COUNT,
    AppConfig,
    AppProfile,
    DeviceProfile,
    MappingAssignment,
    Preset,
    build_blank_app_profile,
    build_blank_preset,
    build_default_device_profile,
    default_assignment_for_process,
    build_default_presets_for_process,
    build_default_media_presets_for_family,
    MAPPING_ACTION_KEYBOARD,
    MAPPING_ACTION_MOUSE_DOUBLE_CLICK,
    MAPPING_ACTION_MOUSE_LEFT_CLICK,
    MAPPING_ACTION_MOUSE_MIDDLE_CLICK,
    MAPPING_ACTION_MOUSE_MOVE,
    MAPPING_ACTION_MOUSE_SCROLL,
    MAPPING_ACTION_MOUSE_RIGHT_CLICK,
    MAPPING_ACTION_MOUSE_WHEEL_DOWN,
    MAPPING_ACTION_MOUSE_WHEEL_LEFT,
    MAPPING_ACTION_MOUSE_WHEEL_RIGHT,
    MAPPING_ACTION_MOUSE_WHEEL_UP,
    is_media_fallback_profile,
    normalize_mapping_action_kind,
)
from ..domain.state import DeviceListEntry, MappingRow, NormalizedControllerState, UiSnapshot
from ..identity import DEFAULT_FALLBACK_PROFILE_NAME
from .autostart import WindowsAutoStartService
from .device_registry import DeviceRegistry
from .keyboard_output import KeyboardShortcutSender
from .normalization import InputNormalizer
from .settings_store import SettingsStore
from .shortcuts import format_shortcut_text, normalize_shortcut_text
from .translations import AVAILABLE_LANGUAGES, normalize_language_code, translate
from ..styles import normalize_theme_id


ANALOG_MOUSE_BASE_PIXELS_PER_TICK = 18.0
ANALOG_SCROLL_BASE_UNITS_PER_TICK = 1.0
ANALOG_DEFAULT_CURVE = 1.7
ANALOG_DEFAULT_SCROLL_CURVE = 1.45
LEFT_STICK_DIRECTION_CONTROLS = (
    LEFT_STICK_LEFT,
    LEFT_STICK_RIGHT,
    LEFT_STICK_UP,
    LEFT_STICK_DOWN,
)
RIGHT_STICK_DIRECTION_CONTROLS = (
    RIGHT_STICK_LEFT,
    RIGHT_STICK_RIGHT,
    RIGHT_STICK_UP,
    RIGHT_STICK_DOWN,
)


class MapperService(QObject):
    snapshot_changed = pyqtSignal(object)
    toast_requested = pyqtSignal(str)

    def __init__(
        self,
        backend: InputBackend,
        normalizer: InputNormalizer,
        store: SettingsStore,
        app_monitor,
        output: KeyboardShortcutSender,
        auto_start: WindowsAutoStartService,
        device_registry: Optional[DeviceRegistry] = None,
        poll_interval_ms: int = 16,
    ) -> None:
        super().__init__()
        self._backend = backend
        self._normalizer = normalizer
        self._store = store
        self._app_monitor = app_monitor
        self._output = output
        self._auto_start = auto_start
        self._poll_interval_ms = poll_interval_ms
        self._device_registry = device_registry or normalizer.device_registry

        self._config: AppConfig = self._store.load()
        self._config.settings.language = normalize_language_code(self._config.settings.language)
        self._config.settings.theme = normalize_theme_id(self._config.settings.theme)
        self._config.settings.auto_start = self._auto_start.is_enabled()

        self._backend_state = BackendState.empty("pygame / SDL2 joystick")
        self._raw_states: Dict[str, RawControllerState] = {}
        self._normalized_states: Dict[str, NormalizedControllerState] = {}
        self._active_controls: Dict[str, Set[str]] = {}
        self._focused_controls: Dict[str, str] = {}
        self._mouse_motion_remainders: Dict[str, Tuple[float, float]] = {}
        self._mouse_scroll_remainders: Dict[str, Tuple[float, float]] = {}
        self._logs: Deque[str] = deque(maxlen=500)
        self._current_process_name = ""

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self._backend_state = self._backend.start()
        self._sync_from_backend(self._backend_state)
        self._log("Mapper started.")
        self._emit_snapshot()
        self._timer.start(self._poll_interval_ms)

    def stop(self) -> None:
        self._timer.stop()
        self._output.release_all()
        self._persist()
        self._backend.stop()

    def current_snapshot(self) -> UiSnapshot:
        return self._build_snapshot()

    def tr(self, key: str, **kwargs: str) -> str:
        return translate(normalize_language_code(self._config.settings.language), key, **kwargs)

    def select_device(self, device_id: str) -> None:
        self._config.selected_device_id = device_id
        self._persist()
        self._emit_snapshot()

    def set_language(self, language: str) -> None:
        self.update_settings(language=language)

    def set_theme(self, theme_id: str) -> None:
        self.update_settings(theme=theme_id)

    def update_settings(self, language: Optional[str] = None, theme: Optional[str] = None) -> None:
        changed = False
        if language is not None:
            normalized_language = normalize_language_code(language)
            if normalized_language != self._config.settings.language:
                self._config.settings.language = normalized_language
                changed = True
        if theme is not None:
            normalized_theme = normalize_theme_id(theme)
            if normalized_theme != self._config.settings.theme:
                self._config.settings.theme = normalized_theme
                changed = True
        if changed:
            self._persist()
            self._emit_snapshot()

    def set_auto_start(self, enabled: bool) -> None:
        self._auto_start.set_enabled(enabled)
        self._config.settings.auto_start = enabled
        self._persist()
        self._emit_snapshot()

    def select_app_profile(self, device_id: str, app_profile_id: str) -> None:
        device = self._ensure_device_profile_by_id(device_id)
        if device is None:
            return
        device.selected_app_profile_id = app_profile_id
        self._persist()
        self._emit_snapshot()

    def add_app_profile(self, device_id: str) -> None:
        device = self._ensure_device_profile_by_id(device_id)
        if device is None:
            return
        app_profile = build_blank_app_profile(
            name="New App {count}".format(count=len(device.app_profiles) + 1),
            process_name="new-app.exe",
            family_id=device.saved_family_id or device.family_override_id,
        )
        device.app_profiles.append(app_profile)
        device.selected_app_profile_id = app_profile.app_profile_id
        self._persist()
        self._emit_snapshot()

    def delete_selected_app_profile(self, device_id: str) -> None:
        device = self._ensure_device_profile_by_id(device_id)
        if device is None or len(device.app_profiles) <= 1:
            return
        selected = device.selected_app_profile()
        device.app_profiles = [
            app_profile
            for app_profile in device.app_profiles
            if app_profile.app_profile_id != selected.app_profile_id
        ]
        device.selected_app_profile_id = device.app_profiles[0].app_profile_id
        self._log(self.tr("app_removed"))
        self._persist()
        self._emit_snapshot()

    def update_selected_app_profile(self, device_id: str, name: str, process_name: str) -> None:
        device = self._ensure_device_profile_by_id(device_id)
        if device is None:
            return
        app_profile = device.selected_app_profile()
        previous_process_name = app_profile.process_name.strip().lower()
        normalized_process_name = process_name.strip().lower() or app_profile.process_name.strip().lower() or "*"
        default_name = DEFAULT_FALLBACK_PROFILE_NAME if normalized_process_name == "*" else "New App"
        app_profile.name = name.strip() or default_name
        app_profile.process_name = normalized_process_name
        if previous_process_name != normalized_process_name:
            if normalized_process_name == "*":
                app_profile.presets = build_default_media_presets_for_family(
                    device.saved_family_id or device.family_override_id
                )
                app_profile.active_preset_index = 0
            elif previous_process_name == "*":
                app_profile.presets = build_default_presets_for_process(
                    normalized_process_name,
                    device.saved_family_id or device.family_override_id,
                )
                app_profile.active_preset_index = 0
        self._persist()
        self._emit_snapshot()

    def select_preset(self, device_id: str, preset_index: int) -> None:
        app_profile = self._selected_app_profile(device_id)
        if app_profile is None:
            return
        app_profile.active_preset_index = max(0, min(preset_index, len(app_profile.presets) - 1))
        self._persist()
        self._emit_snapshot()

    def rename_selected_preset(self, device_id: str, name: str) -> None:
        preset = self._selected_preset(device_id)
        if preset is None:
            return
        preset.name = name.strip() or preset.name
        self._persist()
        self._emit_snapshot()

    def next_selected_preset(self, device_id: str) -> None:
        self._shift_preset(device_id, 1)

    def previous_selected_preset(self, device_id: str) -> None:
        self._shift_preset(device_id, -1)

    def add_preset(self, device_id: str) -> None:
        app_profile = self._selected_app_profile(device_id)
        if app_profile is None or len(app_profile.presets) >= MAX_PRESET_COUNT:
            return
        preset_number = len(app_profile.presets) + 1
        app_profile.presets.append(build_blank_preset("Preset {number}".format(number=preset_number)))
        app_profile.active_preset_index = len(app_profile.presets) - 1
        self._persist()
        self._emit_snapshot()

    def delete_selected_preset(self, device_id: str) -> None:
        app_profile = self._selected_app_profile(device_id)
        if app_profile is None or len(app_profile.presets) <= MIN_PRESET_COUNT:
            return
        del app_profile.presets[app_profile.active_preset_index]
        app_profile.active_preset_index = max(0, app_profile.active_preset_index - 1)
        self._log(self.tr("preset_deleted"))
        self._persist()
        self._emit_snapshot()

    def reset_selected_app_presets(self, device_id: str) -> None:
        app_profile = self._selected_app_profile(device_id)
        if app_profile is None:
            return
        device = self._ensure_device_profile_by_id(device_id)
        family_id = ""
        if device is not None:
            family_id = device.saved_family_id or device.family_override_id
        app_profile.presets = build_default_presets_for_process(app_profile.process_name, family_id)
        app_profile.active_preset_index = 0
        self._log(self.tr("toast_reset"))
        self._toast(self.tr("toast_reset"))
        self._persist()
        self._emit_snapshot()

    def update_mapping(
        self,
        device_id: str,
        control: str,
        shortcut: str,
        label: str,
        action_kind: str = MAPPING_ACTION_KEYBOARD,
    ) -> None:
        preset = self._selected_preset(device_id)
        if preset is None:
            return
        canonical_control = canonicalize_control_id(control)
        normalized_shortcut = normalize_shortcut_text(shortcut.strip())
        normalized_action_kind = normalize_mapping_action_kind(action_kind)
        trimmed_label = label.strip()
        if (
            normalized_action_kind == MAPPING_ACTION_KEYBOARD
            and not normalized_shortcut
            and not trimmed_label
        ):
            preset.mappings.pop(canonical_control, None)
        else:
            preset.mappings[canonical_control] = MappingAssignment(
                control=canonical_control,
                shortcut=normalized_shortcut,
                label=trimmed_label,
                action_kind=normalized_action_kind,
            )
        self._persist()
        self._emit_snapshot()

    def reset_mapping_to_default(self, device_id: str, control: str) -> None:
        device = self._ensure_device_profile_by_id(device_id)
        if device is None:
            return
        app_profile = self._selected_app_profile(device_id)
        preset = self._selected_preset(device_id)
        if app_profile is None or preset is None:
            return

        canonical_control = canonicalize_control_id(control)
        default_assignment = default_assignment_for_process(
            app_profile.process_name,
            device.saved_family_id or device.family_override_id,
            app_profile.active_preset_index,
            canonical_control,
        )
        if (
            default_assignment.action_kind == MAPPING_ACTION_KEYBOARD
            and not default_assignment.shortcut
            and not default_assignment.label
        ):
            preset.mappings.pop(canonical_control, None)
        else:
            preset.mappings[canonical_control] = MappingAssignment(
                control=canonical_control,
                shortcut=default_assignment.shortcut,
                label=default_assignment.label,
                action_kind=default_assignment.action_kind,
            )
        self._persist()
        self._emit_snapshot()

    def _tick(self) -> None:
        update = self._backend.poll()
        self._backend_state = update.state
        for event in update.events:
            self._logs.append(event.format_line())

        self._current_process_name = self._app_monitor.current_process_name()
        self._sync_from_backend(self._backend_state)
        self._run_mappings()
        self._emit_snapshot()

    def _sync_from_backend(self, state: BackendState) -> None:
        self._raw_states = {}
        self._normalized_states = {}

        for raw_state in state.controllers:
            device = self._resolve_or_create_device_profile(raw_state)
            self._raw_states[device.device_id] = raw_state
            normalized_state = self._normalizer.normalize(raw_state, device)
            self._normalized_states[device.device_id] = normalized_state
            if normalized_state.device_family_id not in {"unknown_controller", "standard_controller"}:
                device.saved_family_id = normalized_state.device_family_id

        if not self._config.selected_device_id and self._config.devices:
            self._config.selected_device_id = self._config.devices[0].device_id

    def _run_mappings(self) -> None:
        for device_id, normalized_state in self._normalized_states.items():
            device_profile = self._ensure_device_profile_by_id(device_id)
            if device_profile is None:
                continue

            active_app_profile = self._resolve_active_app_profile(device_profile, self._current_process_name)
            active_controls = {
                control
                for control, control_state in normalized_state.controls.items()
                if control_state.is_active
            }
            previous_controls = self._active_controls.get(device_id, set())
            rising_controls = active_controls - previous_controls
            if rising_controls:
                self._focused_controls[device_id] = self._focus_control(normalized_state, rising_controls)

            allow_preset_switch = not is_media_fallback_profile(active_app_profile)
            if allow_preset_switch and self._handle_preset_switch(device_profile, active_app_profile, rising_controls):
                self._persist()

            reserved_controls = set()
            if allow_preset_switch:
                reserved_controls = {
                    device_profile.preset_switch.previous_control,
                    device_profile.preset_switch.next_control,
                }
            preset = active_app_profile.active_preset()
            move_enabled = self._group_action_enabled(preset, LEFT_STICK_DIRECTION_CONTROLS, MAPPING_ACTION_MOUSE_MOVE)
            scroll_enabled = self._group_action_enabled(
                preset,
                RIGHT_STICK_DIRECTION_CONTROLS,
                MAPPING_ACTION_MOUSE_SCROLL,
            )
            if move_enabled:
                self._dispatch_left_stick_motion(device_profile, active_app_profile, normalized_state)
            else:
                self._mouse_motion_remainders.pop(device_id, None)
            if scroll_enabled:
                self._dispatch_right_stick_scroll(device_profile, active_app_profile, normalized_state)
            else:
                self._mouse_scroll_remainders.pop(device_id, None)

            for control in sorted(rising_controls):
                if control in reserved_controls:
                    continue
                assignment = preset.assignment_for(control)
                if assignment.action_kind in {MAPPING_ACTION_MOUSE_MOVE, MAPPING_ACTION_MOUSE_SCROLL}:
                    continue
                self._dispatch_assignment(device_profile, control, assignment)
            self._active_controls[device_id] = active_controls

        disconnected_device_ids = set(self._active_controls) - set(self._normalized_states)
        for device_id in disconnected_device_ids:
            self._active_controls.pop(device_id, None)
            self._focused_controls.pop(device_id, None)
            self._mouse_motion_remainders.pop(device_id, None)
            self._mouse_scroll_remainders.pop(device_id, None)

    def _handle_preset_switch(
        self,
        device_profile: DeviceProfile,
        app_profile: AppProfile,
        rising_controls: Set[str],
    ) -> bool:
        previous_hit = device_profile.preset_switch.previous_control in rising_controls
        next_hit = device_profile.preset_switch.next_control in rising_controls
        if previous_hit == next_hit:
            return False

        preset_count = len(app_profile.presets)
        if preset_count == 0:
            app_profile.presets = build_default_presets_for_process(
                app_profile.process_name,
                device_profile.saved_family_id or device_profile.family_override_id,
            )
            preset_count = len(app_profile.presets)

        delta = -1 if previous_hit else 1
        app_profile.active_preset_index = (app_profile.active_preset_index + delta) % preset_count
        preset = app_profile.active_preset()
        self._log(
            "Preset -> {device} / {app} / {preset}".format(
                device=device_profile.display_name,
                app=app_profile.name,
                preset=preset.name,
            )
        )
        self._toast(
            self.tr(
                "toast_preset",
                device=device_profile.display_name,
                app=app_profile.name,
                preset=preset.name,
            )
        )
        return True

    def _group_action_enabled(
        self,
        preset: Preset,
        controls: Tuple[str, ...],
        action_kind: str,
    ) -> bool:
        return any(preset.assignment_for(control).action_kind == action_kind for control in controls)

    def _dispatch_left_stick_motion(
        self,
        device_profile: DeviceProfile,
        app_profile: AppProfile,
        normalized_state: NormalizedControllerState,
    ) -> None:
        self._dispatch_analog_vector(
            device_profile=device_profile,
            app_profile=app_profile,
            normalized_state=normalized_state,
            raw_vector=normalized_state.left_stick,
            remainder_store=self._mouse_motion_remainders,
            base_unit=ANALOG_MOUSE_BASE_PIXELS_PER_TICK,
            curve=app_profile.analog_curve or ANALOG_DEFAULT_CURVE,
            sensitivity=app_profile.mouse_sensitivity,
            invert_y=True,
            output_method=self._output.move_mouse,
            output_label="mouse move",
        )

    def _dispatch_right_stick_scroll(
        self,
        device_profile: DeviceProfile,
        app_profile: AppProfile,
        normalized_state: NormalizedControllerState,
    ) -> None:
        self._dispatch_analog_vector(
            device_profile=device_profile,
            app_profile=app_profile,
            normalized_state=normalized_state,
            raw_vector=normalized_state.right_stick,
            remainder_store=self._mouse_scroll_remainders,
            base_unit=ANALOG_SCROLL_BASE_UNITS_PER_TICK,
            curve=app_profile.analog_curve or ANALOG_DEFAULT_SCROLL_CURVE,
            sensitivity=app_profile.scroll_sensitivity,
            invert_y=False,
            output_method=self._output.scroll_mouse,
            output_label="mouse scroll",
        )

    def _dispatch_analog_vector(
        self,
        *,
        device_profile: DeviceProfile,
        app_profile: AppProfile,
        normalized_state: NormalizedControllerState,
        raw_vector: Tuple[float, float],
        remainder_store: Dict[str, Tuple[float, float]],
        base_unit: float,
        curve: float,
        sensitivity: float,
        invert_y: bool,
        output_method,
        output_label: str,
    ) -> None:
        x_value, y_value = raw_vector
        deadzone = max(0.0, min(0.95, app_profile.analog_deadzone))
        scale = self._analog_speed_scale(normalized_state, app_profile)
        scaled_x = self._shape_analog_value(x_value, deadzone, curve) * base_unit * sensitivity * scale
        scaled_y = self._shape_analog_value(y_value, deadzone, curve) * base_unit * sensitivity * scale
        if invert_y:
            scaled_y = -scaled_y

        if scaled_x == 0.0 and scaled_y == 0.0:
            remainder_store.pop(device_profile.device_id, None)
            return

        remainder_x, remainder_y = remainder_store.get(device_profile.device_id, (0.0, 0.0))
        remainder_x = 0.0 if scaled_x == 0.0 else remainder_x + scaled_x
        remainder_y = 0.0 if scaled_y == 0.0 else remainder_y + scaled_y
        emit_x = int(remainder_x)
        emit_y = int(remainder_y)
        remainder_x -= emit_x
        remainder_y -= emit_y
        remainder_store[device_profile.device_id] = (remainder_x, remainder_y)
        if emit_x == 0 and emit_y == 0:
            return

        try:
            output_method(emit_x, emit_y)
        except Exception as exc:
            self._log(
                "Output error for {control}: {error}".format(
                    control=output_label,
                    error=exc,
                )
            )
            return

    def _analog_speed_scale(self, normalized_state: NormalizedControllerState, app_profile: AppProfile) -> float:
        scale = 1.0
        slow_control = canonicalize_control_id(app_profile.slow_modifier_control) if app_profile.slow_modifier_control else ""
        if slow_control:
            slow_state = normalized_state.controls.get(slow_control)
            if slow_state is not None and slow_state.is_active:
                scale *= max(0.1, float(app_profile.slow_speed_multiplier))
        fast_control = canonicalize_control_id(app_profile.fast_modifier_control) if app_profile.fast_modifier_control else ""
        if fast_control:
            fast_state = normalized_state.controls.get(fast_control)
            if fast_state is not None and fast_state.is_active:
                scale *= max(1.0, float(app_profile.fast_speed_multiplier))
        return scale

    def _shape_analog_value(self, value: float, deadzone: float, curve: float) -> float:
        clamped = max(-1.0, min(1.0, float(value)))
        magnitude = abs(clamped)
        if magnitude <= deadzone:
            return 0.0
        normalized = (magnitude - deadzone) / max(0.0001, 1.0 - deadzone)
        curved = normalized ** max(1.0, curve)
        return curved if clamped >= 0.0 else -curved

    def _dispatch_assignment(
        self,
        device_profile: DeviceProfile,
        control: str,
        assignment: MappingAssignment,
    ) -> None:
        if assignment.action_kind == MAPPING_ACTION_MOUSE_LEFT_CLICK:
            error = self._output.click_mouse("left")
        elif assignment.action_kind == MAPPING_ACTION_MOUSE_RIGHT_CLICK:
            error = self._output.click_mouse("right")
        elif assignment.action_kind == MAPPING_ACTION_MOUSE_MIDDLE_CLICK:
            error = self._output.click_mouse("middle")
        elif assignment.action_kind == MAPPING_ACTION_MOUSE_DOUBLE_CLICK:
            error = self._output.click_mouse("left", 2)
        elif assignment.action_kind == MAPPING_ACTION_MOUSE_SCROLL:
            return
        elif assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_UP:
            self._output.scroll_mouse(0, 1)
            error = None
        elif assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_DOWN:
            self._output.scroll_mouse(0, -1)
            error = None
        elif assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_LEFT:
            self._output.scroll_mouse(-1, 0)
            error = None
        elif assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_RIGHT:
            self._output.scroll_mouse(1, 0)
            error = None
        else:
            if not assignment.shortcut:
                return
            error = self._output.send(assignment.shortcut)
        if error:
            self._log(
                "Output error for {control}: {error}".format(
                    control=control,
                    error=error,
                )
            )
            return
        self._log(
            "{device}: {action}".format(
                device=device_profile.display_name,
                action=self._assignment_action_text(assignment, control),
            )
        )

    def _assignment_action_text(self, assignment: MappingAssignment, control: str) -> str:
        if assignment.action_kind == MAPPING_ACTION_MOUSE_MOVE:
            return self.tr("mapping.mouse_pointer_movement")
        if assignment.action_kind == MAPPING_ACTION_MOUSE_SCROLL:
            return self.tr("mapping.mouse_continuous_scroll")
        if assignment.action_kind == MAPPING_ACTION_MOUSE_LEFT_CLICK:
            return self.tr("mapping.mouse_left_click")
        if assignment.action_kind == MAPPING_ACTION_MOUSE_RIGHT_CLICK:
            return self.tr("mapping.mouse_right_click")
        if assignment.action_kind == MAPPING_ACTION_MOUSE_MIDDLE_CLICK:
            return self.tr("mapping.mouse_middle_click")
        if assignment.action_kind == MAPPING_ACTION_MOUSE_DOUBLE_CLICK:
            return self.tr("mapping.mouse_double_click")
        if assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_UP:
            return self.tr("mapping.mouse_wheel_up")
        if assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_DOWN:
            return self.tr("mapping.mouse_wheel_down")
        if assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_LEFT:
            return self.tr("mapping.mouse_wheel_left")
        if assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_RIGHT:
            return self.tr("mapping.mouse_wheel_right")
        return format_shortcut_text(assignment.shortcut) or "-"

    def _resolve_active_app_profile(self, device_profile: DeviceProfile, process_name: str) -> AppProfile:
        wildcard_profile: Optional[AppProfile] = None
        for app_profile in device_profile.app_profiles:
            normalized_process = app_profile.process_name.strip().lower()
            if normalized_process == "*":
                wildcard_profile = app_profile
                continue
            if normalized_process == process_name:
                return app_profile
        if wildcard_profile is not None:
            return wildcard_profile
        return device_profile.selected_app_profile()

    def _selected_app_profile(self, device_id: str) -> Optional[AppProfile]:
        device = self._ensure_device_profile_by_id(device_id)
        if device is None:
            return None
        return device.selected_app_profile()

    def _selected_preset(self, device_id: str) -> Optional[Preset]:
        app_profile = self._selected_app_profile(device_id)
        if app_profile is None:
            return None
        return app_profile.active_preset()

    def _shift_preset(self, device_id: str, delta: int) -> None:
        app_profile = self._selected_app_profile(device_id)
        if app_profile is None or not app_profile.presets:
            return
        app_profile.active_preset_index = (app_profile.active_preset_index + delta) % len(
            app_profile.presets
        )
        preset = app_profile.active_preset()
        device = self._ensure_device_profile_by_id(device_id)
        if device is not None:
            self._toast(
                self.tr(
                    "toast_preset",
                    device=device.display_name,
                    app=app_profile.name,
                    preset=preset.name,
                )
            )
        self._persist()
        self._emit_snapshot()

    def _resolve_or_create_device_profile(self, raw_state: RawControllerState) -> DeviceProfile:
        resolved_family = self._device_registry.resolve_runtime(raw_state.info)
        existing = self._device_registry.find_matching_profile(
            info=raw_state.info,
            existing_devices=self._config.devices,
        )
        if existing is None:
            existing = build_default_device_profile(
                device_id=raw_state.info.device_id,
                display_name=raw_state.info.name,
                guid=raw_state.info.guid,
                family_id=resolved_family.template.family_id,
            )
            self._config.devices.append(existing)
            if not self._config.selected_device_id:
                self._config.selected_device_id = existing.device_id
        previous_device_id = existing.device_id
        existing.device_id = raw_state.info.device_id
        existing.display_name = raw_state.info.name
        existing.guid = raw_state.info.guid
        existing.last_seen_name = raw_state.info.name
        existing.shape_signature = self._device_registry.shape_signature_from_info(raw_state.info)
        if self._config.selected_device_id == previous_device_id:
            self._config.selected_device_id = existing.device_id
        return existing

    def _focus_control(self, normalized_state: NormalizedControllerState, rising_controls: Set[str]) -> str:
        for control in normalized_state.visible_controls:
            if control in rising_controls:
                return control
        return sorted(rising_controls)[0]

    def _ensure_device_profile(self, device_id: str, display_name: str, guid: str) -> DeviceProfile:
        existing = self._config.device_by_id(device_id)
        if existing is not None:
            existing.display_name = display_name
            existing.guid = guid
            return existing
        new_device = build_default_device_profile(device_id=device_id, display_name=display_name, guid=guid)
        self._config.devices.append(new_device)
        if not self._config.selected_device_id:
            self._config.selected_device_id = device_id
        self._persist()
        return new_device

    def _ensure_device_profile_by_id(self, device_id: str) -> Optional[DeviceProfile]:
        return self._config.device_by_id(device_id)

    def _log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._logs.append("[{timestamp}] {message}".format(timestamp=timestamp, message=message))

    def _toast(self, message: str) -> None:
        self.toast_requested.emit(message)

    def _persist(self) -> None:
        self._store.save(self._config)

    def _emit_snapshot(self) -> None:
        self.snapshot_changed.emit(self._build_snapshot())

    def _build_snapshot(self) -> UiSnapshot:
        connected_ids = set(self._raw_states)
        selected_device = self._resolve_selected_device(connected_ids)
        raw_state = self._raw_states.get(selected_device.device_id) if selected_device else None
        normalized_state = self._normalized_states.get(selected_device.device_id) if selected_device else None
        selected_app_profile = selected_device.selected_app_profile() if selected_device else None
        selected_preset = selected_app_profile.active_preset() if selected_app_profile else None

        visible_controls, control_labels = self._resolve_visible_controls(selected_device, normalized_state)
        mapping_rows = self._build_mapping_rows(
            selected_device=selected_device,
            selected_preset=selected_preset,
            normalized_state=normalized_state,
            visible_controls=visible_controls,
            control_labels=control_labels,
        )

        device_entries = tuple(
            DeviceListEntry(
                device_id=device.device_id,
                display_name=device.display_name,
                subtitle=device.last_seen_name or device.display_name,
                is_connected=device.device_id in connected_ids,
                is_selected=device.device_id == (selected_device.device_id if selected_device else ""),
            )
            for device in self._sorted_devices()
        )

        return UiSnapshot(
            backend_name=self._backend_state.backend_name,
            current_process_name=self._current_process_name or "-",
            selected_language=normalize_language_code(self._config.settings.language),
            selected_theme=normalize_theme_id(self._config.settings.theme),
            has_connected_devices=bool(connected_ids),
            focused_control=self._focused_controls.get(selected_device.device_id, "") if selected_device else "",
            selected_device_id=selected_device.device_id if selected_device else "",
            device_entries=device_entries,
            selected_device_profile=selected_device,
            selected_app_profile=selected_app_profile,
            selected_preset=selected_preset,
            raw_state=raw_state,
            normalized_state=normalized_state,
            mapping_rows=tuple(mapping_rows),
            logs=tuple(self._logs),
            available_languages=AVAILABLE_LANGUAGES,
            auto_start_enabled=self._config.settings.auto_start,
        )

    def _resolve_selected_device(self, connected_ids: Set[str]) -> Optional[DeviceProfile]:
        selected_device = self._config.device_by_id(self._config.selected_device_id)
        if selected_device is not None:
            return selected_device
        if connected_ids:
            first_connected = self._first_connected_device(connected_ids)
            if first_connected is not None:
                self._config.selected_device_id = first_connected.device_id
                return first_connected
        if self._config.devices:
            self._config.selected_device_id = self._config.devices[0].device_id
            return self._config.devices[0]
        return None

    def _first_connected_device(self, connected_ids: Set[str]) -> Optional[DeviceProfile]:
        for device in self._sorted_devices():
            if device.device_id in connected_ids:
                return device
        return None

    def _resolve_visible_controls(
        self,
        selected_device: Optional[DeviceProfile],
        normalized_state: Optional[NormalizedControllerState],
    ) -> Tuple[Tuple[str, ...], Dict[str, str]]:
        if normalized_state is not None:
            return normalized_state.visible_controls, dict(normalized_state.control_labels)
        if selected_device is None:
            return (), {}
        resolved_family = self._normalizer.describe_saved_device(selected_device)
        return resolved_family.template.visible_controls, dict(resolved_family.template.control_labels)

    def _build_mapping_rows(
        self,
        selected_device: Optional[DeviceProfile],
        selected_preset: Optional[Preset],
        normalized_state: Optional[NormalizedControllerState],
        visible_controls: Tuple[str, ...],
        control_labels: Dict[str, str],
    ) -> List[MappingRow]:
        if selected_device is None:
            return []

        previous_control = canonicalize_control_id(selected_device.preset_switch.previous_control)
        next_control = canonicalize_control_id(selected_device.preset_switch.next_control)
        allow_preset_switch = not is_media_fallback_profile(selected_device.selected_app_profile())
        rows: List[MappingRow] = []

        for control in visible_controls:
            is_active = False
            if normalized_state is not None and control in normalized_state.controls:
                is_active = normalized_state.controls[control].is_active

            assignment = selected_preset.assignment_for(control) if selected_preset else MappingAssignment(control)
            system_text = ""
            is_system_action = False
            if allow_preset_switch and control == previous_control:
                system_text = self.tr("system_prev")
                is_system_action = True
            elif allow_preset_switch and control == next_control:
                system_text = self.tr("system_next")
                is_system_action = True

            rows.append(
                MappingRow(
                    control=control,
                    button_name=control_labels.get(control, CONTROL_DISPLAY_NAMES.get(control, control)),
                    shortcut=format_shortcut_text(assignment.shortcut),
                    action_kind=assignment.action_kind,
                    action_text=self._assignment_action_text(assignment, control),
                    label=assignment.label,
                    is_active=is_active,
                    is_system_action=is_system_action,
                    system_text=system_text,
                )
            )
        return rows

    def _sorted_devices(self) -> List[DeviceProfile]:
        connected_ids = set(self._raw_states)
        return sorted(
            self._config.devices,
            key=lambda device: (device.device_id not in connected_ids, device.display_name.lower()),
        )
