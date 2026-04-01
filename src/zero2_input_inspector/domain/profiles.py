from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..services.shortcuts import normalize_shortcut_text
from ..styles import DEFAULT_THEME_ID
from .controls import (
    DPAD_DOWN,
    DPAD_LEFT,
    DPAD_RIGHT,
    DPAD_UP,
    FACE_EAST,
    FACE_NORTH,
    FACE_SOUTH,
    FACE_WEST,
    LEFT_STICK_DOWN,
    LEFT_STICK_LEFT,
    LEFT_STICK_PRESS,
    LEFT_STICK_RIGHT,
    LEFT_STICK_UP,
    LEFT_TRIGGER,
    L,
    PRESET_NEXT_CONTROL,
    PRESET_PREVIOUS_CONTROL,
    RIGHT_STICK_DOWN,
    RIGHT_STICK_LEFT,
    RIGHT_STICK_PRESS,
    RIGHT_STICK_RIGHT,
    RIGHT_STICK_UP,
    RIGHT_TRIGGER,
    R,
    SELECT,
    START,
)
from ..identity import DEFAULT_FALLBACK_PROFILE_NAME

MAX_PRESET_COUNT = 5
MIN_PRESET_COUNT = 1
DEFAULT_PRESET_COUNT = 3
DEFAULT_XBOX_FAMILY_ID = "xbox"
LEGACY_FALLBACK_PROFILE_NAMES = {
    DEFAULT_FALLBACK_PROFILE_NAME.casefold(),
    "global",
    "global (*)",
}

MAPPING_ACTION_KEYBOARD = "keyboard"
MAPPING_ACTION_MOUSE_MOVE = "mouse_move"
MAPPING_ACTION_MOUSE_SCROLL = "mouse_scroll"
MAPPING_ACTION_MOUSE_LEFT_CLICK = "mouse_left_click"
MAPPING_ACTION_MOUSE_RIGHT_CLICK = "mouse_right_click"
MAPPING_ACTION_MOUSE_MIDDLE_CLICK = "mouse_middle_click"
MAPPING_ACTION_MOUSE_DOUBLE_CLICK = "mouse_double_click"
MAPPING_ACTION_MOUSE_WHEEL_UP = "mouse_wheel_up"
MAPPING_ACTION_MOUSE_WHEEL_DOWN = "mouse_wheel_down"
MAPPING_ACTION_MOUSE_WHEEL_LEFT = "mouse_wheel_left"
MAPPING_ACTION_MOUSE_WHEEL_RIGHT = "mouse_wheel_right"

MAPPING_ACTION_KINDS = {
    MAPPING_ACTION_KEYBOARD,
    MAPPING_ACTION_MOUSE_MOVE,
    MAPPING_ACTION_MOUSE_SCROLL,
    MAPPING_ACTION_MOUSE_LEFT_CLICK,
    MAPPING_ACTION_MOUSE_RIGHT_CLICK,
    MAPPING_ACTION_MOUSE_MIDDLE_CLICK,
    MAPPING_ACTION_MOUSE_DOUBLE_CLICK,
    MAPPING_ACTION_MOUSE_WHEEL_UP,
    MAPPING_ACTION_MOUSE_WHEEL_DOWN,
    MAPPING_ACTION_MOUSE_WHEEL_LEFT,
    MAPPING_ACTION_MOUSE_WHEEL_RIGHT,
}


def _new_id(prefix: str) -> str:
    return "{prefix}-{suffix}".format(prefix=prefix, suffix=uuid.uuid4().hex[:8])


@dataclass
class MappingAssignment:
    control: str
    shortcut: str = ""
    label: str = ""
    action_kind: str = MAPPING_ACTION_KEYBOARD


@dataclass(frozen=True)
class MappingMigrationRule:
    old_shortcut: str
    old_label: str
    new_shortcut: str
    new_label: str
    new_action_kind: str = MAPPING_ACTION_KEYBOARD


MEDIA_FALLBACK_MAPPING_MIGRATION_RULES: Tuple[MappingMigrationRule, ...] = (
    MappingMigrationRule(
        old_shortcut="Shift+P",
        old_label="Previous Video",
        new_shortcut="Alt+Left",
        new_label="Browser Back",
    ),
    MappingMigrationRule(
        old_shortcut="Shift+N",
        old_label="Next Video",
        new_shortcut="Alt+Right",
        new_label="Browser Forward",
    ),
)


