from __future__ import annotations

from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...domain.state import DeviceListEntry
from ...styles import current_theme_id, current_theme_tokens


class DeviceEntryWidget(QFrame):
    def __init__(self, entry: DeviceListEntry, connected_text: str, disconnected_text: str) -> None:
        super().__init__()
        self.setObjectName("DeviceItemCard")
        self.setProperty("selected", entry.is_selected)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        dot = QFrame(self)
        dot.setFixedSize(10, 10)
        theme = current_theme_tokens()
        if entry.is_connected:
            dot.setStyleSheet(
                "background: {color}; border-radius: 5px;".format(color=theme["accent_neon"])
            )
        else:
            dot.setStyleSheet(
                "background: {color}; border-radius: 5px;".format(color=theme["border_strong"])
            )
        layout.addWidget(dot, 0, Qt.AlignTop)

        text_column = QVBoxLayout()
        text_column.setSpacing(2)

        name_label = QLabel(entry.display_name, self)
        name_label.setObjectName("StrongText" if entry.is_connected else "MutedText")
        if entry.is_connected:
            font = name_label.font()
            font.setBold(True)
            name_label.setFont(font)
        text_column.addWidget(name_label)

        subtitle_label = QLabel(entry.subtitle, self)
        subtitle_label.setObjectName("MutedText")
        text_column.addWidget(subtitle_label)
        layout.addLayout(text_column, 1)

        status_label = QLabel(connected_text if entry.is_connected else disconnected_text, self)
        status_label.setObjectName("ConnectedPill" if entry.is_connected else "DisconnectedPill")
        layout.addWidget(status_label, 0, Qt.AlignVCenter)


class DeviceListWidget(QListWidget):
    device_selected = pyqtSignal(str)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setSpacing(8)
        self.setUniformItemSizes(False)
        self.setSelectionMode(QListWidget.SingleSelection)
        self._entries_signature = ()
        self.currentItemChanged.connect(self._handle_current_item_changed)
        self.itemClicked.connect(self._handle_item_clicked)

    def set_entries(
        self,
        entries,
        connected_text: str,
        disconnected_text: str,
    ) -> None:
        entries_list = list(entries)
        entries_signature = tuple(
            (
                entry.device_id,
                entry.display_name,
                entry.subtitle,
                entry.is_connected,
                entry.is_selected,
            )
            for entry in entries_list
        ) + ((connected_text, disconnected_text, current_theme_id()),)
        if entries_signature == self._entries_signature:
            return

        current_device_id = self.current_device_id()
        was_blocked = self.blockSignals(True)
        try:
            self.clear()
            selected_item = None
            for entry in entries_list:
                item = QListWidgetItem(self)
                item.setData(Qt.UserRole, entry.device_id)
                item.setSizeHint(QSize(220, 72))
                widget = DeviceEntryWidget(entry, connected_text, disconnected_text)
                self.addItem(item)
                self.setItemWidget(item, widget)
                if entry.is_selected or (current_device_id and current_device_id == entry.device_id):
                    selected_item = item
            if selected_item is not None:
                self.setCurrentItem(selected_item)
        finally:
            self.blockSignals(was_blocked)
        self._entries_signature = entries_signature

    def current_device_id(self) -> str:
        item = self.currentItem()
        if item is None:
            return ""
        return str(item.data(Qt.UserRole))

    def _handle_current_item_changed(self, current, previous) -> None:
        if current is None:
            return
        self.device_selected.emit(str(current.data(Qt.UserRole)))

    def _handle_item_clicked(self, item) -> None:
        if item is None:
            return
        self.device_selected.emit(str(item.data(Qt.UserRole)))
