from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from ..domain.controls import (
    CONTROL_DISPLAY_NAMES,
    DPAD_DOWN,
    DPAD_LEFT,
    DPAD_RIGHT,
    DPAD_UP,
    FACE_EAST,
    FACE_NORTH,
    FACE_SOUTH,
    FACE_WEST,
    GUIDE,
    L,
    LEFT_STICK_PRESS,
    LEFT_STICK_DOWN,
    LEFT_STICK_LEFT,
    LEFT_STICK_RIGHT,
    LEFT_STICK_UP,
    LEFT_TRIGGER,
    R,
    RIGHT_STICK_PRESS,
    RIGHT_STICK_DOWN,
    RIGHT_STICK_LEFT,
    RIGHT_STICK_RIGHT,
    RIGHT_STICK_UP,
    RIGHT_TRIGGER,
    SELECT,
    START,
)


@dataclass(frozen=True)
class DeviceShapePattern:
    axes_counts: Tuple[int, ...] = ()
    button_counts: Tuple[int, ...] = ()
    hat_counts: Tuple[int, ...] = ()
    is_standard_controller: Optional[bool] = None

    def matches(
        self,
        *,
        axes_count: int,
        buttons_count: int,
        hats_count: int,
        is_standard_controller: bool,
    ) -> bool:
        if self.axes_counts and axes_count not in self.axes_counts:
            return False
        if self.button_counts and buttons_count not in self.button_counts:
            return False
        if self.hat_counts and hats_count not in self.hat_counts:
            return False
        if (
            self.is_standard_controller is not None
            and self.is_standard_controller != is_standard_controller
        ):
            return False
        return True


@dataclass(frozen=True)
class RawFallbackLayout:
    button_map: Dict[int, str] = field(default_factory=dict)
    trigger_axes: Dict[int, str] = field(default_factory=dict)
    left_stick_axes: Optional[Tuple[int, int]] = None
    right_stick_axes: Optional[Tuple[int, int]] = None
    dpad_hat_index: Optional[int] = None
    dpad_axis_pair: Optional[Tuple[int, int]] = None
    standard_dpad_axes: Optional[Tuple[str, str]] = None


@dataclass(frozen=True)
class DeviceTemplate:
    family_id: str
    title: str
    diagram_kind: str
    has_exact_diagram: bool
    name_tokens: Tuple[str, ...]
    guid_fragments: Tuple[str, ...]
    shape_patterns: Tuple[DeviceShapePattern, ...]
    visible_controls: Tuple[str, ...]
    control_labels: Dict[str, str]
    standard_axis_map: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    standard_control_map: Dict[str, str] = field(default_factory=dict)
    raw_fallback: Optional[RawFallbackLayout] = None
    name_match_requires_standard_controller: bool = False
    allow_shape_only_match: bool = True


POSITION_STANDARD_CONTROL_MAP = {
    "a": FACE_SOUTH,
    "b": FACE_EAST,
    "x": FACE_WEST,
    "y": FACE_NORTH,
    "back": SELECT,
    "start": START,
    "guide": GUIDE,
    "leftshoulder": L,
    "rightshoulder": R,
    "lefttrigger": LEFT_TRIGGER,
    "righttrigger": RIGHT_TRIGGER,
    "leftstick": LEFT_STICK_PRESS,
    "rightstick": RIGHT_STICK_PRESS,
    "dpup": DPAD_UP,
    "dpdown": DPAD_DOWN,
    "dpleft": DPAD_LEFT,
    "dpright": DPAD_RIGHT,
}

ZERO2_STANDARD_CONTROL_MAP = {
    "a": FACE_EAST,
    "b": FACE_SOUTH,
    "x": FACE_NORTH,
    "y": FACE_WEST,
    "back": SELECT,
    "start": START,
    "leftshoulder": L,
    "rightshoulder": R,
    "dpup": DPAD_UP,
    "dpdown": DPAD_DOWN,
    "dpleft": DPAD_LEFT,
    "dpright": DPAD_RIGHT,
}

ZERO2_VISIBLE_CONTROLS = (
    L,
    R,
    SELECT,
    START,
    DPAD_UP,
    DPAD_LEFT,
    DPAD_DOWN,
    DPAD_RIGHT,
    FACE_NORTH,
    FACE_WEST,
    FACE_SOUTH,
    FACE_EAST,
)