@dataclass
class Preset:
    preset_id: str
    name: str
    mappings: Dict[str, MappingAssignment] = field(default_factory=dict)

    def assignment_for(self, control: str) -> MappingAssignment:
        return self.mappings.get(control, MappingAssignment(control=control))


@dataclass
class AppProfile:
    app_profile_id: str
    name: str
    process_name: str
    family_id: str = ""
    presets: List[Preset] = field(default_factory=list)
    active_preset_index: int = 0
    mouse_sensitivity: float = 1.0
    scroll_sensitivity: float = 1.0
    analog_deadzone: float = 0.16
    analog_curve: float = 1.7
    slow_speed_multiplier: float = 0.45
    fast_speed_multiplier: float = 1.75
    slow_modifier_control: str = ""
    fast_modifier_control: str = ""

    def active_preset(self) -> Preset:
        if not self.presets:
            self.presets.extend(build_default_presets_for_process(self.process_name, self.family_id))
        self.active_preset_index = max(0, min(self.active_preset_index, len(self.presets) - 1))
        return self.presets[self.active_preset_index]


@dataclass
class PresetSwitchBinding:
    previous_control: str = PRESET_PREVIOUS_CONTROL
    next_control: str = PRESET_NEXT_CONTROL


@dataclass
class DeviceProfile:
    device_id: str
    display_name: str
    guid: str = ""
    last_seen_name: str = ""
    saved_family_id: str = ""
    family_override_id: str = ""
    shape_signature: str = ""
    app_profiles: List[AppProfile] = field(default_factory=list)
    selected_app_profile_id: str = ""
    preset_switch: PresetSwitchBinding = field(default_factory=PresetSwitchBinding)

    def selected_app_profile(self) -> AppProfile:
        if not self.app_profiles:
            family_id = self.saved_family_id or self.family_override_id
            self.app_profiles.extend(build_default_app_profiles(family_id))
        if not self.selected_app_profile_id:
            self.selected_app_profile_id = default_selected_app_profile_id(
                self.app_profiles,
                self.saved_family_id or self.family_override_id,
            )
        for app_profile in self.app_profiles:
            if app_profile.app_profile_id == self.selected_app_profile_id:
                return app_profile
        self.selected_app_profile_id = default_selected_app_profile_id(
            self.app_profiles,
            self.saved_family_id or self.family_override_id,
        )
        for app_profile in self.app_profiles:
            if app_profile.app_profile_id == self.selected_app_profile_id:
                return app_profile
        self.selected_app_profile_id = self.app_profiles[0].app_profile_id
        return self.app_profiles[0]


@dataclass
class Settings:
    language: str = "en"
    theme: str = DEFAULT_THEME_ID
    auto_start: bool = False


@dataclass
class AppConfig:
    version: int = 1
    settings: Settings = field(default_factory=Settings)
    devices: List[DeviceProfile] = field(default_factory=list)
    selected_device_id: str = ""

    def device_by_id(self, device_id: str) -> Optional[DeviceProfile]:
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None


def build_default_presets() -> List[Preset]:
    preset_specs = [
        (
            "Edit",
            {
                FACE_WEST: ("Ctrl+Z", "Undo"),
                FACE_NORTH: ("Ctrl+Shift+Z", "Redo"),
                FACE_SOUTH: ("Space", "Pan"),
                FACE_EAST: ("Alt", "Sample"),
                L: ("[", "Brush -"),
                R: ("]", "Brush +"),
                DPAD_UP: ("B", "Brush"),
                DPAD_DOWN: ("E", "Eraser"),
                DPAD_LEFT: ("Ctrl+0", "Fit"),
                DPAD_RIGHT: ("Ctrl+1", "100%"),
            },
        ),
        (
            "View",
            {
                FACE_WEST: ("H", "Hand"),
                FACE_NORTH: ("Tab", "Hide Panels"),
                FACE_SOUTH: ("Space", "Pan"),
                FACE_EAST: ("Z", "Zoom"),
                L: ("Ctrl+-", "Zoom Out"),
                R: ("Ctrl+0", "Reset View"),
                DPAD_UP: ("F", "Full Screen"),
                DPAD_DOWN: ("Ctrl+R", "Rulers"),
                DPAD_LEFT: ("Ctrl+Alt+0", "Fit Artboard"),
                DPAD_RIGHT: ("Ctrl+Space", "Scrubby Zoom"),
            },
        ),
        (
            "Tools",
            {
                FACE_WEST: ("V", "Move"),
                FACE_NORTH: ("M", "Marquee"),
                FACE_SOUTH: ("B", "Brush"),
                FACE_EAST: ("E", "Eraser"),
                L: ("X", "Swap Colors"),
                R: ("D", "Default Colors"),
                DPAD_UP: ("G", "Gradient"),
                DPAD_DOWN: ("L", "Lasso"),
                DPAD_LEFT: ("I", "Eyedropper"),
                DPAD_RIGHT: ("J", "Healing"),
            },
        ),
    ]

    return _build_presets_from_specs(preset_specs)


