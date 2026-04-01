from __future__ import annotations

from typing import Dict, Tuple

DPAD_UP = "DPAD_UP"
DPAD_DOWN = "DPAD_DOWN"
DPAD_LEFT = "DPAD_LEFT"
DPAD_RIGHT = "DPAD_RIGHT"
FACE_NORTH = "FACE_NORTH"
FACE_SOUTH = "FACE_SOUTH"
FACE_WEST = "FACE_WEST"
FACE_EAST = "FACE_EAST"
L = "L"
R = "R"
SELECT = "SELECT"
START = "START"
GUIDE = "GUIDE"
LEFT_TRIGGER = "LEFT_TRIGGER"
RIGHT_TRIGGER = "RIGHT_TRIGGER"
LEFT_STICK_PRESS = "LEFT_STICK_PRESS"
RIGHT_STICK_PRESS = "RIGHT_STICK_PRESS"
LEFT_STICK_UP = "LEFT_STICK_UP"
LEFT_STICK_DOWN = "LEFT_STICK_DOWN"
LEFT_STICK_LEFT = "LEFT_STICK_LEFT"
LEFT_STICK_RIGHT = "LEFT_STICK_RIGHT"
RIGHT_STICK_UP = "RIGHT_STICK_UP"
RIGHT_STICK_DOWN = "RIGHT_STICK_DOWN"
RIGHT_STICK_LEFT = "RIGHT_STICK_LEFT"
RIGHT_STICK_RIGHT = "RIGHT_STICK_RIGHT"

# Backward-compatible aliases for existing persisted mappings.
LEFT_SHOULDER = L
RIGHT_SHOULDER = R

CONTROL_ORDER: Tuple[str, ...] = (
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
    GUIDE,
    LEFT_TRIGGER,
    RIGHT_TRIGGER,
    LEFT_STICK_PRESS,
    RIGHT_STICK_PRESS,
    LEFT_STICK_UP,
    LEFT_STICK_DOWN,
    LEFT_STICK_LEFT,
    LEFT_STICK_RIGHT,
    RIGHT_STICK_UP,
    RIGHT_STICK_DOWN,
    RIGHT_STICK_LEFT,
    RIGHT_STICK_RIGHT,
)

CONTROL_DISPLAY_NAMES: Dict[str, str] = {
    L: "L",
    R: "R",
    SELECT: "Select",
    START: "Start",
    DPAD_UP: "D-Pad Up",
    DPAD_DOWN: "D-Pad Down",
    DPAD_LEFT: "D-Pad Left",
    DPAD_RIGHT: "D-Pad Right",
    FACE_NORTH: "Face North",
    FACE_SOUTH: "Face South",
    FACE_WEST: "Face West",
    FACE_EAST: "Face East",
    GUIDE: "Guide",
    LEFT_TRIGGER: "Left Trigger",
    RIGHT_TRIGGER: "Right Trigger",
    LEFT_STICK_PRESS: "Left Stick Press",
    RIGHT_STICK_PRESS: "Right Stick Press",
    LEFT_STICK_UP: "Left Stick Up",
    LEFT_STICK_DOWN: "Left Stick Down",
    LEFT_STICK_LEFT: "Left Stick Left",
    LEFT_STICK_RIGHT: "Left Stick Right",
    RIGHT_STICK_UP: "Right Stick Up",
    RIGHT_STICK_DOWN: "Right Stick Down",
    RIGHT_STICK_LEFT: "Right Stick Left",
    RIGHT_STICK_RIGHT: "Right Stick Right",
}

CONTROL_ALIASES: Dict[str, str] = {
    "LEFT_SHOULDER": L,
    "RIGHT_SHOULDER": R,
}

PRESET_PREVIOUS_CONTROL = SELECT
PRESET_NEXT_CONTROL = START


def canonicalize_control_id(control_id: str) -> str:
    return CONTROL_ALIASES.get(control_id, control_id)
