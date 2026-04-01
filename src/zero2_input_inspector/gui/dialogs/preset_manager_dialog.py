from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...domain.state import UiSnapshot
from ...services.mapper_service import MapperService
from ..widgets.stable_combobox import StableComboBox


class PresetManagerDialog(QDialog):
    def __init__(self, service: MapperService, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._service = service
        self._snapshot: Optional[UiSnapshot] = None
        self._updating = False
        self._current_language = ""

        self.setModal(False)
        self.resize(460, 280)

        self._build_ui()
        self._retranslate()

    def apply_snapshot(self, snapshot: UiSnapshot) -> None:
        self._snapshot = snapshot
        if snapshot.selected_language != self._current_language:
            self.retranslate_ui(snapshot.selected_language)

        self._updating = True
        try:
            selected_app_profile = snapshot.selected_app_profile
            selected_preset = snapshot.selected_preset
            presets = selected_app_profile.presets if selected_app_profile is not None else ()
            self._preset_combo.sync_items(
                ((preset.name, index) for index, preset in enumerate(presets)),
                selected_app_profile.active_preset_index if selected_app_profile is not None else None,
            )
            preset_count = len(presets)
            has_preset = selected_preset is not None
            self._previous_button.setEnabled(has_preset)
            self._next_button.setEnabled(has_preset)
            self._add_button.setEnabled(selected_app_profile is not None and preset_count < 5)
            self._delete_button.setEnabled(preset_count > 1)
            self._preset_name_edit.setEnabled(has_preset)
            self._save_button.setEnabled(has_preset)
            self._sync_line_edit(self._preset_name_edit, selected_preset.name if selected_preset is not None else "")
        finally:
            self._updating = False

    def retranslate_ui(self, language: str) -> None:
        self._current_language = language
        self._retranslate()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        card = QFrame(self)
        card.setObjectName("DialogCard")
        layout = QGridLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        self._preset_label = QLabel(card)
        self._preset_combo = StableComboBox(card)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self._previous_button = QPushButton(card)
        self._previous_button.clicked.connect(self._on_previous_clicked)
        self._next_button = QPushButton(card)
        self._next_button.clicked.connect(self._on_next_clicked)
        self._add_button = QPushButton(card)
        self._add_button.clicked.connect(self._on_add_clicked)
        self._delete_button = QPushButton(card)
        self._delete_button.setObjectName("DangerButton")
        self._delete_button.clicked.connect(self._on_delete_clicked)
        self._preset_name_label = QLabel(card)
        self._preset_name_edit = QLineEdit(card)

        layout.addWidget(self._preset_label, 0, 0)
        layout.addWidget(self._preset_combo, 0, 1, 1, 3)
        layout.addWidget(self._previous_button, 1, 0)
        layout.addWidget(self._next_button, 1, 1)
        layout.addWidget(self._add_button, 1, 2)
        layout.addWidget(self._delete_button, 1, 3)
        layout.addWidget(self._preset_name_label, 2, 0)
        layout.addWidget(self._preset_name_edit, 2, 1, 1, 3)
        root.addWidget(card)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._save_button = QPushButton(self)
        self._save_button.setObjectName("PrimaryButton")
        self._save_button.clicked.connect(self._on_save_clicked)
        self._close_button = QPushButton(self)
        self._close_button.clicked.connect(self.hide)
        footer.addWidget(self._save_button)
        footer.addWidget(self._close_button)
        root.addLayout(footer)

    def _retranslate(self) -> None:
        self.setWindowTitle(self._service.tr("preset_manager"))
        self._preset_label.setText("{label}:".format(label=self._service.tr("preset")))
        self._previous_button.setText(self._service.tr("previous"))
        self._next_button.setText(self._service.tr("next"))
        self._add_button.setText(self._service.tr("add"))
        self._delete_button.setText(self._service.tr("delete"))
        self._preset_name_label.setText("{label}:".format(label=self._service.tr("preset_name")))
        self._save_button.setText(self._service.tr("save"))
        self._close_button.setText(self._service.tr("close"))

    def _sync_line_edit(self, line_edit: QLineEdit, value: str) -> None:
        if line_edit.hasFocus() or line_edit.isModified():
            return
        was_blocked = line_edit.blockSignals(True)
        try:
            line_edit.setText(value)
            line_edit.setModified(False)
        finally:
            line_edit.blockSignals(was_blocked)

    def _selected_device_id(self) -> str:
        if self._snapshot is None:
            return ""
        return self._snapshot.selected_device_id

    def _on_preset_changed(self) -> None:
        if self._updating:
            return
        device_id = self._selected_device_id()
        preset_index = int(self._preset_combo.currentData() or 0)
        if device_id:
            self._service.select_preset(device_id, preset_index)

    def _on_previous_clicked(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.previous_selected_preset(device_id)

    def _on_next_clicked(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.next_selected_preset(device_id)

    def _on_add_clicked(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.add_preset(device_id)

    def _on_delete_clicked(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.delete_selected_preset(device_id)

    def _on_save_clicked(self) -> None:
        device_id = self._selected_device_id()
        if not device_id:
            return
        self._service.rename_selected_preset(device_id, self._preset_name_edit.text())
        self.hide()