def build_default_media_presets() -> List[Preset]:
    return build_default_media_presets_for_family("")


def build_default_media_presets_for_family(family_id: str = "") -> List[Preset]:
    normalized_family_id = (family_id or "").strip().lower()
    if normalized_family_id == DEFAULT_XBOX_FAMILY_ID:
        preset_specs = [
            (
                DEFAULT_FALLBACK_PROFILE_NAME,
                {
                    FACE_SOUTH: ("", "Left Click", MAPPING_ACTION_MOUSE_LEFT_CLICK),
                    FACE_NORTH: ("", "Double Click", MAPPING_ACTION_MOUSE_DOUBLE_CLICK),
                    FACE_WEST: ("", "Right Click", MAPPING_ACTION_MOUSE_RIGHT_CLICK),
                    FACE_EAST: ("Alt+Left", "Browser Back", MAPPING_ACTION_KEYBOARD),
                    DPAD_LEFT: ("Left", "Back 5s", MAPPING_ACTION_KEYBOARD),
                    DPAD_RIGHT: ("Right", "Forward 5s", MAPPING_ACTION_KEYBOARD),
                    DPAD_UP: ("Up", "Volume Up", MAPPING_ACTION_KEYBOARD),
                    DPAD_DOWN: ("Down", "Volume Down", MAPPING_ACTION_KEYBOARD),
                    L: ("J", "Back 10s", MAPPING_ACTION_KEYBOARD),
                    R: ("L", "Forward 10s", MAPPING_ACTION_KEYBOARD),
                    SELECT: ("M", "Mute", MAPPING_ACTION_KEYBOARD),
                    START: ("F", "Fullscreen", MAPPING_ACTION_KEYBOARD),
                    LEFT_TRIGGER: ("Space", "Play/Pause", MAPPING_ACTION_KEYBOARD),
                    RIGHT_TRIGGER: ("K", "Play/Pause Alt", MAPPING_ACTION_KEYBOARD),
                    LEFT_STICK_PRESS: ("Tab", "Focus Next", MAPPING_ACTION_KEYBOARD),
                    RIGHT_STICK_PRESS: ("Enter", "Activate", MAPPING_ACTION_KEYBOARD),
                    LEFT_STICK_LEFT: ("", "Mouse Left", MAPPING_ACTION_MOUSE_MOVE),
                    LEFT_STICK_RIGHT: ("", "Mouse Right", MAPPING_ACTION_MOUSE_MOVE),
                    LEFT_STICK_UP: ("", "Mouse Up", MAPPING_ACTION_MOUSE_MOVE),
                    LEFT_STICK_DOWN: ("", "Mouse Down", MAPPING_ACTION_MOUSE_MOVE),
                    RIGHT_STICK_LEFT: ("", "Scroll Left", MAPPING_ACTION_MOUSE_SCROLL),
                    RIGHT_STICK_RIGHT: ("", "Scroll Right", MAPPING_ACTION_MOUSE_SCROLL),
                    RIGHT_STICK_UP: ("", "Scroll Up", MAPPING_ACTION_MOUSE_SCROLL),
                    RIGHT_STICK_DOWN: ("", "Scroll Down", MAPPING_ACTION_MOUSE_SCROLL),
                },
            ),
        ]
        return _build_presets_from_specs(preset_specs)

    preset_specs = [
        (
            DEFAULT_FALLBACK_PROFILE_NAME,
            {
                FACE_SOUTH: ("Space", "Play/Pause", MAPPING_ACTION_KEYBOARD),
                FACE_NORTH: ("K", "Play/Pause Alt", MAPPING_ACTION_KEYBOARD),
                FACE_WEST: ("J", "Back 10s", MAPPING_ACTION_KEYBOARD),
                FACE_EAST: ("L", "Forward 10s", MAPPING_ACTION_KEYBOARD),
                DPAD_LEFT: ("Arrow Left", "Seek Back", MAPPING_ACTION_KEYBOARD),
                DPAD_RIGHT: ("Arrow Right", "Seek Forward", MAPPING_ACTION_KEYBOARD),
                DPAD_UP: ("Arrow Up", "Volume Up", MAPPING_ACTION_KEYBOARD),
                DPAD_DOWN: ("Arrow Down", "Volume Down", MAPPING_ACTION_KEYBOARD),
                L: ("Alt+Left", "Browser Back", MAPPING_ACTION_KEYBOARD),
                R: ("Alt+Right", "Browser Forward", MAPPING_ACTION_KEYBOARD),
                SELECT: ("Tab", "Focus Next", MAPPING_ACTION_KEYBOARD),
                START: ("Enter", "Activate", MAPPING_ACTION_KEYBOARD),
            },
        ),
    ]
    return _build_presets_from_specs(preset_specs)