STANDARD_VISIBLE_ORDER = (
    L,
    R,
    LEFT_TRIGGER,
    RIGHT_TRIGGER,
    SELECT,
    START,
    GUIDE,
    DPAD_UP,
    DPAD_LEFT,
    DPAD_DOWN,
    DPAD_RIGHT,
    FACE_NORTH,
    FACE_WEST,
    FACE_SOUTH,
    FACE_EAST,
    LEFT_STICK_PRESS,
    RIGHT_STICK_PRESS,
)

XBOX_VISIBLE_CONTROLS = (
    *STANDARD_VISIBLE_ORDER,
    LEFT_STICK_UP,
    LEFT_STICK_LEFT,
    LEFT_STICK_DOWN,
    LEFT_STICK_RIGHT,
    RIGHT_STICK_UP,
    RIGHT_STICK_LEFT,
    RIGHT_STICK_DOWN,
    RIGHT_STICK_RIGHT,
)

ZERO2_CONTROL_LABELS = {
    L: "L",
    R: "R",
    SELECT: "Select",
    START: "Start",
    DPAD_UP: "D-Pad Up",
    DPAD_DOWN: "D-Pad Down",
    DPAD_LEFT: "D-Pad Left",
    DPAD_RIGHT: "D-Pad Right",
    FACE_NORTH: "X",
    FACE_WEST: "Y",
    FACE_SOUTH: "B",
    FACE_EAST: "A",
}

XBOX_CONTROL_LABELS = {
    L: "LB",
    R: "RB",
    LEFT_TRIGGER: "LT",
    RIGHT_TRIGGER: "RT",
    SELECT: "View",
    START: "Menu",
    GUIDE: "Xbox",
    DPAD_UP: "D-Pad Up",
    DPAD_DOWN: "D-Pad Down",
    DPAD_LEFT: "D-Pad Left",
    DPAD_RIGHT: "D-Pad Right",
    FACE_NORTH: "Y",
    FACE_WEST: "X",
    FACE_SOUTH: "A",
    FACE_EAST: "B",
    LEFT_STICK_PRESS: "L3",
    RIGHT_STICK_PRESS: "R3",
    LEFT_STICK_UP: "LS Up",
    LEFT_STICK_DOWN: "LS Down",
    LEFT_STICK_LEFT: "LS Left",
    LEFT_STICK_RIGHT: "LS Right",
    RIGHT_STICK_UP: "RS Up",
    RIGHT_STICK_DOWN: "RS Down",
    RIGHT_STICK_LEFT: "RS Left",
    RIGHT_STICK_RIGHT: "RS Right",
}

GENERIC_STANDARD_LABELS = {
    control: CONTROL_DISPLAY_NAMES.get(control, control)
    for control in STANDARD_VISIBLE_ORDER
}

ZERO2_BUTTON_MAP = {
    0: FACE_EAST,
    1: FACE_SOUTH,
    3: FACE_NORTH,
    4: FACE_WEST,
    6: L,
    7: R,
    10: SELECT,
    11: START,
}

XBOX_BUTTON_MAP = {
    0: FACE_SOUTH,
    1: FACE_EAST,
    2: FACE_WEST,
    3: FACE_NORTH,
    4: L,
    5: R,
    6: SELECT,
    7: START,
    8: LEFT_STICK_PRESS,
    9: RIGHT_STICK_PRESS,
    10: GUIDE,
}

XBOX_STANDARD_AXIS_MAP = {
    "leftx": (LEFT_STICK_LEFT, LEFT_STICK_RIGHT),
    "lefty": (LEFT_STICK_UP, LEFT_STICK_DOWN),
    "rightx": (RIGHT_STICK_LEFT, RIGHT_STICK_RIGHT),
    "righty": (RIGHT_STICK_UP, RIGHT_STICK_DOWN),
}

XBOX_LAYOUT = {
    "body": {
        "core_rect": (170.0, 102.0, 660.0, 270.0),
        "core_radius": 120.0,
        "bridge_rect": (300.0, 246.0, 400.0, 182.0),
        "bridge_radius": 94.0,
        "left_grip_rect": (118.0, 196.0, 316.0, 326.0),
        "right_grip_rect": (566.0, 196.0, 316.0, 326.0),
        "accent_rect": (320.0, 124.0, 360.0, 10.0),
    },
    "triggers": {
        "left": (150.0, 54.0, 170.0, 28.0),
        "right": (680.0, 54.0, 170.0, 28.0),
    },
    "shoulders": {
        "left": (146.0, 80.0, 178.0, 28.0),
        "right": (676.0, 80.0, 178.0, 28.0),
    },
    "sticks": {
        "left_center": (324.0, 272.0),
        "right_center": (610.0, 326.0),
        "base_radius": 48.0,
        "press_radius": 18.0,
        "segment_width": 36.0,
        "segment_height": 30.0,
    },
    "dpad": {
        "center": (236.0, 326.0),
        "radius": 16.0,
        "arm_width": 60.0,
        "arm_length": 82.0,
    },
    "face": {
        "center": (764.0, 258.0),
        "radius": 28.0,
        "offset": 56.0,
    },
    "center_buttons": {
        "view": (452.0, 236.0, 44.0, 20.0),
        "menu": (504.0, 236.0, 44.0, 20.0),
        "xbox": (466.0, 188.0, 68.0, 68.0),
    },
    "brand": (402.0, 162.0, 196.0, 28.0),
}

