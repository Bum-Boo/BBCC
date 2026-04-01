from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, List, Sequence, Tuple


MODIFIER_ORDER: Tuple[str, ...] = ("Ctrl", "Alt", "Shift", "Win")
MODIFIER_SET = set(MODIFIER_ORDER)

SHORTCUT_TOKEN_ALIASES = {
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "alt": "Alt",
    "option": "Alt",
    "shift": "Shift",
    "win": "Win",
    "windows": "Win",
    "cmd": "Win",
    "meta": "Win",
    "super": "Win",
    "space": "Space",
    "tab": "Tab",
    "enter": "Enter",
    "return": "Enter",
    "escape": "Escape",
    "esc": "Escape",
    "backspace": "Backspace",
    "delete": "Delete",
    "del": "Delete",
    "insert": "Insert",
    "ins": "Insert",
    "home": "Home",
    "end": "End",
    "pageup": "Page Up",
    "pgup": "Page Up",
    "pagedown": "Page Down",
    "pgdown": "Page Down",
    "up": "Arrow Up",
    "arrowup": "Arrow Up",
    "down": "Arrow Down",
    "arrowdown": "Arrow Down",
    "left": "Arrow Left",
    "arrowleft": "Arrow Left",
    "right": "Arrow Right",
    "arrowright": "Arrow Right",
    "capslock": "Caps Lock",
    "scrolllock": "Scroll Lock",
    "printscreen": "Print Screen",
    "prtsc": "Print Screen",
    "pause": "Pause/Break",
    "break": "Pause/Break",
    "pausebreak": "Pause/Break",
    "contextmenu": "Context Menu",
    "menu": "Context Menu",
    "volumeup": "Volume Up",
    "volumedown": "Volume Down",
    "volumemute": "Volume Mute",
    "mediaplaypause": "Media Play/Pause",
    "playpause": "Media Play/Pause",
    "mediaplay": "Media Play/Pause",
    "medianexttrack": "Media Next Track",
    "nexttrack": "Media Next Track",
    "mediaprevioustrack": "Media Previous Track",
    "prevtrack": "Media Previous Track",
    "previoustrack": "Media Previous Track",
    "mediastop": "Media Stop",
    "stop": "Media Stop",
}

SHORTCUT_PICKER_SECTIONS: Tuple[Tuple[str, Tuple[Tuple[str, str], ...]], ...] = (
    (
        "Media",
        (
            ("Play/Pause", "Media Play/Pause"),
            ("Next Track", "Media Next Track"),
            ("Previous Track", "Media Previous Track"),
            ("Stop", "Media Stop"),
            ("Mute", "Volume Mute"),
            ("Volume Up", "Volume Up"),
            ("Volume Down", "Volume Down"),
        ),
    ),
    (
        "Navigation",
        (
            ("Arrow Up", "Arrow Up"),
            ("Arrow Down", "Arrow Down"),
            ("Arrow Left", "Arrow Left"),
            ("Arrow Right", "Arrow Right"),
            ("Page Up", "Page Up"),
            ("Page Down", "Page Down"),
            ("Home", "Home"),
            ("End", "End"),
        ),
    ),
    (
        "Editing",
        (
            ("Enter", "Enter"),
            ("Escape", "Escape"),
            ("Tab", "Tab"),
            ("Backspace", "Backspace"),
            ("Delete", "Delete"),
            ("Insert", "Insert"),
            ("Space", "Space"),
            ("Print Screen", "Print Screen"),
            ("Scroll Lock", "Scroll Lock"),
            ("Pause/Break", "Pause/Break"),
            ("Caps Lock", "Caps Lock"),
            ("Context Menu", "Context Menu"),
        ),
    ),
    (
        "Modifiers",
        (
            ("Ctrl", "Ctrl"),
            ("Shift", "Shift"),
            ("Alt", "Alt"),
            ("Win", "Win"),
        ),
    ),
    (
        "Function Keys",
        tuple(("F{index}".format(index=index), "F{index}".format(index=index)) for index in range(1, 13)),
    ),
)

SPECIAL_SHORTCUT_PRESET_GROUPS: Tuple[Tuple[str, Tuple[Tuple[str, str], ...]], ...] = (
    (
        "Media",
        (
            ("Play/Pause", "Media Play/Pause"),
            ("Next Track", "Media Next Track"),
            ("Previous Track", "Media Previous Track"),
            ("Stop", "Media Stop"),
            ("Mute", "Volume Mute"),
            ("Volume Up", "Volume Up"),
            ("Volume Down", "Volume Down"),
        ),
    ),
    (
        "Browser",
        (
            ("Back", "Alt+Left"),
            ("Forward", "Alt+Right"),
            ("Refresh", "F5"),
        ),
    ),
    (
        "Navigation",
        (
            ("Home", "Home"),
            ("End", "End"),
            ("Page Up", "Page Up"),
            ("Page Down", "Page Down"),
        ),
    ),
)

@dataclass(frozen=True)
class ShortcutBinding:
    modifiers: Tuple[str, ...]
    key: str

    def to_text(self) -> str:
        return "+".join((*self.modifiers, self.key)) if self.modifiers else self.key


def normalize_shortcut_text(text: str) -> str:
    if not text:
        return ""
    try:
        return parse_shortcut_text(text).to_text()
    except ValueError:
        return text.strip()


def format_shortcut_text(text: str) -> str:
    return normalize_shortcut_text(text)


def parse_shortcut_text(text: str) -> ShortcutBinding:
    tokens = [normalize_shortcut_token(token) for token in text.split("+") if token.strip()]
    if not tokens:
        raise ValueError("Shortcut is empty.")

    if len(tokens) == 1:
        return ShortcutBinding((), tokens[0])

    modifiers: List[str] = []
    for token in tokens[:-1]:
        if token not in MODIFIER_SET:
            raise ValueError("Unsupported shortcut token: {token}".format(token=token))
        if token not in modifiers:
            modifiers.append(token)

    key = tokens[-1]
    if key in MODIFIER_SET and len(tokens) == 2:
        return ShortcutBinding((tokens[0],), key)
    if key in MODIFIER_SET and len(tokens) > 2:
        raise ValueError("Unsupported shortcut token: {token}".format(token=key))

    ordered_modifiers = tuple(modifier for modifier in MODIFIER_ORDER if modifier in modifiers)
    return ShortcutBinding(ordered_modifiers, key)


def normalize_shortcut_token(token: str) -> str:
    stripped = token.strip()
    if not stripped:
        return ""
    compact = re.sub(r"[\s_\-\/]+", "", stripped.lower())
    alias = SHORTCUT_TOKEN_ALIASES.get(compact)
    if alias is not None:
        return alias
    if re.fullmatch(r"f([1-9]|1[0-2])", compact):
        return compact.upper()
    if len(compact) == 1:
        return compact.upper() if compact.isalpha() else compact
    return stripped


@lru_cache(maxsize=1)
def get_special_shortcut_preset_values() -> frozenset[str]:
    return frozenset(
        normalize_shortcut_text(shortcut_text)
        for _group_name, entries in SPECIAL_SHORTCUT_PRESET_GROUPS
        for _display_text, shortcut_text in entries
    )