def build_default_app_profiles(family_id: str = "") -> List[AppProfile]:
    normalized_family_id = (family_id or "").strip().lower()
    profile_specs = [
        ("Photoshop", "photoshop.exe"),
        ("Illustrator", "illustrator.exe"),
        (DEFAULT_FALLBACK_PROFILE_NAME, "*"),
    ]
    app_profiles: List[AppProfile] = []
    for profile_name, process_name in profile_specs:
        app_profiles.append(
            AppProfile(
                app_profile_id=_new_id("app"),
                name=profile_name,
                process_name=process_name,
                family_id=normalized_family_id,
                presets=build_default_presets_for_process(process_name, family_id),
            )
        )
    return app_profiles


def build_default_device_profile(
    device_id: str,
    display_name: str,
    guid: str = "",
    family_id: str = "",
) -> DeviceProfile:
    normalized_family_id = (family_id or "").strip().lower()
    app_profiles = build_default_app_profiles(normalized_family_id)
    return DeviceProfile(
        device_id=device_id,
        display_name=display_name,
        guid=guid,
        last_seen_name=display_name,
        saved_family_id=normalized_family_id,
        app_profiles=app_profiles,
        selected_app_profile_id=default_selected_app_profile_id(app_profiles, normalized_family_id),
    )


def build_blank_app_profile(
    name: str = "New App",
    process_name: str = "new-app.exe",
    family_id: str = "",
) -> AppProfile:
    return AppProfile(
        app_profile_id=_new_id("app"),
        name=name,
        process_name=process_name,
        family_id=(family_id or "").strip().lower(),
        presets=build_default_presets_for_process(process_name, family_id),
    )


def build_blank_preset(name: str) -> Preset:
    return Preset(preset_id=_new_id("preset"), name=name)


def _build_presets_from_specs(preset_specs) -> List[Preset]:
    presets: List[Preset] = []
    for preset_name, mappings in preset_specs:
        preset = Preset(preset_id=_new_id("preset"), name=preset_name)
        for control, mapping_spec in mappings.items():
            if isinstance(mapping_spec, MappingAssignment):
                assignment = mapping_spec
            else:
                if len(mapping_spec) == 2:
                    shortcut, label = mapping_spec
                    action_kind = MAPPING_ACTION_KEYBOARD
                elif len(mapping_spec) == 3:
                    shortcut, label, action_kind = mapping_spec
                else:
                    raise ValueError("Unsupported mapping spec for control {control}".format(control=control))
                assignment = MappingAssignment(
                    control=control,
                    shortcut=str(shortcut),
                    label=str(label),
                    action_kind=normalize_mapping_action_kind(str(action_kind)),
                )
            if assignment.action_kind not in MAPPING_ACTION_KINDS:
                assignment = MappingAssignment(
                    control=assignment.control,
                    shortcut=assignment.shortcut,
                    label=assignment.label,
                    action_kind=MAPPING_ACTION_KEYBOARD,
                )
            preset.mappings[control] = MappingAssignment(
                control=assignment.control,
                shortcut=assignment.shortcut,
                label=assignment.label,
                action_kind=assignment.action_kind,
            )
        presets.append(preset)
    return presets