GENERIC_BUTTON_MAP = {
    0: FACE_SOUTH,
    1: FACE_EAST,
    2: FACE_WEST,
    3: FACE_NORTH,
    4: L,
    5: R,
    6: SELECT,
    7: START,
}

ZERO2_TEMPLATE = DeviceTemplate(
    family_id="8bitdo_zero2",
    title="8BitDo Zero 2",
    diagram_kind="zero2",
    has_exact_diagram=True,
    name_tokens=("8bitdo zero 2", "zero 2", "zero2"),
    guid_fragments=("c82d000018900000", "c82d000030320000"),
    shape_patterns=(
        DeviceShapePattern(axes_counts=(2, 4), button_counts=(10, 12), hat_counts=(0, 1)),
    ),
    visible_controls=ZERO2_VISIBLE_CONTROLS,
    control_labels=ZERO2_CONTROL_LABELS,
    standard_control_map=ZERO2_STANDARD_CONTROL_MAP,
    raw_fallback=RawFallbackLayout(
        button_map=ZERO2_BUTTON_MAP,
        dpad_hat_index=0,
        dpad_axis_pair=(0, 1),
        standard_dpad_axes=("leftx", "lefty"),
    ),
)

XBOX_TEMPLATE = DeviceTemplate(
    family_id="xbox",
    title="Xbox Controller",
    diagram_kind="xbox",
    has_exact_diagram=True,
    name_tokens=("xbox", "xinput", "x-input"),
    guid_fragments=(),
    shape_patterns=(
        DeviceShapePattern(axes_counts=(6,), button_counts=(10, 11), hat_counts=(1,), is_standard_controller=True),
    ),
    visible_controls=XBOX_VISIBLE_CONTROLS,
    control_labels=XBOX_CONTROL_LABELS,
    standard_axis_map=XBOX_STANDARD_AXIS_MAP,
    standard_control_map=POSITION_STANDARD_CONTROL_MAP,
    raw_fallback=RawFallbackLayout(
        button_map=XBOX_BUTTON_MAP,
        trigger_axes={2: LEFT_TRIGGER, 5: RIGHT_TRIGGER},
        left_stick_axes=(0, 1),
        right_stick_axes=(3, 4),
        dpad_hat_index=0,
    ),
    name_match_requires_standard_controller=True,
    allow_shape_only_match=False,
)

GENERIC_STANDARD_TEMPLATE = DeviceTemplate(
    family_id="standard_controller",
    title="Standard Controller",
    diagram_kind="unknown",
    has_exact_diagram=False,
    name_tokens=(),
    guid_fragments=(),
    shape_patterns=(),
    visible_controls=STANDARD_VISIBLE_ORDER,
    control_labels=GENERIC_STANDARD_LABELS,
    standard_control_map=POSITION_STANDARD_CONTROL_MAP,
    raw_fallback=RawFallbackLayout(button_map=GENERIC_BUTTON_MAP),
)

UNKNOWN_DEVICE_TEMPLATE = DeviceTemplate(
    family_id="unknown_controller",
    title="Unknown Controller",
    diagram_kind="unknown",
    has_exact_diagram=False,
    name_tokens=(),
    guid_fragments=(),
    shape_patterns=(),
    visible_controls=(),
    control_labels={},
)

SUPPORTED_DEVICE_TEMPLATES = (
    ZERO2_TEMPLATE,
    XBOX_TEMPLATE,
)

KNOWN_DEVICE_TEMPLATES = SUPPORTED_DEVICE_TEMPLATES + (
    GENERIC_STANDARD_TEMPLATE,
    UNKNOWN_DEVICE_TEMPLATE,
)

DEVICE_TEMPLATES_BY_FAMILY = {
    template.family_id: template
    for template in KNOWN_DEVICE_TEMPLATES
}
