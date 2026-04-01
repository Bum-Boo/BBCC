from __future__ import annotations

from typing import Dict, Optional, Tuple

from PyQt5.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..domain.profiles import (
    MAPPING_ACTION_KEYBOARD,
    MAPPING_ACTION_MOUSE_DOUBLE_CLICK,
    MAPPING_ACTION_MOUSE_LEFT_CLICK,
    MAPPING_ACTION_MOUSE_MIDDLE_CLICK,
    MAPPING_ACTION_MOUSE_MOVE,
    MAPPING_ACTION_MOUSE_SCROLL,
    MAPPING_ACTION_MOUSE_RIGHT_CLICK,
    MAPPING_ACTION_MOUSE_WHEEL_DOWN,
    MAPPING_ACTION_MOUSE_WHEEL_LEFT,
    MAPPING_ACTION_MOUSE_WHEEL_RIGHT,
    MAPPING_ACTION_MOUSE_WHEEL_UP,
)
from ..domain.state import MappingRow, UiSnapshot
from ..identity import APP_PRODUCT_NAME
from ..services.mapper_service import MapperService
from ..services.shortcuts import (
    get_special_shortcut_preset_values,
    format_shortcut_text,
    normalize_shortcut_text,
)
from .dialogs import InspectorDialog, PresetManagerDialog, ProfileSettingsDialog, SettingsDialog
from .widgets import ControllerDiagramWidget, DeviceListWidget, ShortcutEdit, StableComboBox


EDITOR_MAPPING_TYPE_SHORTCUT = "shortcut"
EDITOR_MAPPING_TYPE_SPECIAL = "special"
EDITOR_MAPPING_TYPE_MOUSE = "mouse"

SPECIAL_KEY_GROUPS: Tuple[Tuple[str, Tuple[Tuple[str, str], ...]], ...] = (
    (
        "mapping.special_group_media",
        (
            ("mapping.special_play_pause", "Media Play/Pause"),
            ("mapping.special_next_track", "Media Next Track"),
            ("mapping.special_previous_track", "Media Previous Track"),
            ("mapping.special_stop", "Media Stop"),
            ("mapping.special_mute", "Volume Mute"),
            ("mapping.special_volume_up", "Volume Up"),
            ("mapping.special_volume_down", "Volume Down"),
        ),
    ),
    (
        "mapping.special_group_browser",
        (
            ("mapping.special_back", "Alt+Left"),
            ("mapping.special_forward", "Alt+Right"),
            ("mapping.special_refresh", "F5"),
        ),
    ),
    (
        "mapping.special_group_navigation",
        (
            ("mapping.special_home", "Home"),
            ("mapping.special_end", "End"),
            ("mapping.special_page_up", "Page Up"),
            ("mapping.special_page_down", "Page Down"),
        ),
    ),
)

MOUSE_ACTION_DEFINITIONS: Tuple[Tuple[str, str], ...] = (
    ("mapping.mouse_pointer_movement", MAPPING_ACTION_MOUSE_MOVE),
    ("mapping.mouse_continuous_scroll", MAPPING_ACTION_MOUSE_SCROLL),
    ("mapping.mouse_left_click", MAPPING_ACTION_MOUSE_LEFT_CLICK),
    ("mapping.mouse_right_click", MAPPING_ACTION_MOUSE_RIGHT_CLICK),
    ("mapping.mouse_middle_click", MAPPING_ACTION_MOUSE_MIDDLE_CLICK),
    ("mapping.mouse_double_click", MAPPING_ACTION_MOUSE_DOUBLE_CLICK),
    ("mapping.mouse_wheel_up", MAPPING_ACTION_MOUSE_WHEEL_UP),
    ("mapping.mouse_wheel_down", MAPPING_ACTION_MOUSE_WHEEL_DOWN),
    ("mapping.mouse_wheel_left", MAPPING_ACTION_MOUSE_WHEEL_LEFT),
    ("mapping.mouse_wheel_right", MAPPING_ACTION_MOUSE_WHEEL_RIGHT),
)

DEVICE_DRAWER_WIDTH = 280


