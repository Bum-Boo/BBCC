from __future__ import annotations

import ctypes
from typing import Optional, Sequence

from pynput.keyboard import Controller, Key
from pynput.mouse import Button, Controller as MouseController

from .shortcuts import ShortcutBinding, normalize_shortcut_text, parse_shortcut_text

USER32 = ctypes.windll.user32
KEYEVENTF_KEYUP = 0x0002

SPECIAL_KEY_TO_PYNPUT = {
    "Space": Key.space,
    "Tab": Key.tab,
    "Enter": Key.enter,
    "Escape": Key.esc,
    "Backspace": Key.backspace,
    "Delete": Key.delete,
    "Insert": Key.insert,
    "Home": Key.home,
    "End": Key.end,
    "Page Up": Key.page_up,
    "Page Down": Key.page_down,
    "Arrow Up": Key.up,
    "Arrow Down": Key.down,
    "Arrow Left": Key.left,
    "Arrow Right": Key.right,
    "Caps Lock": Key.caps_lock,
    "Scroll Lock": Key.scroll_lock,
    "Print Screen": Key.print_screen,
    "Pause/Break": getattr(Key, "pause", None),
    "Context Menu": Key.menu,
    "Win": Key.cmd,
}

SPECIAL_KEY_TO_VK = {
    "Volume Up": 0xAF,
    "Volume Down": 0xAE,
    "Volume Mute": 0xAD,
    "Media Play/Pause": 0xB3,
    "Media Next Track": 0xB0,
    "Media Previous Track": 0xB1,
    "Media Stop": 0xB2,
    "Pause/Break": 0x13,
}


class KeyboardShortcutSender:
    def __init__(self) -> None:
        self._controller = Controller()
        self._mouse = MouseController()

    def send(self, shortcut: str) -> Optional[str]:
        normalized = normalize_shortcut_text(shortcut)
        if not normalized.strip():
            return None

        try:
            binding = parse_shortcut_text(normalized)
        except ValueError as exc:
            return str(exc)

        try:
            if self._send_media_key(binding):
                return None
            self._send_binding(binding)
        except Exception as exc:
            return str(exc)
        return None

    def release_all(self) -> None:
        for key in (Key.ctrl, Key.alt, Key.shift, Key.cmd):
            try:
                self._controller.release(key)
            except Exception:
                pass

    def move_mouse(self, dx: int, dy: int) -> None:
        self._mouse.move(int(dx), int(dy))

    def scroll_mouse(self, dx: int, dy: int) -> None:
        self._mouse.scroll(int(dx), int(dy))

    def click_mouse(self, button: str, count: int = 1) -> Optional[str]:
        resolved_button = self._resolve_mouse_button(button)
        if resolved_button is None:
            return "Unsupported mouse button: {button}".format(button=button)
        try:
            self._mouse.click(resolved_button, count)
        except Exception as exc:
            return str(exc)
        return None

    def _send_binding(self, binding: ShortcutBinding) -> None:
        pressed_keys: Sequence[object] = self._resolve_keys(binding)
        held_keys = []
        try:
            for key in pressed_keys:
                self._controller.press(key)
                held_keys.append(key)
            for key in reversed(held_keys):
                self._controller.release(key)
        except Exception:
            for key in reversed(held_keys):
                try:
                    self._controller.release(key)
                except Exception:
                    pass
            raise

    def _send_media_key(self, binding: ShortcutBinding) -> bool:
        if binding.modifiers:
            return False
        vk_code = SPECIAL_KEY_TO_VK.get(binding.key)
        if vk_code is None:
            return False
        USER32.keybd_event(vk_code, 0, 0, 0)
        USER32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
        return True

    def _resolve_keys(self, binding: ShortcutBinding) -> Sequence[object]:
        keys = [self._resolve_modifier(modifier) for modifier in binding.modifiers]
        keys.append(self._resolve_key(binding.key))
        return keys

    def _resolve_modifier(self, modifier: str) -> object:
        if modifier == "Ctrl":
            return Key.ctrl
        if modifier == "Alt":
            return Key.alt
        if modifier == "Shift":
            return Key.shift
        if modifier == "Win":
            return Key.cmd
        raise ValueError("Unsupported modifier token: {token}".format(token=modifier))

    def _resolve_key(self, token: str) -> object:
        if token == "Ctrl":
            return Key.ctrl
        if token == "Alt":
            return Key.alt
        if token == "Shift":
            return Key.shift
        if token == "Win":
            return Key.cmd
        if token in SPECIAL_KEY_TO_PYNPUT and SPECIAL_KEY_TO_PYNPUT[token] is not None:
            return SPECIAL_KEY_TO_PYNPUT[token]
        if token in SPECIAL_KEY_TO_VK:
            return token
        if token.startswith("F") and token[1:].isdigit():
            return getattr(Key, token.lower())
        if len(token) == 1:
            return token.lower()
        raise ValueError("Unsupported shortcut token: {token}".format(token=token))

    def _resolve_mouse_button(self, token: str) -> Optional[Button]:
        normalized = str(token or "").strip().lower()
        if normalized == "left":
            return Button.left
        if normalized == "right":
            return Button.right
        if normalized == "middle":
            return Button.middle
        return None
