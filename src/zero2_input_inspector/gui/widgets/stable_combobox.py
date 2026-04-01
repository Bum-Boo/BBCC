from __future__ import annotations

from typing import Iterable, Optional, Tuple

from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import QComboBox, QWidget


class StableComboBox(QComboBox):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self._items_signature: Tuple[Tuple[str, object], ...] = ()
        self._pending_items_signature: Optional[Tuple[Tuple[str, object], ...]] = None
        self._pending_selected_data: object = None
        self._popup_open = False
        self._popup_user_changed = False
        self.currentIndexChanged.connect(self._on_current_index_changed)
        self.view().viewport().installEventFilter(self)

    def sync_items(self, items: Iterable[Tuple[str, object]], selected_data: object = None) -> None:
        normalized_items = tuple((str(text), data) for text, data in items)
        if self._popup_open:
            self._pending_items_signature = normalized_items
            self._pending_selected_data = selected_data
            return
        self._apply_items(normalized_items, selected_data)

    def is_popup_open(self) -> bool:
        return self._popup_open

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._popup_open:
            event.accept()
            return
        if self.hasFocus():
            super().wheelEvent(event)
            return
        event.accept()

    def showPopup(self) -> None:
        self._popup_open = True
        self._popup_user_changed = False
        self.setFocus(Qt.PopupFocusReason)
        super().showPopup()
        self.view().setFocus(Qt.PopupFocusReason)

    def hidePopup(self) -> None:
        super().hidePopup()
        self._popup_open = False
        if self._pending_items_signature is not None:
            pending_items = self._pending_items_signature
            pending_selected_data = self._pending_selected_data
            self._pending_items_signature = None
            self._pending_selected_data = None
            if self._popup_user_changed:
                current_data = self.currentData()
                if current_data is not None:
                    pending_selected_data = current_data
            self._apply_items(pending_items, pending_selected_data)
        self._popup_user_changed = False

    def _apply_items(self, items: Tuple[Tuple[str, object], ...], selected_data: object) -> None:
        if items != self._items_signature:
            was_blocked = self.blockSignals(True)
            try:
                self.clear()
                for text, data in items:
                    self.addItem(text, data)
                self._items_signature = items
            finally:
                self.blockSignals(was_blocked)
        self._sync_current_index(selected_data)

    def _sync_current_index(self, selected_data: object) -> None:
        if self.count() == 0:
            if self.currentIndex() != -1:
                was_blocked = self.blockSignals(True)
                try:
                    self.setCurrentIndex(-1)
                finally:
                    self.blockSignals(was_blocked)
            return

        target_index = self.findData(selected_data) if selected_data is not None else -1
        if target_index < 0:
            if selected_data is None:
                current_index = self.currentIndex()
                if 0 <= current_index < self.count():
                    target_index = current_index
                else:
                    target_index = 0
            else:
                target_index = 0

        if target_index != self.currentIndex():
            was_blocked = self.blockSignals(True)
            try:
                self.setCurrentIndex(target_index)
            finally:
                self.blockSignals(was_blocked)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.view().viewport() and event.type() == QEvent.Wheel:
            return False
        return super().eventFilter(watched, event)

    def _on_current_index_changed(self, _index: int) -> None:
        if self._popup_open:
            self._popup_user_changed = True