class MainWindow(QMainWindow):
    def __init__(self, service: MapperService, tray_icon: QIcon) -> None:
        super().__init__()
        self._service = service
        self._snapshot: Optional[UiSnapshot] = None
        self._selected_control = ""
        self._live_control = ""
        self._control_to_row: Dict[str, int] = {}
        self._updating_ui = False
        self._allow_close = False
        self._current_language = ""
        self._current_theme = ""
        self._mapping_rows_signature: Tuple[Tuple[object, ...], ...] = ()
        self._rendered_selected_control = ""
        self._force_editor_refresh_control = ""
        self._landing_mode = True
        self._editor_opened = False
        self._line_edit_commit_guards = {
            "mapping_shortcut": False,
            "mapping_label": False,
        }
        self._drawer_open = True

        self._inspector_dialog = InspectorDialog(service, self)
        self._preset_manager_dialog = PresetManagerDialog(service, self)
        self._profile_settings_dialog = ProfileSettingsDialog(service, self)
        self._settings_dialog = SettingsDialog(service, self)

        self.setWindowTitle(APP_PRODUCT_NAME)
        self.setWindowIcon(tray_icon)
        self.resize(1500, 940)

        self._build_ui()
        self._retranslate()

    def begin_quit(self) -> None:
        self._allow_close = True

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close:
            super().closeEvent(event)
            return
        event.ignore()
        self.hide()

    def apply_snapshot(self, snapshot: UiSnapshot) -> None:
        self._snapshot = snapshot
        self._updating_ui = True
        try:
            self._landing_mode = self._should_show_landing(snapshot)
            self._live_control = snapshot.focused_control
            if snapshot.selected_language != self._current_language:
                self._current_language = snapshot.selected_language
                self._retranslate_all(snapshot)
            if snapshot.selected_theme != self._current_theme:
                self._current_theme = snapshot.selected_theme
                self._refresh_theme_widgets()
            self._update_toolbar(snapshot)
            self._empty_device_list.set_entries(
                snapshot.device_entries,
                connected_text=self._service.tr("connected"),
                disconnected_text=self._service.tr("disconnected"),
            )
            self._device_list.set_entries(
                snapshot.device_entries,
                connected_text=self._service.tr("connected"),
                disconnected_text=self._service.tr("disconnected"),
            )
            self._pages.setCurrentWidget(self._empty_page if self._landing_mode else self._connected_page)
            self._update_connected_workspace(snapshot)
            self._inspector_dialog.apply_snapshot(snapshot)
            self._preset_manager_dialog.apply_snapshot(snapshot)
            self._profile_settings_dialog.apply_snapshot(snapshot)
            self._settings_dialog.apply_snapshot(snapshot)
        finally:
            self._updating_ui = False

    def _retranslate_all(self, snapshot: Optional[UiSnapshot] = None) -> None:
        self._retranslate()
        self._inspector_dialog.retranslate_ui(self._current_language)
        self._preset_manager_dialog.retranslate_ui(self._current_language)
        self._profile_settings_dialog.retranslate_ui(self._current_language)
        self._settings_dialog.retranslate_ui(self._current_language)
        if snapshot is None:
            return
        connected_text = self._service.tr("connected")
        disconnected_text = self._service.tr("disconnected")
        self._empty_device_list.set_entries(
            snapshot.device_entries,
            connected_text=connected_text,
            disconnected_text=disconnected_text,
        )
        self._device_list.set_entries(
            snapshot.device_entries,
            connected_text=connected_text,
            disconnected_text=disconnected_text,
        )

    def _refresh_theme_widgets(self) -> None:
        self._controller_diagram.update()
        if hasattr(self, "_empty_device_list"):
            self._empty_device_list.viewport().update()
        if hasattr(self, "_device_list"):
            self._device_list.viewport().update()

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(16)
        outer.addWidget(self._build_toolbar(), 0)

        self._pages = QStackedWidget(root)
        self._empty_page = self._build_empty_page()
        self._connected_page = self._build_connected_page()
        self._pages.addWidget(self._empty_page)
        self._pages.addWidget(self._connected_page)
        outer.addWidget(self._pages, 1)

    def _build_toolbar(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("ToolbarCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        self._drawer_toggle_button = QPushButton(card)
        self._drawer_toggle_button.clicked.connect(self._toggle_device_drawer)
        self._toolbar_hint = QLabel(card)
        self._toolbar_hint.setObjectName("ToolbarHint")
        self._toolbar_hint.setWordWrap(True)

        self._inspector_button = QPushButton(card)
        self._inspector_button.clicked.connect(self._show_inspector)
        self._settings_button = QPushButton(card)
        self._settings_button.clicked.connect(self._show_settings)

        layout.addWidget(self._drawer_toggle_button)
        layout.addWidget(self._toolbar_hint, 1)
        layout.addWidget(self._inspector_button)
        layout.addWidget(self._settings_button)
        return card

    def _build_empty_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        card = QFrame(page)
        card.setObjectName("EmptyStateCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(18)

        self._empty_title = QLabel(card)
        self._empty_title.setObjectName("PageTitle")
        self._empty_body = QLabel(card)
        self._empty_body.setObjectName("MutedText")
        self._empty_body.setWordWrap(True)
        self._empty_devices_title = QLabel(card)
        self._empty_devices_title.setObjectName("SectionTitle")
        self._empty_device_list = DeviceListWidget(card)
        self._empty_device_list.device_selected.connect(self._on_device_selected)
        self._empty_device_list.setMinimumHeight(420)

        card_layout.addWidget(self._empty_title)
        card_layout.addWidget(self._empty_body)
        card_layout.addSpacing(8)
        card_layout.addWidget(self._empty_devices_title)
        card_layout.addWidget(self._empty_device_list, 1)

        layout.addWidget(card, 1)
        return page

    def _build_connected_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        body = QHBoxLayout()
        body.setSpacing(16)
        self._device_drawer = QFrame(page)
        self._device_drawer.setMaximumWidth(DEVICE_DRAWER_WIDTH)
        self._device_drawer.setMinimumWidth(0)
        self._device_drawer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        drawer_layout = QVBoxLayout(self._device_drawer)
        drawer_layout.setContentsMargins(0, 0, 0, 0)
        drawer_layout.addWidget(self._build_device_panel(), 1)
        body.addWidget(self._device_drawer, 0)

        workspace = QVBoxLayout()
        workspace.setSpacing(16)
        workspace.addWidget(self._build_workspace_header(), 0)

        center = QHBoxLayout()
        center.setSpacing(16)
        center.addWidget(self._build_diagram_panel(), 4)
        center.addWidget(self._build_mapping_panel(), 8)
        workspace.addLayout(center, 1)

        body.addLayout(workspace, 1)
        layout.addLayout(body, 1)
        self._device_drawer_animation = QPropertyAnimation(self._device_drawer, b"maximumWidth", self)
        self._device_drawer_animation.setDuration(180)
        self._device_drawer_animation.setEasingCurve(QEasingCurve.InOutCubic)
        return page

    def _build_device_panel(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("PanelCard")
        card.setFixedWidth(280)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self._devices_title = QLabel(card)
        self._devices_title.setObjectName("SectionTitle")
        self._devices_hint = QLabel(card)
        self._devices_hint.setObjectName("MutedText")
        self._devices_hint.setWordWrap(True)
        self._device_list = DeviceListWidget(card)
        self._device_list.device_selected.connect(self._on_device_selected)

        layout.addWidget(self._devices_title)
        layout.addWidget(self._devices_hint)
        layout.addWidget(self._device_list, 1)
        return card

    def _build_workspace_header(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("WorkspaceHeaderCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        self._device_name_chip = QFrame(card)
        self._device_name_chip.setObjectName("DeviceNameChip")
        chip_layout = QHBoxLayout(self._device_name_chip)
        chip_layout.setContentsMargins(10, 4, 10, 4)
        chip_layout.setSpacing(0)
        self._device_name = QLabel(self._device_name_chip)
        self._device_name.setObjectName("HeaderTitle")
        chip_layout.addWidget(self._device_name)
        self._device_status = QLabel(card)
        self._device_status.setObjectName("ConnectedPill")
        self._header_profile_button = QPushButton(card)
        self._header_profile_button.clicked.connect(self._show_profile_settings)

        layout.addWidget(self._device_name_chip, 0)
        layout.addWidget(self._device_status, 0)
        layout.addStretch(1)
        layout.addWidget(self._header_profile_button, 0)
        card.setMinimumHeight(56)
        return card

    def _build_diagram_panel(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("PanelCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self._controller_title = QLabel(card)
        self._controller_title.setObjectName("SectionTitle")
        self._diagram_note = QLabel(card)
        self._diagram_note.setObjectName("MutedText")
        self._diagram_note.setWordWrap(True)
        self._controller_subtitle = QLabel(card)
        self._controller_subtitle.setObjectName("MutedText")
        self._controller_subtitle.setWordWrap(True)

        self._controller_diagram = ControllerDiagramWidget(card)
        self._controller_diagram.control_selected.connect(self._on_diagram_control_selected)

        layout.addWidget(self._controller_title)
        layout.addWidget(self._diagram_note)
        layout.addWidget(self._controller_subtitle)
        layout.addWidget(self._controller_diagram, 1)
        return card

    def _build_mapping_panel(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("PanelCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._mappings_title = QLabel(card)
        self._mappings_title.setObjectName("SectionTitle")
        self._mapping_hint = QLabel(card)
        self._mapping_hint.setObjectName("MutedText")
        self._mapping_hint.setWordWrap(True)

        self._mapping_table = QTableWidget(0, 3, card)
        self._mapping_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._mapping_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._mapping_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._mapping_table.verticalHeader().setVisible(False)
        self._mapping_table.setAlternatingRowColors(True)
        self._mapping_table.itemSelectionChanged.connect(self._on_mapping_selection_changed)
        self._mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._mapping_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        preset_card = self._build_preset_strip()

        editor_card = QFrame(card)
        editor_card.setObjectName("MappingEditorCard")
        editor_layout = QGridLayout(editor_card)
        editor_layout.setContentsMargins(16, 16, 16, 16)
        editor_layout.setHorizontalSpacing(10)
        editor_layout.setVerticalSpacing(10)

        self._edit_title = QLabel(editor_card)
        self._edit_title.setObjectName("SectionTitle")
        self._selected_button_value = QLabel(editor_card)
        self._selected_button_value.setObjectName("StrongText")
        self._editor_note = QLabel(editor_card)
        self._editor_note.setObjectName("MutedText")
        self._editor_note.setWordWrap(True)
        self._edit_type_label = QLabel(editor_card)
        self._edit_type_combo = StableComboBox(editor_card)
        initial_mapping_type_items = self._mapping_type_items()
        self._edit_type_combo.sync_items(initial_mapping_type_items, EDITOR_MAPPING_TYPE_SHORTCUT)
        self._edit_type_combo.currentIndexChanged.connect(self._on_mapping_type_changed)
        self._edit_value_label = QLabel(editor_card)
        self._edit_shortcut = ShortcutEdit(editor_card)
        self._edit_special = StableComboBox(editor_card)
        initial_special_items = self._special_key_items()
        self._edit_special.sync_items(initial_special_items, initial_special_items[0][1] if initial_special_items else None)
        self._edit_special.currentIndexChanged.connect(self._on_mapping_picker_changed)
        self._edit_mouse = StableComboBox(editor_card)
        initial_mouse_items = self._mouse_action_items()
        self._edit_mouse.sync_items(initial_mouse_items, initial_mouse_items[0][1] if initial_mouse_items else None)
        self._edit_mouse.currentIndexChanged.connect(self._on_mapping_picker_changed)
        self._edit_value_stack = QStackedWidget(editor_card)
        self._edit_value_stack.addWidget(self._edit_shortcut)
        self._edit_value_stack.addWidget(self._edit_special)
        self._edit_value_stack.addWidget(self._edit_mouse)
        self._edit_label_label = QLabel(editor_card)
        self._edit_label = QLineEdit(editor_card)
        self._save_mapping_button = QPushButton(editor_card)
        self._save_mapping_button.setObjectName("PrimaryButton")
        self._save_mapping_button.clicked.connect(self._on_save_mapping)
        self._cancel_mapping_button = QPushButton(editor_card)
        self._cancel_mapping_button.clicked.connect(self._on_cancel_mapping)
        self._reset_mapping_button = QPushButton(editor_card)
        self._reset_mapping_button.clicked.connect(self._on_reset_mapping)
        for button in (self._save_mapping_button, self._cancel_mapping_button, self._reset_mapping_button):
            button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        editor_layout.addWidget(self._edit_title, 0, 0, 1, 2)
        editor_layout.addWidget(self._selected_button_value, 1, 0, 1, 2)
        editor_layout.addWidget(self._editor_note, 2, 0, 1, 2)
        editor_layout.addWidget(self._edit_type_label, 3, 0)
        editor_layout.addWidget(self._edit_type_combo, 3, 1)
        editor_layout.addWidget(self._edit_value_label, 4, 0)
        editor_layout.addWidget(self._edit_value_stack, 4, 1)
        editor_layout.addWidget(self._edit_label_label, 5, 0)
        editor_layout.addWidget(self._edit_label, 5, 1)
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addStretch(1)
        action_row.addWidget(self._save_mapping_button)
        action_row.addWidget(self._cancel_mapping_button)
        action_row.addWidget(self._reset_mapping_button)
        editor_layout.addLayout(action_row, 6, 0, 1, 2)

        layout.addWidget(self._mappings_title)
        layout.addWidget(self._mapping_hint)
        layout.addWidget(preset_card)
        layout.addWidget(self._mapping_table, 1)
        layout.addWidget(editor_card)
        return card

    def _build_preset_strip(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("PresetStrip")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        self._preset_title = QLabel(card)
        self._preset_title.setObjectName("SectionTitle")
        self._previous_preset_button = QPushButton(card)
        self._previous_preset_button.clicked.connect(self._on_previous_preset)
        self._current_preset_label = QLabel(card)
        self._current_preset_label.setObjectName("MutedText")
        self._preset_name_edit = QLineEdit(card)
        self._preset_name_edit.editingFinished.connect(self._on_preset_renamed)
        self._next_preset_button = QPushButton(card)
        self._next_preset_button.clicked.connect(self._on_next_preset)
        self._add_preset_button = QPushButton(card)
        self._add_preset_button.clicked.connect(self._on_add_preset)
        self._delete_preset_button = QPushButton(card)
        self._delete_preset_button.setObjectName("DangerButton")
        self._delete_preset_button.clicked.connect(self._on_delete_preset)

        layout.addWidget(self._preset_title)
        layout.addWidget(self._previous_preset_button)
        layout.addWidget(self._current_preset_label)
        layout.addWidget(self._preset_name_edit, 1)
        layout.addWidget(self._next_preset_button)
        layout.addWidget(self._add_preset_button)
        layout.addWidget(self._delete_preset_button)
        return card

    def _mapping_type_items(self) -> Tuple[Tuple[str, str], ...]:
        return (
            (self._service.tr("mapping_type_shortcut"), EDITOR_MAPPING_TYPE_SHORTCUT),
            (self._service.tr("mapping_type_special"), EDITOR_MAPPING_TYPE_SPECIAL),
            (self._service.tr("mapping_type_mouse"), EDITOR_MAPPING_TYPE_MOUSE),
        )

    def _special_key_items(self) -> Tuple[Tuple[str, str], ...]:
        items = []
        for group_key, entries in SPECIAL_KEY_GROUPS:
            group_label = self._service.tr(group_key)
            for item_key, shortcut_text in entries:
                items.append((f"{group_label} - {self._service.tr(item_key)}", normalize_shortcut_text(shortcut_text)))
        return tuple(items)

    def _mouse_action_items(self) -> Tuple[Tuple[str, str], ...]:
        return tuple((self._service.tr(label_key), action_kind) for label_key, action_kind in MOUSE_ACTION_DEFINITIONS)

    def _retranslate(self) -> None:
        self.setWindowTitle(APP_PRODUCT_NAME)
        self._drawer_toggle_button.setText(
            self._service.tr("hide_devices") if self._drawer_open else self._service.tr("show_devices")
        )
        self._toolbar_hint.setText(
            self._service.tr("toolbar.landing_hint") if self._landing_mode else self._service.tr("toolbar_hint")
        )
        self._inspector_button.setText(self._service.tr("inspector"))
        self._settings_button.setText(self._service.tr("settings"))

        self._empty_title.setText(self._service.tr("empty_title"))
        self._empty_body.setText(self._service.tr("empty_body"))
        self._empty_devices_title.setText(self._service.tr("remembered_devices"))
        self._devices_title.setText(self._service.tr("remembered_devices"))
        self._devices_hint.setText(self._service.tr("empty_body"))

        self._controller_title.setText(self._service.tr("controller"))
        self._mappings_title.setText(self._service.tr("button_mappings"))
        self._mapping_hint.setText(self._service.tr("mapping_hint"))
        self._mapping_table.setHorizontalHeaderLabels(
            [
                self._service.tr("button"),
                self._service.tr("assigned_action"),
                self._service.tr("label"),
            ]
        )
        self._edit_title.setText(self._service.tr("mapping_editor"))
        self._edit_type_label.setText("{label}:".format(label=self._service.tr("mapping_type")))
        self._edit_value_label.setText("{label}:".format(label=self._service.tr("mapping_value")))
        self._edit_label_label.setText("{label}:".format(label=self._service.tr("label")))
        self._save_mapping_button.setText(self._service.tr("save"))
        self._cancel_mapping_button.setText(self._service.tr("cancel"))
        self._reset_mapping_button.setText(self._service.tr("reset"))
        self._preset_title.setText(self._service.tr("preset"))
        self._current_preset_label.setText("{label}:".format(label=self._service.tr("preset_name")))
        self._previous_preset_button.setText(self._service.tr("previous"))
        self._next_preset_button.setText(self._service.tr("next"))
        self._add_preset_button.setText(self._service.tr("add"))
        self._delete_preset_button.setText(self._service.tr("delete"))
        self._header_profile_button.setText(self._service.tr("profile_settings"))
        self._edit_type_combo.sync_items(self._mapping_type_items(), self._edit_type_combo.currentData())
        self._edit_special.sync_items(self._special_key_items(), self._edit_special.currentData())
        self._edit_mouse.sync_items(self._mouse_action_items(), self._edit_mouse.currentData())

    def _update_toolbar(self, snapshot: UiSnapshot) -> None:
        selected_device = snapshot.selected_device_profile
        self._toolbar_hint.setText(
            self._service.tr("toolbar.landing_hint") if self._landing_mode else self._service.tr("toolbar_hint")
        )
        if self._landing_mode:
            self._drawer_toggle_button.setEnabled(False)
            self._inspector_button.setEnabled(False)
            self._settings_button.setEnabled(True)
            return
        if selected_device is None:
            for widget in (
                self._drawer_toggle_button,
                self._inspector_button,
            ):
                widget.setEnabled(False)
            self._settings_button.setEnabled(True)
            return

        self._drawer_toggle_button.setEnabled(True)
        self._inspector_button.setEnabled(True)
        self._settings_button.setEnabled(True)

    def _update_connected_workspace(self, snapshot: UiSnapshot) -> None:
        selected_device = snapshot.selected_device_profile
        selected_app_profile = snapshot.selected_app_profile
        selected_preset = snapshot.selected_preset
        normalized_state = snapshot.normalized_state

        if selected_device is None:
            self._device_name.setText(self._service.tr("no_device"))
            self._device_status.setText(self._service.tr("disconnected"))
            self._controller_subtitle.setText("")
            self._controller_diagram.set_presentation(
                "unknown",
                {},
                (),
                False,
                self._service.tr("unknown_diagram_title"),
                self._service.tr("unknown_diagram_body"),
            )
            self._controller_diagram.set_active_controls(set())
            self._controller_diagram.set_selected_control("")
            self._controller_diagram.set_live_control("")
            self._update_mapping_table(())
            self._set_editor_empty()
            return

        is_connected = selected_device.device_id in {entry.device_id for entry in snapshot.device_entries if entry.is_connected}
        self._device_name.setText(selected_device.display_name)
        self._device_status.setText(self._service.tr("connected") if is_connected else self._service.tr("disconnected"))
        status_object_name = "ConnectedPill" if is_connected else "DisconnectedPill"
        if self._device_status.objectName() != status_object_name:
            self._device_status.setObjectName(status_object_name)
            self._device_status.style().unpolish(self._device_status)
            self._device_status.style().polish(self._device_status)

        if normalized_state is not None:
            if normalized_state.has_exact_diagram:
                note_key = {
                    "zero2": "zero2_exact",
                    "xbox": "xbox_exact",
                }.get(normalized_state.diagram_kind, "generic_layout")
                placeholder_title = ""
                placeholder_body = ""
            elif normalized_state.has_canonical_mapping:
                note_key = "unknown_layout_supported"
                placeholder_title = self._service.tr("unknown_diagram_title")
                placeholder_body = self._service.tr("unknown_diagram_body")
            else:
                note_key = "unknown_layout_unavailable"
                placeholder_title = self._service.tr("unmapped_diagram_title")
                placeholder_body = self._service.tr("unmapped_diagram_body")
            self._diagram_note.setText(self._service.tr(note_key))
            self._controller_subtitle.setText(normalized_state.device_title)
            active_controls = {
                control
                for control, control_state in normalized_state.controls.items()
                if control_state.is_active
            }
            self._controller_diagram.set_presentation(
                normalized_state.diagram_kind,
                normalized_state.control_labels,
                normalized_state.visible_controls,
                normalized_state.has_exact_diagram,
                placeholder_title,
                placeholder_body,
            )
            self._controller_diagram.set_active_controls(active_controls)
        else:
            resolved_family = self._service.normalizer.describe_saved_device(selected_device)
            template = resolved_family.template
            if template.family_id == "unknown_controller":
                note_key = "unknown_layout_unavailable"
                presentation_kind = "unknown"
                control_labels = {}
                visible_controls = ()
                has_exact_diagram = False
                placeholder_title = self._service.tr("unmapped_diagram_title")
                placeholder_body = self._service.tr("unmapped_diagram_body")
            else:
                note_key = {
                    "zero2": "zero2_exact",
                    "xbox": "xbox_exact",
                }.get(template.diagram_kind, "generic_layout")
                presentation_kind = template.diagram_kind
                control_labels = dict(template.control_labels)
                visible_controls = template.visible_controls
                has_exact_diagram = template.has_exact_diagram
                placeholder_title = ""
                placeholder_body = ""
            self._diagram_note.setText(self._service.tr(note_key))
            self._controller_subtitle.setText(selected_device.last_seen_name or selected_device.display_name)
            self._controller_diagram.set_presentation(
                presentation_kind,
                control_labels,
                visible_controls,
                has_exact_diagram,
                placeholder_title,
                placeholder_body,
            )
            self._controller_diagram.set_active_controls(set())

        self._controller_diagram.set_selected_control(self._selected_control)
        self._controller_diagram.set_live_control(self._live_control)
        self._update_mapping_table(snapshot.mapping_rows)
        self._header_profile_button.setEnabled(selected_device is not None)
        preset_count = len(selected_app_profile.presets) if selected_app_profile is not None else 0
        has_preset = selected_app_profile is not None and selected_preset is not None
        self._previous_preset_button.setEnabled(has_preset)
        self._next_preset_button.setEnabled(has_preset)
        self._add_preset_button.setEnabled(selected_app_profile is not None and preset_count < 5)
        self._delete_preset_button.setEnabled(selected_app_profile is not None and preset_count > 1)
        self._preset_name_edit.setEnabled(has_preset)
        self._sync_line_edit(self._preset_name_edit, selected_preset.name if selected_preset is not None else "", "preset_name")

    def _update_mapping_table(self, rows) -> None:
        row_list = list(rows)
        row_signature = tuple(
            (
                row.control,
                row.button_name,
                row.shortcut,
                row.label,
                row.action_kind,
                row.action_text,
                row.is_system_action,
                row.system_text,
            )
            for row in row_list
        )
        rows_changed = row_signature != self._mapping_rows_signature
        selection_changed = self._selected_control != self._rendered_selected_control
        force_editor_refresh = selection_changed or self._force_editor_refresh_control == self._selected_control
        if not rows_changed and not selection_changed:
            if not force_editor_refresh:
                return

        if rows_changed:
            self._mapping_table.setRowCount(len(row_list))
            self._control_to_row = {}
            row_to_select = -1

            was_blocked = self._mapping_table.blockSignals(True)
            try:
                for row_index, row in enumerate(row_list):
                    self._control_to_row[row.control] = row_index
                    display_action = (
                        row.system_text
                        if row.is_system_action
                        else (row.action_text or format_shortcut_text(row.shortcut) or "-")
                    )
                    display_label = row.label or "-"
                    values = (row.button_name, display_action, display_label)
                    for column_index, value in enumerate(values):
                        item = self._mapping_table.item(row_index, column_index)
                        if item is None:
                            item = QTableWidgetItem()
                            self._mapping_table.setItem(row_index, column_index, item)
                        item.setText(value)
                        item.setData(Qt.UserRole, row.control)
                    if row.control == self._selected_control:
                        row_to_select = row_index

                if row_list and row_to_select < 0 and not self._mapping_editor_is_active():
                    row_to_select = 0
                if row_to_select >= 0:
                    self._mapping_table.selectRow(row_to_select)
                    self._selected_control = row_list[row_to_select].control
                else:
                    self._mapping_table.clearSelection()
                    self._selected_control = ""
            finally:
                self._mapping_table.blockSignals(was_blocked)
        else:
            row_to_select = self._control_to_row.get(self._selected_control, -1)
            if row_to_select < 0 and row_list and not self._mapping_editor_is_active():
                row_to_select = 0
            was_blocked = self._mapping_table.blockSignals(True)
            try:
                if row_to_select >= 0:
                    self._mapping_table.selectRow(row_to_select)
                    self._selected_control = row_list[row_to_select].control
                else:
                    self._mapping_table.clearSelection()
                    self._selected_control = ""
            finally:
                self._mapping_table.blockSignals(was_blocked)

        self._mapping_rows_signature = row_signature
        self._rendered_selected_control = self._selected_control
        if force_editor_refresh:
            self._force_editor_refresh_control = ""

        self._controller_diagram.set_selected_control(self._selected_control)
        self._refresh_mapping_editor(row_list, force=force_editor_refresh)

    def _refresh_mapping_editor(self, rows, force: bool = False) -> None:
        selected_row = next((row for row in rows if row.control == self._selected_control), None)
        if selected_row is None:
            self._set_editor_empty()
            return

        self._selected_button_value.setText(
            "{label}: {value}".format(
                label=self._service.tr("selected_button"),
                value=selected_row.button_name,
            )
        )
        if not force and self._mapping_editor_has_unsaved_changes(selected_row):
            return
        self._load_mapping_editor_from_row(selected_row, force=force)

        if selected_row.is_system_action:
            self._editor_note.setText(
                "{title}: {detail}".format(
                    title=self._service.tr("system_action"),
                    detail=selected_row.system_text,
                )
            )
            self._edit_type_combo.setEnabled(False)
            self._edit_shortcut.setEnabled(False)
            self._edit_special.setEnabled(False)
            self._edit_mouse.setEnabled(False)
            self._edit_label.setEnabled(False)
            self._save_mapping_button.setEnabled(False)
            self._cancel_mapping_button.setEnabled(False)
            self._reset_mapping_button.setEnabled(False)
        else:
            self._editor_note.setText(self._service.tr("mapping_hint"))
            self._edit_type_combo.setEnabled(True)
            self._edit_shortcut.setEnabled(True)
            self._edit_special.setEnabled(True)
            self._edit_mouse.setEnabled(True)
            self._edit_label.setEnabled(True)
            self._save_mapping_button.setEnabled(True)
            self._cancel_mapping_button.setEnabled(True)
            self._reset_mapping_button.setEnabled(True)
        self._edit_shortcut.setPlaceholderText(self._service.tr("mapping.shortcut_placeholder"))
        self._edit_label.setPlaceholderText("")

    def _set_editor_empty(self) -> None:
        self._selected_button_value.setText(self._service.tr("no_selection"))
        self._editor_note.setText(self._service.tr("system_mapping_note"))
        self._set_combo_data(self._edit_type_combo, EDITOR_MAPPING_TYPE_SHORTCUT)
        self._set_line_edit_text(self._edit_shortcut, "")
        special_items = self._special_key_items()
        mouse_items = self._mouse_action_items()
        self._set_combo_data(self._edit_special, special_items[0][1] if special_items else None)
        self._set_combo_data(self._edit_mouse, mouse_items[0][1] if mouse_items else None)
        self._set_line_edit_text(self._edit_label, "")
        self._edit_type_combo.setEnabled(False)
        self._edit_shortcut.setEnabled(False)
        self._edit_special.setEnabled(False)
        self._edit_mouse.setEnabled(False)
        self._edit_label.setEnabled(False)
        self._save_mapping_button.setEnabled(False)
        self._cancel_mapping_button.setEnabled(False)
        self._reset_mapping_button.setEnabled(False)
        self._update_editor_value_stack()

    def _load_mapping_editor_from_row(self, row: MappingRow, force: bool = False) -> None:
        editor_type = self._editor_type_for_row(row)
        self._set_combo_data(self._edit_type_combo, editor_type)
        self._update_editor_value_stack()
        if force:
            self._set_line_edit_text(self._edit_shortcut, row.shortcut)
        else:
            self._sync_line_edit(self._edit_shortcut, row.shortcut, "mapping_shortcut")
        if row.shortcut:
            self._set_combo_data(self._edit_special, normalize_shortcut_text(row.shortcut))
        self._set_combo_data(self._edit_mouse, row.action_kind)
        if force:
            self._set_line_edit_text(self._edit_label, row.label)
        else:
            self._sync_line_edit(self._edit_label, row.label, "mapping_label")

    def _editor_type_for_row(self, row: MappingRow) -> str:
        if row.action_kind != MAPPING_ACTION_KEYBOARD:
            return EDITOR_MAPPING_TYPE_MOUSE
        normalized_shortcut = normalize_shortcut_text(row.shortcut)
        if normalized_shortcut in get_special_shortcut_preset_values():
            return EDITOR_MAPPING_TYPE_SPECIAL
        return EDITOR_MAPPING_TYPE_SHORTCUT

    def _set_combo_data(self, combo: StableComboBox, value: object) -> None:
        target_index = combo.findData(value)
        if target_index < 0:
            if combo.count() == 0:
                return
            target_index = 0
        if combo.currentIndex() == target_index:
            return
        was_blocked = combo.blockSignals(True)
        try:
            combo.setCurrentIndex(target_index)
        finally:
            combo.blockSignals(was_blocked)

    def _update_editor_value_stack(self) -> None:
        current_type = self._edit_type_combo.currentData()
        if current_type == EDITOR_MAPPING_TYPE_SPECIAL:
            self._edit_value_stack.setCurrentWidget(self._edit_special)
        elif current_type == EDITOR_MAPPING_TYPE_MOUSE:
            self._edit_value_stack.setCurrentWidget(self._edit_mouse)
        else:
            self._edit_value_stack.setCurrentWidget(self._edit_shortcut)

    def _mapping_editor_has_unsaved_changes(self, selected_row: Optional[MappingRow] = None) -> bool:
        row = selected_row or self._selected_mapping_row()
        if row is None:
            return False
        expected_type = self._editor_type_for_row(row)
        current_type = str(self._edit_type_combo.currentData() or EDITOR_MAPPING_TYPE_SHORTCUT)
        if current_type != expected_type:
            return True

        current_shortcut, current_action_kind = self._current_editor_mapping_value()
        expected_shortcut = normalize_shortcut_text(row.shortcut)
        if normalize_shortcut_text(current_shortcut) != expected_shortcut:
            return True
        if current_action_kind != row.action_kind:
            return True
        return self._edit_label.text().strip() != row.label.strip()

    def _selected_mapping_row(self) -> Optional[MappingRow]:
        if self._snapshot is None:
            return None
        return next((row for row in self._snapshot.mapping_rows if row.control == self._selected_control), None)

    def _current_editor_mapping_value(self) -> Tuple[str, str]:
        editor_type = str(self._edit_type_combo.currentData() or EDITOR_MAPPING_TYPE_SHORTCUT)
        if editor_type == EDITOR_MAPPING_TYPE_SPECIAL:
            return normalize_shortcut_text(str(self._edit_special.currentData() or "")), MAPPING_ACTION_KEYBOARD
        if editor_type == EDITOR_MAPPING_TYPE_MOUSE:
            return "", str(self._edit_mouse.currentData() or MAPPING_ACTION_MOUSE_LEFT_CLICK)
        return normalize_shortcut_text(self._edit_shortcut.text()), MAPPING_ACTION_KEYBOARD

    def _sync_line_edit(self, line_edit: QLineEdit, value: str, guard_key: str) -> None:
        if line_edit.text() == value:
            if line_edit.isModified():
                was_blocked = line_edit.blockSignals(True)
                try:
                    line_edit.setModified(False)
                finally:
                    line_edit.blockSignals(was_blocked)
            return

        if not self._line_edit_commit_guards.get(guard_key, False) and (
            line_edit.hasFocus() or line_edit.isModified()
        ):
            return

        self._set_line_edit_text(line_edit, value)

    def _set_line_edit_text(self, line_edit: QLineEdit, value: str) -> None:
        was_blocked = line_edit.blockSignals(True)
        try:
            line_edit.setText(value)
            line_edit.setModified(False)
        finally:
            line_edit.blockSignals(was_blocked)

    def _run_with_commit_guard(self, keys: Tuple[str, ...], action) -> None:
        for key in keys:
            self._line_edit_commit_guards[key] = True
        try:
            action()
        finally:
            for key in keys:
                self._line_edit_commit_guards[key] = False

    def _mapping_editor_is_active(self) -> bool:
        has_focus_or_commit = any(
            line_edit.hasFocus() or line_edit.isModified() or self._line_edit_commit_guards.get(guard_key, False)
            for line_edit, guard_key in (
                (self._edit_shortcut, "mapping_shortcut"),
                (self._edit_label, "mapping_label"),
            )
        )
        combo_active = any(
            combo.hasFocus() or combo.is_popup_open()
            for combo in (self._edit_type_combo, self._edit_special, self._edit_mouse)
        )
        return has_focus_or_commit or combo_active or self._edit_shortcut.is_popup_open() or self._mapping_editor_has_unsaved_changes()

    def _toggle_device_drawer(self) -> None:
        self._set_device_drawer_open(not self._drawer_open, animated=True)

    def _set_device_drawer_open(self, is_open: bool, animated: bool) -> None:
        self._drawer_open = is_open
        if hasattr(self, "_drawer_toggle_button"):
            self._drawer_toggle_button.setText(
                self._service.tr("hide_devices") if self._drawer_open else self._service.tr("show_devices")
            )
        if not hasattr(self, "_device_drawer"):
            return

        target_width = DEVICE_DRAWER_WIDTH if is_open else 0
        if animated and hasattr(self, "_device_drawer_animation"):
            self._device_drawer_animation.stop()
            self._device_drawer_animation.setStartValue(self._device_drawer.maximumWidth())
            self._device_drawer_animation.setEndValue(target_width)
            self._device_drawer_animation.start()
        else:
            self._device_drawer.setMaximumWidth(target_width)

    def _selected_device_id(self) -> str:
        if self._snapshot is None:
            return ""
        return self._snapshot.selected_device_id

    def _should_show_landing(self, snapshot: UiSnapshot) -> bool:
        if not self._editor_opened:
            return True
        return snapshot.selected_device_profile is None

    def _on_device_selected(self, device_id: str) -> None:
        if self._updating_ui:
            return
        self._editor_opened = True
        self._service.select_device(device_id)

    def _on_app_profile_changed(self) -> None:
        if self._updating_ui:
            return
        device_id = self._selected_device_id()
        app_profile_id = self._app_combo.currentData()
        if device_id and app_profile_id is not None:
            self._service.select_app_profile(device_id, str(app_profile_id))

    def _on_add_app_profile(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.add_app_profile(device_id)

    def _on_delete_app_profile(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.delete_selected_app_profile(device_id)

    def _on_app_profile_metadata_changed(self) -> None:
        if self._updating_ui:
            return
        device_id = self._selected_device_id()
        if device_id:
            self._run_with_commit_guard(
                ("profile_name", "process_name"),
                lambda: self._service.update_selected_app_profile(
                    device_id,
                    self._profile_name_edit.text(),
                    self._process_name_edit.text(),
                ),
            )

    def _on_toolbar_preset_selected(self) -> None:
        if self._updating_ui:
            return
        device_id = self._selected_device_id()
        preset_index = int(self._toolbar_preset_combo.currentData() or 0)
        if device_id:
            self._service.select_preset(device_id, preset_index)

    def _on_previous_preset(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.previous_selected_preset(device_id)

    def _on_next_preset(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.next_selected_preset(device_id)

    def _on_add_preset(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.add_preset(device_id)

    def _on_delete_preset(self) -> None:
        device_id = self._selected_device_id()
        if device_id:
            self._service.delete_selected_preset(device_id)

    def _on_preset_renamed(self) -> None:
        if self._updating_ui:
            return
        device_id = self._selected_device_id()
        if device_id:
            self._run_with_commit_guard(
                ("preset_name",),
                lambda: self._service.rename_selected_preset(device_id, self._preset_name_edit.text()),
            )

    def _on_mapping_selection_changed(self) -> None:
        if self._updating_ui:
            return
        items = self._mapping_table.selectedItems()
        if not items:
            return
        self._selected_control = str(items[0].data(Qt.UserRole))
        self._rendered_selected_control = self._selected_control
        self._controller_diagram.set_selected_control(self._selected_control)
        if self._snapshot is not None:
            self._refresh_mapping_editor(self._snapshot.mapping_rows, force=True)

    def _on_diagram_control_selected(self, control: str) -> None:
        row_index = self._control_to_row.get(control)
        if row_index is None:
            return
        self._mapping_table.selectRow(row_index)
        self._mapping_table.scrollToItem(self._mapping_table.item(row_index, 0))

    def _on_mapping_type_changed(self) -> None:
        self._update_editor_value_stack()

    def _on_mapping_picker_changed(self) -> None:
        if self._updating_ui:
            return

    def _on_save_mapping(self) -> None:
        device_id = self._selected_device_id()
        if not device_id or not self._selected_control:
            return
        shortcut, action_kind = self._current_editor_mapping_value()
        self._run_with_commit_guard(
            ("mapping_shortcut", "mapping_label"),
            lambda: self._service.update_mapping(
                device_id=device_id,
                control=self._selected_control,
                shortcut=shortcut,
                label=self._edit_label.text(),
                action_kind=action_kind,
            ),
        )

    def _on_cancel_mapping(self) -> None:
        if self._snapshot is None:
            return
        self._refresh_mapping_editor(self._snapshot.mapping_rows, force=True)

    def _on_reset_mapping(self) -> None:
        device_id = self._selected_device_id()
        if not device_id or not self._selected_control:
            return
        self._force_editor_refresh_control = self._selected_control
        self._service.reset_mapping_to_default(device_id, self._selected_control)

    def _show_inspector(self) -> None:
        self._inspector_dialog.show()
        self._inspector_dialog.raise_()
        self._inspector_dialog.activateWindow()

    def _show_preset_manager(self) -> None:
        self._preset_manager_dialog.show()
        self._preset_manager_dialog.raise_()
        self._preset_manager_dialog.activateWindow()

    def _show_profile_settings(self) -> None:
        self._profile_settings_dialog.show()
        self._profile_settings_dialog.raise_()
        self._profile_settings_dialog.activateWindow()

    def _show_settings(self) -> None:
        self._settings_dialog.show()
        self._settings_dialog.raise_()
        self._settings_dialog.activateWindow()
