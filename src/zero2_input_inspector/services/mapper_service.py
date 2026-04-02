from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import datetime
from time import monotonic
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
    RIGHT_STICK_EFFECTIVE_DOWN,
    RIGHT_STICK_EFFECTIVE_LEFT,
    RIGHT_STICK_EFFECTIVE_RIGHT,
    RIGHT_STICK_EFFECTIVE_UP,
    RIGHT_STICK_MODE,
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
    MAPPING_ACTION_STICK_MODE,
    RIGHT_STICK_MODE_CONTINUOUS_SCROLL,
    RIGHT_STICK_MODE_CUSTOM_ADVANCED,
    RIGHT_STICK_MODE_DISABLED,
    RIGHT_STICK_MODE_MOUSE_MOVE,
    RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
    RIGHT_STICK_MODE_WHEEL_STEP_VERTICAL,
    is_media_fallback_profile,
    normalize_mapping_action_kind,
    normalize_right_stick_mode,
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
SINGLE_FIRE_COOLDOWN_SECONDS = 0.18
WHEEL_REPEAT_INTERVAL_SECONDS = 0.14
RIGHT_STICK_IDLE_BASELINE_MAX = 0.18
RIGHT_STICK_BASELINE_UPDATE_ALPHA = 0.2
RIGHT_STICK_WHEEL_DOMINANCE_MARGIN = 0.08
RIGHT_STICK_NEUTRAL_LATCH_SECONDS = 0.12
XBOX_WHEEL_STEP_DEADZONE = 0.18
XBOX_WHEEL_STEP_ACTIVATION_THRESHOLD = 0.34
XBOX_WHEEL_STEP_DOMINANCE_MARGIN = 0.03
XBOX_WHEEL_STEP_NEUTRAL_LATCH_SECONDS = 0.05
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
RIGHT_STICK_EFFECTIVE_ROWS = {
    RIGHT_STICK_UP: RIGHT_STICK_EFFECTIVE_UP,
    RIGHT_STICK_DOWN: RIGHT_STICK_EFFECTIVE_DOWN,
    RIGHT_STICK_LEFT: RIGHT_STICK_EFFECTIVE_LEFT,
    RIGHT_STICK_RIGHT: RIGHT_STICK_EFFECTIVE_RIGHT,
}


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
        self._single_fire_last_fired: Dict[str, Dict[str, float]] = {}
        self._wheel_repeat_last_fired: Dict[str, Dict[str, float]] = {}
        self._wheel_neutral_latches: Dict[str, Dict[str, object]] = {}
        self._mouse_motion_remainders: Dict[str, Tuple[float, float]] = {}
        self._mouse_scroll_remainders: Dict[str, Tuple[float, float]] = {}
        self._right_stick_baselines: Dict[str, Tuple[float, float]] = {}
        self._right_stick_diagnostics: Dict[str, Dict[str, object]] = {}
        self._active_profile_signatures: Dict[str, Tuple[str, str]] = {}
        self._logs: Deque[str] = deque(maxlen=500)
        self._current_process_name = ""
        self._log_load_report()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self._backend_state = self._backend.start()
        self._sync_from_backend(self._backend_state)
        self._log("Mapper started.")
        self._emit_snapshot()
        self._timer.start(self._poll_interval_ms)

    @property
    def normalizer(self) -> InputNormalizer:
        return self._normalizer

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
        family_id = self._resolve_app_family_id(device, app_profile)
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
        device = self._ensure_device_profile_by_id(device_id)
        app_profile = self._selected_app_profile(device_id)
        preset = self._selected_preset(device_id)
        if device is None or app_profile is None or preset is None:
            return
        canonical_control = canonicalize_control_id(control)
        if canonical_control == RIGHT_STICK_MODE or normalize_mapping_action_kind(action_kind) == MAPPING_ACTION_STICK_MODE:
            self._apply_right_stick_mode_to_preset(preset, shortcut)
            self._persist()
            self._emit_snapshot()
            return
        normalized_shortcut = normalize_shortcut_text(shortcut.strip())
        normalized_action_kind = normalize_mapping_action_kind(action_kind)
        trimmed_label = label.strip()
        default_assignment = default_assignment_for_process(
            app_profile.process_name,
            self._resolve_app_family_id(device, app_profile),
            app_profile.active_preset_index,
            canonical_control,
        )
        previous_assignment = preset.assignment_for(canonical_control)
        if (
            normalized_action_kind == default_assignment.action_kind
            and normalized_shortcut == normalize_shortcut_text(default_assignment.shortcut)
        ):
            trimmed_label = default_assignment.label
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
            self._resolve_app_family_id(device, app_profile),
            app_profile.active_preset_index,
            canonical_control,
        )
        if default_assignment.action_kind == MAPPING_ACTION_STICK_MODE:
            self._apply_right_stick_mode_to_preset(preset, default_assignment.shortcut)
            self._persist()
            self._emit_snapshot()
            return
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
            preset = active_app_profile.active_preset()
            profile_signature = (active_app_profile.app_profile_id, preset.preset_id)
            if self._active_profile_signatures.get(device_id) != profile_signature:
                self._reset_right_stick_runtime_state(device_id)
                self._active_profile_signatures[device_id] = profile_signature
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
            right_stick_vector = self._stabilize_right_stick_vector(device_id, normalized_state.right_stick)
            self._update_input_diagnostics(
                device_profile=device_profile,
                app_profile=active_app_profile,
                preset=preset,
                normalized_state=normalized_state,
                active_controls=active_controls,
                rising_controls=rising_controls,
            )
            right_stick_mode = normalize_right_stick_mode(preset.right_stick_mode)
            move_directions = self._analog_action_directions(
                preset,
                LEFT_STICK_DIRECTION_CONTROLS,
                MAPPING_ACTION_MOUSE_MOVE,
            )
            if any(move_directions):
                self._dispatch_left_stick_motion(
                    device_profile,
                    active_app_profile,
                    normalized_state,
                    move_directions,
                )
            else:
                self._mouse_motion_remainders.pop(device_id, None)
            if right_stick_mode == RIGHT_STICK_MODE_CONTINUOUS_SCROLL:
                self._dispatch_right_stick_scroll(
                    device_profile,
                    active_app_profile,
                    normalized_state,
                    right_stick_vector,
                    (True, True, True, True),
                )
            elif right_stick_mode == RIGHT_STICK_MODE_MOUSE_MOVE:
                self._dispatch_analog_vector(
                    device_profile=device_profile,
                    app_profile=active_app_profile,
                    normalized_state=normalized_state,
                    raw_vector=right_stick_vector,
                    remainder_store=self._mouse_motion_remainders,
                    base_unit=ANALOG_MOUSE_BASE_PIXELS_PER_TICK,
                    deadzone=active_app_profile.analog_deadzone,
                    activation_threshold=None,
                    curve=active_app_profile.analog_curve or ANALOG_DEFAULT_CURVE,
                    sensitivity=active_app_profile.mouse_sensitivity,
                    invert_y=True,
                    enabled_directions=(True, True, True, True),
                    output_method=self._output.move_mouse,
                    output_label="mouse move",
                )
            elif right_stick_mode == RIGHT_STICK_MODE_CUSTOM_ADVANCED:
                scroll_directions = self._analog_action_directions(
                    preset,
                    RIGHT_STICK_DIRECTION_CONTROLS,
                    MAPPING_ACTION_MOUSE_SCROLL,
                )
                if any(scroll_directions):
                    self._dispatch_right_stick_scroll(
                        device_profile,
                        active_app_profile,
                        normalized_state,
                        right_stick_vector,
                        scroll_directions,
                    )
                else:
                    self._mouse_scroll_remainders.pop(device_id, None)
                self._dispatch_right_stick_wheel_actions(
                    device_profile,
                    active_app_profile,
                    normalized_state,
                    preset,
                    right_stick_vector,
                    canonical_source="right_stick_mode:custom_advanced",
                )
            else:
                self._mouse_scroll_remainders.pop(device_id, None)
            if right_stick_mode in {
                RIGHT_STICK_MODE_WHEEL_STEP_VERTICAL,
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
            }:
                self._dispatch_right_stick_wheel_step_mode(
                    device_profile,
                    active_app_profile,
                    normalized_state,
                    preset,
                    right_stick_vector,
                    right_stick_mode,
                )

            for control in sorted(rising_controls):
                if control in reserved_controls:
                    continue
                assignment = preset.assignment_for(control)
                if assignment.action_kind in {MAPPING_ACTION_MOUSE_MOVE, MAPPING_ACTION_MOUSE_SCROLL}:
                    continue
                if (
                    control in RIGHT_STICK_DIRECTION_CONTROLS
                    and assignment.action_kind in {
                        MAPPING_ACTION_MOUSE_WHEEL_UP,
                        MAPPING_ACTION_MOUSE_WHEEL_DOWN,
                        MAPPING_ACTION_MOUSE_WHEEL_LEFT,
                        MAPPING_ACTION_MOUSE_WHEEL_RIGHT,
                    }
                ):
                    continue
                if not self._should_dispatch_assignment(device_id, control, assignment):
                    continue
                self._dispatch_assignment(device_profile, control, assignment)
            self._active_controls[device_id] = active_controls
            self._prune_single_fire_state(device_id, active_controls)

        disconnected_device_ids = set(self._active_controls) - set(self._normalized_states)
        for device_id in disconnected_device_ids:
            self._active_controls.pop(device_id, None)
            self._focused_controls.pop(device_id, None)
            self._single_fire_last_fired.pop(device_id, None)
            self._wheel_repeat_last_fired.pop(device_id, None)
            self._wheel_neutral_latches.pop(device_id, None)
            self._mouse_motion_remainders.pop(device_id, None)
            self._mouse_scroll_remainders.pop(device_id, None)
            self._right_stick_baselines.pop(device_id, None)
            self._right_stick_diagnostics.pop(device_id, None)
            self._active_profile_signatures.pop(device_id, None)

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

    def _analog_action_directions(
        self,
        preset: Preset,
        controls: Tuple[str, ...],
        action_kind: str,
    ) -> Tuple[bool, ...]:
        return tuple(
            preset.assignment_for(control).action_kind == action_kind
            for control in controls
        )

    def _dispatch_left_stick_motion(
        self,
        device_profile: DeviceProfile,
        app_profile: AppProfile,
        normalized_state: NormalizedControllerState,
        enabled_directions: Tuple[bool, bool, bool, bool],
    ) -> None:
        self._dispatch_analog_vector(
            device_profile=device_profile,
            app_profile=app_profile,
            normalized_state=normalized_state,
            raw_vector=normalized_state.left_stick,
            remainder_store=self._mouse_motion_remainders,
            base_unit=ANALOG_MOUSE_BASE_PIXELS_PER_TICK,
            deadzone=app_profile.analog_deadzone,
            activation_threshold=None,
            curve=app_profile.analog_curve or ANALOG_DEFAULT_CURVE,
            sensitivity=app_profile.mouse_sensitivity,
            invert_y=True,
            enabled_directions=enabled_directions,
            output_method=self._output.move_mouse,
            output_label="mouse move",
        )

    def _dispatch_right_stick_scroll(
        self,
        device_profile: DeviceProfile,
        app_profile: AppProfile,
        normalized_state: NormalizedControllerState,
        stabilized_vector: Tuple[float, float],
        enabled_directions: Tuple[bool, bool, bool, bool],
    ) -> None:
        self._dispatch_analog_vector(
            device_profile=device_profile,
            app_profile=app_profile,
            normalized_state=normalized_state,
            raw_vector=stabilized_vector,
            remainder_store=self._mouse_scroll_remainders,
            base_unit=ANALOG_SCROLL_BASE_UNITS_PER_TICK,
            deadzone=app_profile.scroll_deadzone,
            activation_threshold=app_profile.scroll_activation_threshold,
            curve=app_profile.analog_curve or ANALOG_DEFAULT_SCROLL_CURVE,
            sensitivity=app_profile.scroll_sensitivity,
            invert_y=False,
            enabled_directions=enabled_directions,
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
        deadzone: float,
        activation_threshold: Optional[float],
        curve: float,
        sensitivity: float,
        invert_y: bool,
        enabled_directions: Tuple[bool, bool, bool, bool],
        output_method,
        output_label: str,
    ) -> None:
        x_value, y_value = raw_vector
        left_enabled, right_enabled, up_enabled, down_enabled = enabled_directions
        x_value = self._filter_analog_component(x_value, negative_enabled=left_enabled, positive_enabled=right_enabled)
        y_value = self._filter_analog_component(y_value, negative_enabled=down_enabled, positive_enabled=up_enabled)
        deadzone = max(0.0, min(0.95, deadzone))
        threshold = deadzone if activation_threshold is None else max(deadzone, min(0.98, activation_threshold))
        if abs(x_value) < threshold:
            x_value = 0.0
        if abs(y_value) < threshold:
            y_value = 0.0
        scale = self._analog_speed_scale(normalized_state, app_profile)
        scaled_x = self._shape_analog_value(x_value, deadzone, curve) * base_unit * sensitivity * scale
        scaled_y = self._shape_analog_value(y_value, deadzone, curve) * base_unit * sensitivity * scale
        if invert_y:
            scaled_y = -scaled_y

        diagnostics = self._right_stick_diagnostics.setdefault(device_profile.device_id, {})
        if output_label == "mouse scroll":
            diagnostics["scroll_shaped_vector"] = (round(scaled_x, 4), round(scaled_y, 4))
            diagnostics["scroll_deadzone"] = round(deadzone, 4)
            diagnostics["scroll_activation_threshold"] = round(threshold, 4)

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
        if output_label == "mouse scroll":
            diagnostics["scroll_emitted"] = (emit_x, emit_y)
            self._record_analog_scroll_emission(device_profile.device_id, emit_x, emit_y)
            self._log(
                "RS scroll -> raw={raw} stabilized={stabilized} shaped=({sx:.3f}, {sy:.3f}) emit=({ex}, {ey})".format(
                    raw=diagnostics.get("raw_vector"),
                    stabilized=diagnostics.get("stabilized_vector"),
                    sx=scaled_x,
                    sy=scaled_y,
                    ex=emit_x,
                    ey=emit_y,
                )
            )

    def _filter_analog_component(
        self,
        value: float,
        *,
        negative_enabled: bool,
        positive_enabled: bool,
    ) -> float:
        signed_value = float(value)
        if signed_value < 0.0 and not negative_enabled:
            return 0.0
        if signed_value > 0.0 and not positive_enabled:
            return 0.0
        if not negative_enabled and not positive_enabled:
            return 0.0
        return signed_value

    def _stabilize_right_stick_vector(
        self,
        device_id: str,
        raw_vector: Tuple[float, float],
    ) -> Tuple[float, float]:
        raw_x, raw_y = (float(raw_vector[0]), float(raw_vector[1]))
        baseline_x, baseline_y = self._right_stick_baselines.get(device_id, (0.0, 0.0))
        if max(abs(raw_x), abs(raw_y)) <= RIGHT_STICK_IDLE_BASELINE_MAX:
            if device_id not in self._right_stick_baselines:
                baseline_x, baseline_y = raw_x, raw_y
            else:
                baseline_x = ((1.0 - RIGHT_STICK_BASELINE_UPDATE_ALPHA) * baseline_x) + (
                    RIGHT_STICK_BASELINE_UPDATE_ALPHA * raw_x
                )
                baseline_y = ((1.0 - RIGHT_STICK_BASELINE_UPDATE_ALPHA) * baseline_y) + (
                    RIGHT_STICK_BASELINE_UPDATE_ALPHA * raw_y
                )
            self._right_stick_baselines[device_id] = (baseline_x, baseline_y)
        stabilized = (
            max(-1.0, min(1.0, raw_x - baseline_x)),
            max(-1.0, min(1.0, raw_y - baseline_y)),
        )
        diagnostics = self._right_stick_diagnostics.setdefault(device_id, {})
        diagnostics["raw_vector"] = (round(raw_x, 4), round(raw_y, 4))
        diagnostics["baseline_vector"] = (round(baseline_x, 4), round(baseline_y, 4))
        diagnostics["stabilized_vector"] = (round(stabilized[0], 4), round(stabilized[1], 4))
        return stabilized

    def input_diagnostics(self, device_id: str) -> Dict[str, object]:
        return deepcopy(self._right_stick_diagnostics.get(device_id, {}))

    def right_stick_diagnostics(self, device_id: str) -> Dict[str, object]:
        return self.input_diagnostics(device_id)

    def _wheel_step_gate_config(
        self,
        app_profile: AppProfile,
        normalized_state: NormalizedControllerState,
    ) -> Dict[str, float | bool]:
        neutral_threshold = max(0.0, min(0.95, app_profile.scroll_deadzone))
        activation_threshold = max(neutral_threshold, min(0.98, app_profile.scroll_activation_threshold))
        dominance_margin = RIGHT_STICK_WHEEL_DOMINANCE_MARGIN
        neutral_latch_seconds = RIGHT_STICK_NEUTRAL_LATCH_SECONDS
        xbox_tuned = normalized_state.device_family_id == "xbox"
        if xbox_tuned:
            neutral_threshold = min(neutral_threshold, XBOX_WHEEL_STEP_DEADZONE)
            activation_threshold = min(
                max(neutral_threshold, activation_threshold),
                XBOX_WHEEL_STEP_ACTIVATION_THRESHOLD,
            )
            dominance_margin = min(dominance_margin, XBOX_WHEEL_STEP_DOMINANCE_MARGIN)
            neutral_latch_seconds = min(neutral_latch_seconds, XBOX_WHEEL_STEP_NEUTRAL_LATCH_SECONDS)
        return {
            "neutral_threshold": round(neutral_threshold, 4),
            "activation_threshold": round(activation_threshold, 4),
            "dominance_margin": round(dominance_margin, 4),
            "neutral_latch_seconds": round(neutral_latch_seconds, 4),
            "xbox_tuned": xbox_tuned,
        }

    def _dispatch_right_stick_wheel_actions(
        self,
        device_profile: DeviceProfile,
        app_profile: AppProfile,
        normalized_state: NormalizedControllerState,
        preset: Preset,
        stabilized_vector: Tuple[float, float],
        canonical_source: str = "",
    ) -> None:
        diagnostics = self._right_stick_diagnostics.setdefault(device_profile.device_id, {})
        gate_config = self._wheel_step_gate_config(app_profile, normalized_state)
        diagnostics["wheel_gate_config"] = gate_config
        diagnostics["wheel_deadzone"] = gate_config["neutral_threshold"]
        diagnostics["wheel_activation_threshold"] = gate_config["activation_threshold"]
        now = monotonic()
        neutral_threshold = float(gate_config["neutral_threshold"])
        threshold = float(gate_config["activation_threshold"])
        dominance_margin = float(gate_config["dominance_margin"])
        neutral_latch_seconds = float(gate_config["neutral_latch_seconds"])
        repeat_store = self._wheel_repeat_last_fired.setdefault(device_profile.device_id, {})
        diagnostics["wheel_gate_reason"] = ""

        neutral_armed = True
        latch_state: Dict[str, object] = {
            "armed": True,
            "neutral_since": None,
            "required": False,
        }
        if normalized_state.device_family_id == "xbox":
            neutral_armed, latch_state = self._update_wheel_neutral_latch(
                device_profile.device_id,
                stabilized_vector,
                neutral_threshold,
                now,
                neutral_latch_seconds,
            )
        diagnostics["wheel_neutral_latch"] = {
            "armed": bool(latch_state.get("armed")),
            "neutral_since": (
                round(float(latch_state["neutral_since"]), 4)
                if latch_state.get("neutral_since") is not None
                else None
            ),
            "required": bool(latch_state.get("required")),
            "neutral_threshold": round(neutral_threshold, 4),
            "duration_seconds": neutral_latch_seconds,
        }

        x_value, y_value = stabilized_vector
        abs_x = abs(x_value)
        abs_y = abs(y_value)
        is_neutral = max(abs_x, abs_y) < neutral_threshold
        vertical_ready = abs_y >= threshold
        horizontal_ready = abs_x >= threshold
        dominant_control = ""
        if abs_y >= threshold and abs_y > abs_x + dominance_margin:
            dominant_control = RIGHT_STICK_UP if y_value > 0.0 else RIGHT_STICK_DOWN
        elif abs_x >= threshold and abs_x > abs_y + dominance_margin:
            dominant_control = RIGHT_STICK_RIGHT if x_value > 0.0 else RIGHT_STICK_LEFT
        diagnostics["wheel_vector_analysis"] = {
            "abs_x": round(abs_x, 4),
            "abs_y": round(abs_y, 4),
            "dominance_margin": round(dominance_margin, 4),
            "dominant_control": dominant_control,
            "dominant_axis": (
                "vertical"
                if dominant_control in {RIGHT_STICK_UP, RIGHT_STICK_DOWN}
                else "horizontal"
                if dominant_control in {RIGHT_STICK_LEFT, RIGHT_STICK_RIGHT}
                else ""
            ),
            "vertical_dominance_passed": dominant_control in {RIGHT_STICK_UP, RIGHT_STICK_DOWN},
            "horizontal_dominance_passed": dominant_control in {RIGHT_STICK_LEFT, RIGHT_STICK_RIGHT},
            "vertical_ready": vertical_ready,
            "horizontal_ready": horizontal_ready,
            "is_neutral": is_neutral,
        }
        if is_neutral:
            self._clear_wheel_repeat_state(device_profile.device_id, "neutral")
            diagnostics["wheel_gate_reason"] = "below_deadzone"
            diagnostics["wheel_repeat_active_control"] = ""
            return

        active_control = ""
        active_assignment: Optional[MappingAssignment] = None
        for control, direction_value in (
            (RIGHT_STICK_LEFT, max(0.0, -x_value)),
            (RIGHT_STICK_RIGHT, max(0.0, x_value)),
            (RIGHT_STICK_UP, max(0.0, y_value)),
            (RIGHT_STICK_DOWN, max(0.0, -y_value)),
        ):
            assignment = preset.assignment_for(control)
            is_wheel_assignment = assignment.action_kind in {
                MAPPING_ACTION_MOUSE_WHEEL_UP,
                MAPPING_ACTION_MOUSE_WHEEL_DOWN,
                MAPPING_ACTION_MOUSE_WHEEL_LEFT,
                MAPPING_ACTION_MOUSE_WHEEL_RIGHT,
            }
            is_dominant = control == dominant_control
            is_active = neutral_armed and is_wheel_assignment and is_dominant
            if assignment.action_kind not in {
                MAPPING_ACTION_MOUSE_WHEEL_UP,
                MAPPING_ACTION_MOUSE_WHEEL_DOWN,
                MAPPING_ACTION_MOUSE_WHEEL_LEFT,
                MAPPING_ACTION_MOUSE_WHEEL_RIGHT,
            }:
                repeat_store.pop(control, None)
            diagnostics["wheel_{control}".format(control=control)] = {
                "value": round(direction_value, 4),
                "active": is_active,
                "dominant": is_dominant,
                "eligible": is_wheel_assignment,
                "action_kind": assignment.action_kind,
            }
            if is_active:
                active_control = control
                active_assignment = assignment

        if not neutral_armed:
            self._clear_wheel_repeat_state(device_profile.device_id, "awaiting_neutral_latch")
            diagnostics["wheel_gate_reason"] = "awaiting_neutral_latch"
            diagnostics["wheel_repeat_active_control"] = ""
            return
        if not vertical_ready and not horizontal_ready:
            self._clear_wheel_repeat_state(device_profile.device_id, "below_activation_threshold")
            diagnostics["wheel_gate_reason"] = "below_activation_threshold"
            diagnostics["wheel_repeat_active_control"] = ""
            return
        if not dominant_control:
            self._clear_wheel_repeat_state(device_profile.device_id, "dominance_failed")
            diagnostics["wheel_gate_reason"] = "dominance_failed"
            diagnostics["wheel_repeat_active_control"] = ""
            return
        if not active_control or active_assignment is None:
            self._clear_wheel_repeat_state(device_profile.device_id, "direction_unassigned")
            diagnostics["wheel_gate_reason"] = "direction_unassigned"
            diagnostics["wheel_repeat_active_control"] = ""
            return

        current_repeat_control = next(iter(repeat_store), "")
        if current_repeat_control and current_repeat_control != active_control:
            self._clear_wheel_repeat_state(device_profile.device_id, "direction_flip")
            repeat_store = self._wheel_repeat_last_fired.setdefault(device_profile.device_id, {})

        diagnostics["wheel_repeat_active_control"] = active_control
        last_fired_at = repeat_store.get(active_control)
        if last_fired_at is not None and now - last_fired_at < WHEEL_REPEAT_INTERVAL_SECONDS:
            diagnostics["wheel_gate_reason"] = "repeat_cooldown"
            return

        repeat_store[active_control] = now
        self._dispatch_assignment(
            device_profile,
            active_control,
            active_assignment,
            canonical_source=canonical_source,
        )
        diagnostics["wheel_emitted"] = {
            "control": active_control,
            "action_kind": active_assignment.action_kind,
            "canonical_source": canonical_source or "assignment:{control}".format(control=active_control),
        }
        diagnostics["wheel_gate_reason"] = {
            RIGHT_STICK_UP: "emitted_wheel_up",
            RIGHT_STICK_DOWN: "emitted_wheel_down",
            RIGHT_STICK_LEFT: "emitted_wheel_left",
            RIGHT_STICK_RIGHT: "emitted_wheel_right",
        }.get(active_control, "emitted")
        self._log(
            "RS wheel -> reason={reason} control={control} raw={raw} stabilized={stabilized} action={action}".format(
                reason=diagnostics["wheel_gate_reason"],
                control=active_control,
                raw=diagnostics.get("raw_vector"),
                stabilized=diagnostics.get("stabilized_vector"),
                action=active_assignment.action_kind,
            )
        )

        if not repeat_store:
            self._wheel_repeat_last_fired.pop(device_profile.device_id, None)

    def _dispatch_right_stick_wheel_step_mode(
        self,
        device_profile: DeviceProfile,
        app_profile: AppProfile,
        normalized_state: NormalizedControllerState,
        preset: Preset,
        stabilized_vector: Tuple[float, float],
        right_stick_mode: str,
    ) -> None:
        normalized_mode = normalize_right_stick_mode(right_stick_mode)
        diagnostics = self._right_stick_diagnostics.setdefault(device_profile.device_id, {})
        diagnostics["right_stick_mode"] = normalized_mode
        diagnostics["right_stick_canonical_source"] = "right_stick_mode:{mode}".format(mode=normalized_mode)
        temp_preset = Preset(
            preset_id=preset.preset_id,
            name=preset.name,
            right_stick_mode=preset.right_stick_mode,
            mappings=self._right_stick_wheel_step_assignments(normalized_mode),
        )
        self._dispatch_right_stick_wheel_actions(
            device_profile,
            app_profile,
            normalized_state,
            temp_preset,
            stabilized_vector,
            canonical_source="right_stick_mode:{mode}".format(mode=normalized_mode),
        )

    def _dispatch_right_stick_wheel_mode(
        self,
        device_profile: DeviceProfile,
        app_profile: AppProfile,
        normalized_state: NormalizedControllerState,
        preset: Preset,
        stabilized_vector: Tuple[float, float],
    ) -> None:
        self._dispatch_right_stick_wheel_step_mode(
            device_profile,
            app_profile,
            normalized_state,
            preset,
            stabilized_vector,
            RIGHT_STICK_MODE_WHEEL_STEP_VERTICAL,
        )

    def _right_stick_wheel_step_assignments(self, right_stick_mode: str) -> Dict[str, MappingAssignment]:
        normalized_mode = normalize_right_stick_mode(right_stick_mode)
        assignments: Dict[str, MappingAssignment] = {
            RIGHT_STICK_UP: MappingAssignment(
                control=RIGHT_STICK_UP,
                action_kind=MAPPING_ACTION_MOUSE_WHEEL_UP,
            ),
            RIGHT_STICK_DOWN: MappingAssignment(
                control=RIGHT_STICK_DOWN,
                action_kind=MAPPING_ACTION_MOUSE_WHEEL_DOWN,
            ),
        }
        if normalized_mode == RIGHT_STICK_MODE_WHEEL_STEP_4WAY:
            assignments[RIGHT_STICK_LEFT] = MappingAssignment(
                control=RIGHT_STICK_LEFT,
                action_kind=MAPPING_ACTION_MOUSE_WHEEL_LEFT,
            )
            assignments[RIGHT_STICK_RIGHT] = MappingAssignment(
                control=RIGHT_STICK_RIGHT,
                action_kind=MAPPING_ACTION_MOUSE_WHEEL_RIGHT,
            )
        return assignments

    def _update_wheel_neutral_latch(
        self,
        device_id: str,
        stabilized_vector: Tuple[float, float],
        neutral_threshold: float,
        now: float,
        neutral_latch_seconds: float,
    ) -> Tuple[bool, Dict[str, object]]:
        latch_state = self._wheel_neutral_latches.setdefault(
            device_id,
            {
                "armed": False,
                "neutral_since": None,
                "required": True,
            },
        )
        in_neutral = max(abs(stabilized_vector[0]), abs(stabilized_vector[1])) < neutral_threshold
        if in_neutral:
            if latch_state.get("neutral_since") is None:
                latch_state["neutral_since"] = now
            elif not latch_state.get("armed") and now - float(latch_state["neutral_since"]) >= neutral_latch_seconds:
                latch_state["armed"] = True
        elif not latch_state.get("armed"):
            latch_state["neutral_since"] = None
        else:
            latch_state["neutral_since"] = None
        return bool(latch_state.get("armed")), latch_state

    def _clear_wheel_repeat_state(self, device_id: str, reason: str) -> None:
        self._wheel_repeat_last_fired.pop(device_id, None)
        diagnostics = self._right_stick_diagnostics.setdefault(device_id, {})
        diagnostics["wheel_repeat_reset_reason"] = reason

    def _reset_right_stick_runtime_state(self, device_id: str) -> None:
        self._clear_wheel_repeat_state(device_id, "profile_changed")
        self._wheel_neutral_latches.pop(device_id, None)
        self._mouse_scroll_remainders.pop(device_id, None)

    def _update_input_diagnostics(
        self,
        *,
        device_profile: DeviceProfile,
        app_profile: AppProfile,
        preset: Preset,
        normalized_state: NormalizedControllerState,
        active_controls: Set[str],
        rising_controls: Set[str],
    ) -> None:
        diagnostics = self._right_stick_diagnostics.setdefault(device_profile.device_id, {})
        diagnostics["right_stick_mode"] = normalize_right_stick_mode(preset.right_stick_mode)
        diagnostics["profile"] = {
            "app_profile_id": app_profile.app_profile_id,
            "app_profile_name": app_profile.name,
            "process_name": app_profile.process_name,
            "preset_id": preset.preset_id,
            "preset_name": preset.name,
        }
        active_entries = []
        upward_candidates = []
        for control in sorted(active_controls):
            control_state = normalized_state.controls.get(control)
            if control_state is None:
                continue
            assignment = preset.assignment_for(control)
            entry = {
                "control": control,
                "value": round(control_state.value, 4),
                "source": control_state.source,
                "action_kind": assignment.action_kind,
                "shortcut": normalize_shortcut_text(assignment.shortcut),
                "label": assignment.label,
                "rising": control in rising_controls,
            }
            active_entries.append(entry)
            if self._assignment_source_kind(assignment) in {"mouse_wheel_up", "mouse_scroll", "keyboard_up"}:
                upward_candidates.append(entry)
        diagnostics["active_controls"] = active_entries
        diagnostics["upward_candidates"] = upward_candidates
        diagnostics["focused_control"] = self._focused_controls.get(device_profile.device_id, "")

    def _assignment_source_kind(self, assignment: MappingAssignment) -> str:
        if assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_UP:
            return "mouse_wheel_up"
        if assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_DOWN:
            return "mouse_wheel_down"
        if assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_LEFT:
            return "mouse_wheel_left"
        if assignment.action_kind == MAPPING_ACTION_MOUSE_WHEEL_RIGHT:
            return "mouse_wheel_right"
        if assignment.action_kind == MAPPING_ACTION_MOUSE_SCROLL:
            return "mouse_scroll"
        if assignment.action_kind == MAPPING_ACTION_KEYBOARD:
            normalized_shortcut = normalize_shortcut_text(assignment.shortcut)
            if normalized_shortcut == "Arrow Up":
                return "keyboard_up"
            if normalized_shortcut == "Arrow Down":
                return "keyboard_down"
            return "keyboard"
        return assignment.action_kind

    def _record_analog_scroll_emission(self, device_id: str, emit_x: int, emit_y: int) -> None:
        diagnostics = self._right_stick_diagnostics.setdefault(device_id, {})
        entry = {
            "control": "RIGHT_STICK_ANALOG",
            "action_kind": MAPPING_ACTION_MOUSE_SCROLL,
            "source_kind": "mouse_scroll",
            "emit_vector": (emit_x, emit_y),
        }
        diagnostics["last_emitted_action"] = entry
        if emit_y > 0:
            diagnostics["last_upward_emission"] = entry

    def _record_action_emission(
        self,
        device_id: str,
        control: str,
        assignment: MappingAssignment,
        canonical_source: str = "",
    ) -> None:
        diagnostics = self._right_stick_diagnostics.setdefault(device_id, {})
        normalized_state = self._normalized_states.get(device_id)
        physical_source = ""
        if normalized_state is not None and control in normalized_state.controls:
            physical_source = normalized_state.controls[control].source
        entry = {
            "control": control,
            "action_kind": assignment.action_kind,
            "shortcut": normalize_shortcut_text(assignment.shortcut),
            "label": assignment.label,
            "source_kind": self._assignment_source_kind(assignment),
            "physical_source": physical_source,
            "canonical_source": canonical_source or "assignment:{control}".format(control=control),
        }
        diagnostics["last_emitted_action"] = entry
        if entry["source_kind"] in {"mouse_wheel_up", "keyboard_up", "mouse_scroll"}:
            diagnostics["last_upward_emission"] = entry

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
        canonical_source: str = "",
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
        self._record_action_emission(
            device_profile.device_id,
            control,
            assignment,
            canonical_source=canonical_source,
        )
        self._log(
            "{device}: {action}".format(
                device=device_profile.display_name,
                action=self._assignment_action_text(assignment, control),
            )
        )

    def _should_dispatch_assignment(self, device_id: str, control: str, assignment: MappingAssignment) -> bool:
        if not self._is_single_fire_assignment(assignment):
            return True

        now = monotonic()
        device_fires = self._single_fire_last_fired.setdefault(device_id, {})
        last_fired_at = device_fires.get(control)
        if last_fired_at is not None and now - last_fired_at < SINGLE_FIRE_COOLDOWN_SECONDS:
            return False

        device_fires[control] = now
        return True

    def _prune_single_fire_state(self, device_id: str, active_controls: Set[str]) -> None:
        device_fires = self._single_fire_last_fired.get(device_id)
        if not device_fires:
            return
        for control in list(device_fires):
            if control not in active_controls:
                device_fires.pop(control, None)
        if not device_fires:
            self._single_fire_last_fired.pop(device_id, None)

    def _is_single_fire_assignment(self, assignment: MappingAssignment) -> bool:
        if assignment.action_kind in {
            MAPPING_ACTION_MOUSE_LEFT_CLICK,
            MAPPING_ACTION_MOUSE_RIGHT_CLICK,
            MAPPING_ACTION_MOUSE_MIDDLE_CLICK,
            MAPPING_ACTION_MOUSE_DOUBLE_CLICK,
        }:
            return True

        if assignment.action_kind != MAPPING_ACTION_KEYBOARD:
            return False

        normalized_shortcut = normalize_shortcut_text(assignment.shortcut)
        return normalized_shortcut in {
            "Alt+Arrow Left",
            "Alt+Arrow Right",
            "Space",
            "M",
            "F",
            "Tab",
            "Enter",
            "Media Play/Pause",
            "Volume Mute",
            "Shift+N",
        }

    def _assignment_action_text(self, assignment: MappingAssignment, control: str) -> str:
        if assignment.action_kind == MAPPING_ACTION_STICK_MODE:
            return self._right_stick_mode_action_text(assignment.shortcut)
        if assignment.action_kind == MAPPING_ACTION_KEYBOARD and not assignment.shortcut and not assignment.label:
            return self.tr("mapping.unassigned")
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

    def _assignment_matches_semantics(
        self,
        assignment: MappingAssignment,
        expected: Optional[MappingAssignment],
    ) -> bool:
        if expected is None:
            return False
        return (
            normalize_shortcut_text(assignment.shortcut) == normalize_shortcut_text(expected.shortcut)
            and normalize_mapping_action_kind(assignment.action_kind)
            == normalize_mapping_action_kind(expected.action_kind)
        )

    def _fallback_label_for_assignment(self, assignment: MappingAssignment, control: str) -> str:
        if assignment.action_kind == MAPPING_ACTION_STICK_MODE:
            return ""
        if assignment.action_kind == MAPPING_ACTION_KEYBOARD:
            if not assignment.shortcut:
                return self.tr("mapping.unassigned")
            return assignment.label or format_shortcut_text(assignment.shortcut) or self.tr("mapping.unassigned")
        return assignment.label or self._assignment_action_text(assignment, control)

    def _effective_assignment_label(
        self,
        assignment: MappingAssignment,
        control: str,
        selected_app_profile: Optional[AppProfile],
        family_id: str,
    ) -> str:
        if assignment.action_kind == MAPPING_ACTION_STICK_MODE:
            return ""
        if selected_app_profile is not None:
            default_assignment = default_assignment_for_process(
                selected_app_profile.process_name,
                family_id,
                selected_app_profile.active_preset_index,
                control,
            )
            if (
                default_assignment.action_kind != MAPPING_ACTION_STICK_MODE
                and self._assignment_matches_semantics(assignment, default_assignment)
            ):
                return default_assignment.label or self._fallback_label_for_assignment(default_assignment, control)
        return self._fallback_label_for_assignment(assignment, control)

    def _right_stick_mode_action_text(self, mode: str) -> str:
        normalized_mode = normalize_right_stick_mode(mode)
        return self.tr(
            {
                RIGHT_STICK_MODE_DISABLED: "mapping.stick_mode_disabled",
                RIGHT_STICK_MODE_MOUSE_MOVE: "mapping.stick_mode_mouse_move",
                RIGHT_STICK_MODE_WHEEL_STEP_VERTICAL: "mapping.stick_mode_wheel_step_vertical",
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY: "mapping.stick_mode_wheel_step_4way",
                RIGHT_STICK_MODE_CONTINUOUS_SCROLL: "mapping.stick_mode_continuous_scroll",
                RIGHT_STICK_MODE_CUSTOM_ADVANCED: "mapping.stick_mode_custom_advanced",
            }.get(normalized_mode, "mapping.stick_mode_custom_advanced")
        )

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

    def _resolve_app_family_id(self, device: Optional[DeviceProfile], app_profile: Optional[AppProfile]) -> str:
        candidates = []
        if app_profile is not None:
            candidates.append(app_profile.family_id)
        if device is not None:
            candidates.append(device.saved_family_id)
            candidates.append(device.family_override_id)
        for candidate in candidates:
            normalized = str(candidate or "").strip().lower()
            if normalized:
                return normalized
        return ""

    def _apply_right_stick_mode_to_preset(self, preset: Preset, mode: str) -> None:
        preset.right_stick_mode = normalize_right_stick_mode(mode)
        if preset.right_stick_mode != RIGHT_STICK_MODE_CUSTOM_ADVANCED:
            for control in RIGHT_STICK_DIRECTION_CONTROLS:
                preset.mappings.pop(control, None)

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

    def _log_load_report(self) -> None:
        report = getattr(self._store, "last_load_report", {})
        if not report:
            return
        self._log(
            "Config load -> source={source} migrated={migrated} legacy_xbox={legacy_xbox} rebuilt_defaults={rebuilt}".format(
                source=report.get("source", "unknown"),
                migrated=bool(report.get("migrated", False)),
                legacy_xbox=bool(report.get("legacy_xbox_recognized", False)),
                rebuilt=bool(report.get("rebuilt_from_canonical_defaults", False)),
            )
        )

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
            selected_app_profile=selected_app_profile,
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
        selected_app_profile: Optional[AppProfile],
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
        right_stick_mode_inserted = False
        family_id = self._resolve_app_family_id(selected_device, selected_app_profile)
        right_stick_mode = normalize_right_stick_mode(
            selected_preset.right_stick_mode if selected_preset is not None else RIGHT_STICK_MODE_CUSTOM_ADVANCED
        )

        for control in visible_controls:
            if control in RIGHT_STICK_DIRECTION_CONTROLS and right_stick_mode != RIGHT_STICK_MODE_CUSTOM_ADVANCED:
                if not right_stick_mode_inserted:
                    right_stick_is_active = False
                    if normalized_state is not None:
                        right_stick_is_active = any(
                            normalized_state.controls.get(stick_control) is not None
                            and normalized_state.controls[stick_control].is_active
                            for stick_control in RIGHT_STICK_DIRECTION_CONTROLS
                        )
                    rows.append(
                        MappingRow(
                            control=RIGHT_STICK_MODE,
                            button_name=CONTROL_DISPLAY_NAMES.get(RIGHT_STICK_MODE, RIGHT_STICK_MODE),
                            shortcut=right_stick_mode,
                            action_kind=MAPPING_ACTION_STICK_MODE,
                            action_text=self._right_stick_mode_action_text(right_stick_mode),
                            label="",
                            is_active=right_stick_is_active,
                            is_system_action=False,
                            system_text="",
                        )
                    )
                    rows.extend(
                        self._build_right_stick_effective_rows(
                            selected_app_profile=selected_app_profile,
                            normalized_state=normalized_state,
                            right_stick_mode=right_stick_mode,
                            control_labels=control_labels,
                        )
                    )
                    right_stick_mode_inserted = True
                continue
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
                    label=self._effective_assignment_label(assignment, control, selected_app_profile, family_id),
                    is_active=is_active,
                    is_system_action=is_system_action,
                    system_text=system_text,
                )
            )
        return rows

    def _build_right_stick_effective_rows(
        self,
        selected_app_profile: Optional[AppProfile],
        normalized_state: Optional[NormalizedControllerState],
        right_stick_mode: str,
        control_labels: Dict[str, str],
    ) -> List[MappingRow]:
        effective_assignments = self._right_stick_effective_assignments(right_stick_mode)
        rows: List[MappingRow] = []
        for source_control in (
            RIGHT_STICK_UP,
            RIGHT_STICK_DOWN,
            RIGHT_STICK_LEFT,
            RIGHT_STICK_RIGHT,
        ):
            assignment = effective_assignments[source_control]
            is_active = False
            if normalized_state is not None and source_control in normalized_state.controls:
                is_active = normalized_state.controls[source_control].is_active
            rows.append(
                MappingRow(
                    control=RIGHT_STICK_EFFECTIVE_ROWS[source_control],
                    button_name="  {label}".format(
                        label=control_labels.get(source_control, CONTROL_DISPLAY_NAMES.get(source_control, source_control))
                    ),
                    shortcut=format_shortcut_text(assignment.shortcut),
                    action_kind=assignment.action_kind,
                    action_text=self._assignment_action_text(assignment, source_control),
                    label=self._effective_assignment_label(assignment, source_control, selected_app_profile, ""),
                    is_active=is_active,
                    is_system_action=False,
                    system_text="",
                    is_read_only=True,
                )
            )
        return rows

    def _right_stick_effective_assignments(self, right_stick_mode: str) -> Dict[str, MappingAssignment]:
        normalized_mode = normalize_right_stick_mode(right_stick_mode)
        if normalized_mode == RIGHT_STICK_MODE_WHEEL_STEP_VERTICAL:
            return {
                RIGHT_STICK_UP: MappingAssignment(
                    control=RIGHT_STICK_UP,
                    label=self.tr("mapping.mouse_wheel_up"),
                    action_kind=MAPPING_ACTION_MOUSE_WHEEL_UP,
                ),
                RIGHT_STICK_DOWN: MappingAssignment(
                    control=RIGHT_STICK_DOWN,
                    label=self.tr("mapping.mouse_wheel_down"),
                    action_kind=MAPPING_ACTION_MOUSE_WHEEL_DOWN,
                ),
                RIGHT_STICK_LEFT: MappingAssignment(control=RIGHT_STICK_LEFT),
                RIGHT_STICK_RIGHT: MappingAssignment(control=RIGHT_STICK_RIGHT),
            }
        if normalized_mode == RIGHT_STICK_MODE_WHEEL_STEP_4WAY:
            return {
                RIGHT_STICK_UP: MappingAssignment(
                    control=RIGHT_STICK_UP,
                    label=self.tr("mapping.mouse_wheel_up"),
                    action_kind=MAPPING_ACTION_MOUSE_WHEEL_UP,
                ),
                RIGHT_STICK_DOWN: MappingAssignment(
                    control=RIGHT_STICK_DOWN,
                    label=self.tr("mapping.mouse_wheel_down"),
                    action_kind=MAPPING_ACTION_MOUSE_WHEEL_DOWN,
                ),
                RIGHT_STICK_LEFT: MappingAssignment(
                    control=RIGHT_STICK_LEFT,
                    label=self.tr("mapping.mouse_wheel_left"),
                    action_kind=MAPPING_ACTION_MOUSE_WHEEL_LEFT,
                ),
                RIGHT_STICK_RIGHT: MappingAssignment(
                    control=RIGHT_STICK_RIGHT,
                    label=self.tr("mapping.mouse_wheel_right"),
                    action_kind=MAPPING_ACTION_MOUSE_WHEEL_RIGHT,
                ),
            }
        if normalized_mode == RIGHT_STICK_MODE_MOUSE_MOVE:
            return {
                RIGHT_STICK_UP: MappingAssignment(control=RIGHT_STICK_UP, label="Mouse Up", action_kind=MAPPING_ACTION_MOUSE_MOVE),
                RIGHT_STICK_DOWN: MappingAssignment(control=RIGHT_STICK_DOWN, label="Mouse Down", action_kind=MAPPING_ACTION_MOUSE_MOVE),
                RIGHT_STICK_LEFT: MappingAssignment(control=RIGHT_STICK_LEFT, label="Mouse Left", action_kind=MAPPING_ACTION_MOUSE_MOVE),
                RIGHT_STICK_RIGHT: MappingAssignment(control=RIGHT_STICK_RIGHT, label="Mouse Right", action_kind=MAPPING_ACTION_MOUSE_MOVE),
            }
        if normalized_mode == RIGHT_STICK_MODE_CONTINUOUS_SCROLL:
            return {
                RIGHT_STICK_UP: MappingAssignment(control=RIGHT_STICK_UP, label="Scroll Up", action_kind=MAPPING_ACTION_MOUSE_SCROLL),
                RIGHT_STICK_DOWN: MappingAssignment(control=RIGHT_STICK_DOWN, label="Scroll Down", action_kind=MAPPING_ACTION_MOUSE_SCROLL),
                RIGHT_STICK_LEFT: MappingAssignment(control=RIGHT_STICK_LEFT, label="Scroll Left", action_kind=MAPPING_ACTION_MOUSE_SCROLL),
                RIGHT_STICK_RIGHT: MappingAssignment(control=RIGHT_STICK_RIGHT, label="Scroll Right", action_kind=MAPPING_ACTION_MOUSE_SCROLL),
            }
        return {
            RIGHT_STICK_UP: MappingAssignment(control=RIGHT_STICK_UP),
            RIGHT_STICK_DOWN: MappingAssignment(control=RIGHT_STICK_DOWN),
            RIGHT_STICK_LEFT: MappingAssignment(control=RIGHT_STICK_LEFT),
            RIGHT_STICK_RIGHT: MappingAssignment(control=RIGHT_STICK_RIGHT),
        }

    def _sorted_devices(self) -> List[DeviceProfile]:
        connected_ids = set(self._raw_states)
        return sorted(
            self._config.devices,
            key=lambda device: (device.device_id not in connected_ids, device.display_name.lower()),
        )
