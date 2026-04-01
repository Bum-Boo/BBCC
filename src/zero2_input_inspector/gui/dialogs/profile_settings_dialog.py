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


class ProfileSettingsDialog(QDialog):
    def __init__(self, service: MapperService, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._service = service
        self._snapshot: Optional[UiSnapshot] = None
        self._updating = False
        self._current_language = ""

        self.setModal(False)
        self.resize(540, 440)

        self._build_ui()
        self._retranslate()

    def apply_snapshot(self, snapshot: UiSnapshot) -> None:
        self._snapshot = snapshot
        if snapshot.selected_language != self._current_language:
            self.retranslate_ui(snapshot.selected_language)

        self._updating = True
        try:
            selected_device = snapshot.selected_device_profile
            selected_app_profile = snapshot.selected_app_profile
            app_profiles = selected_device.app_profiles if selected_device is not None else ()
            self._app_combo.sync_items(
                ((app_profile.name, app_profile.app_profile_id) for app_profile in app_profiles),
                selected_app_profile.app_profile_id if selected_app_profile is not None else None,
            )
            self._add_button.setEnabled(selected_device is not None)
            self._delete_button.setEnabled(selected_device is not None and len(app_profiles) > 1)
            self._profile_name_edit.setEnabled(selected_app_profile is not None)
            self._process_name_edit.setEnabled(selected_app_profile is not None)
            self._save_button.setEnabled(selected_app_profile is not None)
            self._sync_line_edit(
                self._profile_name_edit,
                selected_app_profile.name if selected_app_profile is not None else "",
            )
            self._sync_line_edit(
                self._process_name_edit,
                selected_app_profile.process_name if selected_app_profile is not None else "",
            )
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

        self._app_label = QLabel(card)
        self._app_combo = StableComboBox(card)
        self._app_combo.currentIndexChanged.connect(self._on_app_profile_changed)
        self._add_button = QPushButton(card)
        self._add_button.clicked.connect(self._on_add_clicked)
        self._delete_button = QPushButton(card)
        self._delete_button.setObjectName("DangerButton")
        self._delete_button.clicked.connect(self._on_delete_clicked)
        self._profile_name_label = QLabel(card)
        self._profile_name_edit = QLineEdit(card)
        self._process_name_label = QLabel(card)
        self._process_name_edit = QLineEdit(card)
        self._hint_label = QLabel(card)
        self._hint_label.setObjectName("MutedText")
        self._hint_label.setWordWrap(True)

        layout.addWidget(self._app_label, 0, 0)
        layout.addWidget(self._app_combo, 0, 1, 1, 2)
        layout.addWidget(self._add_button, 1, 1)
        layout.addWidget(self._delete_button, 1, 2)
        layout.addWidget(self._profile_name_label, 2, 0)
        layout.addWidget(self._profile_name_edit, 2, 1, 1, 2)
        layout.addWidget(self._process_name_label, 3, 0)
        layout.addWidget(self._process_name_edit, 3, 1, 1, 2)
        layout.addWidget(self._hint_label, 4, 0, 1, 3)

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
        self.setWindowTitle(self._service.tr("profile_settings"))
        self._app_label.setText("{label}:".format(label=self._service.tr("app_profile")))
        self._add_button.setText(self._service.tr("add_app"))
        self._delete_button.setText(self._service.tr("delete_app"))
        self._profile_name_label.setText("{label}:".format(label=self._service.tr("profile_name")))
        self._process_name_label.setText("{label}:".format(label=self._service.tr("process_name")))
        self._hint_label.setText(self._service.tr("process_wildcard_hint"))
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

    def _on_app_profile_changed(self) -> None:
        if self._updating:
            return
        device_id = self._selected_device_id()
        app_profile_id = self._app_combo.currentData()
        if device_id and app_profile_id is not None:
            self._service.select_app_profile(device_id, str(app_profile_id))

    def _on_add_clicked(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.add_app_profile(device_id)

    def _on_delete_clicked(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.delete_selected_app_profile(device_id)

    def _on_save_clicked(self) -> None:
        device_id = self._selected_device_id()
        if not device_id:
            return
        self._service.update_selected_app_profile(
            device_id,
            self._profile_name_edit.text(),
            self._process_name_edit.text(),
        )
        self.hide()
