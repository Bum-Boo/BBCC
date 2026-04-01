from __future__ import annotations

from typing import Optional

from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...domain.state import UiSnapshot
from ...services.mapper_service import MapperService
from ...styles import THEME_DEFINITIONS, normalize_theme_id
from ...services.translations import normalize_language_code
from ..widgets.stable_combobox import StableComboBox


class SettingsDialog(QDialog):
    def __init__(self, service: MapperService, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._service = service
        self._snapshot: Optional[UiSnapshot] = None
        self._updating = False
        self._current_language = ""
        self._pending_language = ""
        self._language_dirty = False
        self._current_theme = ""
        self._pending_theme = ""
        self._theme_dirty = False
        self._closing_after_save = False

        self.setWindowTitle(self._service.tr("settings"))
        self.setModal(False)
        self.resize(500, 340)

        self._build_ui()
        self._retranslate()

    def apply_snapshot(self, snapshot: UiSnapshot) -> None:
        self._snapshot = snapshot
        self._updating = True
        try:
            selected_language = normalize_language_code(snapshot.selected_language)
            if selected_language != self._current_language:
                self.retranslate_ui(selected_language)
            language_to_show = self._pending_language if self._language_dirty else selected_language
            self._language_combo.sync_items(snapshot.available_languages, language_to_show)
            selected_theme = normalize_theme_id(snapshot.selected_theme)
            language_theme = self._pending_theme if self._theme_dirty else selected_theme
            self._theme_combo.sync_items(self._theme_items(), language_theme)
            was_blocked = self._auto_start_checkbox.blockSignals(True)
            try:
                self._auto_start_checkbox.setChecked(snapshot.auto_start_enabled)
            finally:
                self._auto_start_checkbox.blockSignals(was_blocked)
            self._reset_presets_button.setEnabled(snapshot.selected_device_profile is not None)
        finally:
            self._updating = False

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

        self._language_label = QLabel(card)
        self._language_combo = StableComboBox(card)
        self._language_combo.currentIndexChanged.connect(self._on_language_changed)
        self._theme_label = QLabel(card)
        self._theme_combo = StableComboBox(card)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        initial_theme_items = self._theme_items()
        self._theme_combo.sync_items(initial_theme_items, initial_theme_items[0][1] if initial_theme_items else None)
        self._auto_start_checkbox = QCheckBox(card)
        self._auto_start_checkbox.toggled.connect(self._on_auto_start_toggled)
        self._reset_presets_button = QPushButton(card)
        self._reset_presets_button.clicked.connect(self._on_reset_presets)
        self._hint_label = QLabel(card)
        self._hint_label.setObjectName("MutedText")
        self._hint_label.setWordWrap(True)

        layout.addWidget(self._language_label, 0, 0)
        layout.addWidget(self._language_combo, 0, 1)
        layout.addWidget(self._theme_label, 1, 0)
        layout.addWidget(self._theme_combo, 1, 1)
        layout.addWidget(self._auto_start_checkbox, 2, 0, 1, 2)
        layout.addWidget(self._reset_presets_button, 3, 0, 1, 2)
        layout.addWidget(self._hint_label, 4, 0, 1, 2)
        root.addWidget(card)

        footer = QHBoxLayout()
        footer.addStretch(1)
        self._save_button = QPushButton(self)
        self._save_button.setObjectName("PrimaryButton")
        self._save_button.clicked.connect(self._on_save_clicked)
        self._save_button.setDefault(True)
        footer.addWidget(self._save_button)
        self._close_button = QPushButton(self)
        self._close_button.clicked.connect(self._on_close_clicked)
        footer.addWidget(self._close_button)
        root.addLayout(footer)

    def _retranslate(self) -> None:
        self.setWindowTitle(self._service.tr("settings"))
        self._language_label.setText("{label}:".format(label=self._service.tr("language")))
        self._theme_label.setText("{label}:".format(label=self._service.tr("theme")))
        self._auto_start_checkbox.setText(self._service.tr("auto_start"))
        self._reset_presets_button.setText(self._service.tr("reset_presets"))
        self._hint_label.setText(self._service.tr("settings_hint"))
        self._save_button.setText(self._service.tr("save"))
        self._close_button.setText(self._service.tr("close"))

    def retranslate_ui(self, language: str) -> None:
        self._current_language = language
        self._retranslate()

    def _on_language_changed(self, _index: int = 0) -> None:
        if self._updating:
            return
        language = self._language_combo.currentData()
        if language is not None:
            new_language = normalize_language_code(str(language))
            if self._snapshot is not None and new_language == self._snapshot.selected_language:
                self._pending_language = ""
                self._language_dirty = False
            else:
                self._pending_language = new_language
                self._language_dirty = True

    def _on_theme_changed(self, _index: int = 0) -> None:
        if self._updating:
            return
        theme = self._theme_combo.currentData()
        if theme is not None:
            new_theme = normalize_theme_id(str(theme))
            if self._snapshot is not None and new_theme == normalize_theme_id(self._snapshot.selected_theme):
                self._pending_theme = ""
                self._theme_dirty = False
            else:
                self._pending_theme = new_theme
                self._theme_dirty = True

    def _theme_items(self):
        return tuple((self._service.tr(f"theme_{theme_id}"), theme_id) for theme_id in THEME_DEFINITIONS)

    def _on_save_clicked(self) -> None:
        selected_language = ""
        selected_theme = ""
        if self._snapshot is not None:
            selected_language = normalize_language_code(self._pending_language or self._snapshot.selected_language)
            selected_theme = normalize_theme_id(self._pending_theme or self._snapshot.selected_theme)
            self._language_dirty = False
            self._theme_dirty = False
            self._pending_language = ""
            self._pending_theme = ""
            self._service.update_settings(language=selected_language, theme=selected_theme)
        self._closing_after_save = True
        try:
            self.close()
        finally:
            self._closing_after_save = False
            self._language_dirty = False
            self._theme_dirty = False
            self._pending_language = ""
            self._pending_theme = ""

    def _on_auto_start_toggled(self, checked: bool) -> None:
        if self._updating:
            return
        self._service.set_auto_start(checked)

    def _on_reset_presets(self) -> None:
        if self._snapshot is None or not self._snapshot.selected_device_id:
            return
        self._service.reset_selected_app_presets(self._snapshot.selected_device_id)

    def _on_close_clicked(self) -> None:
        self._discard_pending_language()
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._closing_after_save:
            self._discard_pending_language()
        super().closeEvent(event)

    def _discard_pending_language(self) -> None:
        if self._snapshot is None:
            self._language_dirty = False
            self._pending_language = ""
            self._theme_dirty = False
            self._pending_theme = ""
            return
        self._updating = True
        try:
            self._pending_language = ""
            self._language_dirty = False
            self._pending_theme = ""
            self._theme_dirty = False
            self._language_combo.sync_items(
                self._snapshot.available_languages,
                normalize_language_code(self._snapshot.selected_language),
            )
            self._theme_combo.sync_items(
                self._theme_items(),
                normalize_theme_id(self._snapshot.selected_theme),
            )
        finally:
            self._updating = False