def build_default_presets_for_process(process_name: str, family_id: str = "") -> List[Preset]:
    if is_media_fallback_process_name(process_name):
        return build_default_media_presets_for_family(family_id)
    return build_default_presets()


def default_assignment_for_process(
    process_name: str,
    family_id: str,
    preset_index: int,
    control: str,
) -> MappingAssignment:
    presets = build_default_presets_for_process(process_name, family_id)
    canonical_control = str(control)
    if 0 <= preset_index < len(presets):
        default_assignment = presets[preset_index].assignment_for(canonical_control)
        return MappingAssignment(
            control=canonical_control,
            shortcut=default_assignment.shortcut,
            label=default_assignment.label,
            action_kind=default_assignment.action_kind,
        )
    return MappingAssignment(control=canonical_control)


def migrate_preset_mappings(preset: Preset, rules: Tuple[MappingMigrationRule, ...]) -> bool:
    migrated = False
    for control, mapping in list(preset.mappings.items()):
        for rule in rules:
            if _mapping_matches_rule(mapping, rule):
                preset.mappings[control] = MappingAssignment(
                    control=control,
                    shortcut=rule.new_shortcut,
                    label=rule.new_label,
                    action_kind=normalize_mapping_action_kind(rule.new_action_kind),
                )
                migrated = True
                break
    return migrated


def migrate_media_fallback_profile(app_profile: AppProfile) -> bool:
    if not is_media_fallback_profile(app_profile):
        return False
    migrated = False
    for preset in app_profile.presets:
        migrated = migrate_preset_mappings(preset, MEDIA_FALLBACK_MAPPING_MIGRATION_RULES) or migrated
    default_presets = build_default_media_presets_for_family(app_profile.family_id)
    for preset_index, preset in enumerate(app_profile.presets):
        if preset_index >= len(default_presets):
            break
        default_preset = default_presets[preset_index]
        for control, default_assignment in default_preset.mappings.items():
            if control in preset.mappings:
                continue
            preset.mappings[control] = MappingAssignment(
                control=control,
                shortcut=default_assignment.shortcut,
                label=default_assignment.label,
                action_kind=default_assignment.action_kind,
            )
            migrated = True
    return migrated


def normalize_mapping_action_kind(action_kind: str) -> str:
    normalized = str(action_kind or "").strip().lower()
    if normalized in MAPPING_ACTION_KINDS:
        return normalized
    return MAPPING_ACTION_KEYBOARD


def default_selected_app_profile_id(app_profiles: List[AppProfile], family_id: str = "") -> str:
    for app_profile in app_profiles:
        if is_media_fallback_profile(app_profile):
            return app_profile.app_profile_id
    return app_profiles[0].app_profile_id if app_profiles else ""


def is_media_fallback_name(name: str) -> bool:
    return str(name or "").strip().casefold() in LEGACY_FALLBACK_PROFILE_NAMES


def is_media_fallback_process_name(process_name: str) -> bool:
    return str(process_name or "").strip().lower() == "*"


def is_media_fallback_profile(app_profile: AppProfile) -> bool:
    return is_media_fallback_process_name(app_profile.process_name) or is_media_fallback_name(app_profile.name)


def _mapping_matches_rule(mapping: MappingAssignment, rule: MappingMigrationRule) -> bool:
    return (
        normalize_shortcut_text(mapping.shortcut) == normalize_shortcut_text(rule.old_shortcut)
        and _normalize_label(mapping.label) == _normalize_label(rule.old_label)
        and normalize_mapping_action_kind(mapping.action_kind) == normalize_mapping_action_kind(
            rule.new_action_kind
        )
    )


def _normalize_label(text: str) -> str:
    return str(text or "").strip().casefold()
