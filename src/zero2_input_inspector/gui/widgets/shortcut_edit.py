from __future__ import annotations

from typing import Dict

from PyQt5.QtCore import QEvent, Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QLineEdit

from ...services.shortcuts import normalize_shortcut_text


def _qt_shortcut_token_map() -> Dict[int, str]:
    token_map = {
        Qt.Key_Space: "Space",
        Qt.Key_Tab: "Tab",
        Qt.Key_Return: "Enter",
        Qt.Key_Enter: "Enter",
        Qt.Key_Escape: "Escape",
        Qt.Key_Backspace: "Backspace",
        Qt.Key_Delete: "Delete",
        Qt.Key_Insert: "Insert",
        Qt.Key_Home: "Home",
        Qt.Key_End: "End",
        Qt.Key_PageUp: "Page Up",
        Qt.Key_PageDown: "Page Down",
        Qt.Key_Up: "Arrow Up",
        Qt.Key_Down: "Arrow Down",
        Qt.Key_Left: "Arrow Left",
        Qt.Key_Right: "Arrow Right",
        Qt.Key_CapsLock: "Caps Lock",
        Qt.Key_ScrollLock: "Scroll Lock",
        Qt.Key_Print: "Print Screen",
        Qt.Key_Pause: "Pause/Break",
        Qt.Key_Menu: "Context Menu",
        Qt.Key_BracketLeft: "[",
        Qt.Key_BracketRight: "]",
        Qt.Key_Minus: "-",
        Qt.Key_Equal: "=",
        Qt.Key_Comma: ",",
        Qt.Key_Period: ".",
        Qt.Key_Slash: "/",
        Qt.Key_Backslash: "\\",
        Qt.Key_Semicolon: ";",
        Qt.Key_Apostrophe: "'",
        Qt.Key_QuoteLeft: "`",
        Qt.Key_MediaPlay: "Media Play/Pause",
        Qt.Key_MediaPause: "Media Play/Pause",
        Qt.Key_MediaStop: "Media Stop",
        Qt.Key_MediaNext: "Media Next Track",
        Qt.Key_MediaPrevious: "Media Previous Track",
        Qt.Key_VolumeMute: "Volume Mute",
        Qt.Key_VolumeDown: "Volume Down",
        Qt.Key_VolumeUp: "Volume Up",
    }
    if hasattr(Qt, "Key_Super_L"):
        token_map[getattr(Qt, "Key_Super_L")] = "Win"
    if hasattr(Qt, "Key_Super_R"):
        token_map[getattr(Qt, "Key_Super_R")] = "Win"
    return token_map


QT_SHORTCUT_TOKEN_MAP = _qt_shortcut_token_map()


class ShortcutEdit(QLineEdit):
    shortcutCaptured = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Ctrl+Z")

    def is_popup_open(self) -> bool:
        return False

    def event(self, event) -> bool:
        if event.type() == QEvent.KeyPress:
            shortcut = self._shortcut_from_key_event(event)
            if shortcut:
                self._apply_shortcut(shortcut)
                event.accept()
                return True
        return super().event(event)

    def _shortcut_from_key_event(self, event: QKeyEvent) -> str:
        if event.key() in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return ""

        modifiers = []
        if event.modifiers() & Qt.ControlModifier:
            modifiers.append("Ctrl")
        if event.modifiers() & Qt.AltModifier:
            modifiers.append("Alt")
        if event.modifiers() & Qt.ShiftModifier:
            modifiers.append("Shift")
        if event.modifiers() & Qt.MetaModifier:
            modifiers.append("Win")

        token = QT_SHORTCUT_TOKEN_MAP.get(event.key())
        if token is None:
            if Qt.Key_F1 <= event.key() <= Qt.Key_F12:
                token = "F{index}".format(index=event.key() - Qt.Key_F1 + 1)
            elif Qt.Key_0 <= event.key() <= Qt.Key_9:
                token = chr(ord("0") + (event.key() - Qt.Key_0))
            elif Qt.Key_A <= event.key() <= Qt.Key_Z:
                token = chr(ord("A") + (event.key() - Qt.Key_A))
            else:
                return ""

        if not modifiers and token in {"Ctrl", "Alt", "Shift", "Win"}:
            return ""
        return normalize_shortcut_text("+".join((*modifiers, token)) if modifiers else token)

    def _apply_shortcut(self, shortcut: str) -> None:
        normalized = normalize_shortcut_text(shortcut)
        was_blocked = self.blockSignals(True)
        try:
            self.setText(normalized)
            self.setModified(True)
        finally:
            self.blockSignals(was_blocked)
        self.shortcutCaptured.emit(normalized)
