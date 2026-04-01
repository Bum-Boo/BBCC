from __future__ import annotations

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QSystemTrayIcon

from .backend.pygame_backend import PygameJoystickBackend
from .identity import APP_PRODUCT_NAME
from .gui.main_window import MainWindow
from .gui.widgets.toast import ToastWidget
from .services.app_monitor import ForegroundAppMonitor
from .services.autostart import WindowsAutoStartService
from .services.device_registry import DeviceRegistry
from .services.icon_factory import build_app_icon
from .services.keyboard_output import KeyboardShortcutSender
from .services.mapper_service import MapperService
from .services.normalization import InputNormalizer
from .services.settings_store import SettingsStore
from .services.typography import (
    DEFAULT_BASE_FONT_SIZE_PT,
    build_application_font,
    build_font_family_stack,
    load_application_fonts,
)
from .styles import build_stylesheet


class ControllerMapperApplication(QObject):
    def __init__(self, qt_app: QApplication, start_hidden: bool = False) -> None:
        super().__init__()
        self._qt_app = qt_app
        self._start_hidden = start_hidden
        self._is_quitting = False
        self._current_language = ""
        self._current_theme = ""
        load_application_fonts()

        icon = build_app_icon()
        self._qt_app.setWindowIcon(icon)
        device_registry = DeviceRegistry()

        self._service = MapperService(
            backend=PygameJoystickBackend(preferred_name_tokens=("8bitdo", "zero 2", "xbox")),
            normalizer=InputNormalizer(device_registry=device_registry),
            store=SettingsStore(),
            app_monitor=ForegroundAppMonitor(),
            output=KeyboardShortcutSender(),
            auto_start=WindowsAutoStartService(),
            device_registry=device_registry,
            poll_interval_ms=16,
        )

        initial_snapshot = self._service.current_snapshot()
        self._current_language = initial_snapshot.selected_language
        self._current_theme = initial_snapshot.selected_theme
        self._apply_appearance(self._current_language, self._current_theme)

        self._window = MainWindow(service=self._service, tray_icon=icon)
        self._toast = ToastWidget()
        self._tray = QSystemTrayIcon(icon, self._qt_app)
        self._configure_tray()

        self._service.toast_requested.connect(self._toast.show_message)
        self._service.snapshot_changed.connect(self._on_snapshot_changed)

    def start(self) -> None:
        self._service.start()
        self._tray.show()
        if not self._start_hidden:
            self._window.show()

    def _configure_tray(self) -> None:
        menu = QMenu()

        self._open_action = QAction(menu)
        self._open_action.triggered.connect(self._show_window)
        menu.addAction(self._open_action)

        self._hide_action = QAction(menu)
        self._hide_action.triggered.connect(self._window.hide)
        menu.addAction(self._hide_action)

        menu.addSeparator()

        self._quit_action = QAction(menu)
        self._quit_action.triggered.connect(self._quit)
        menu.addAction(self._quit_action)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._handle_tray_activation)
        self._retranslate_tray()

    def _on_snapshot_changed(self, snapshot) -> None:
        if (
            snapshot.selected_language != self._current_language
            or snapshot.selected_theme != self._current_theme
        ):
            self._current_language = snapshot.selected_language
            self._current_theme = snapshot.selected_theme
            self._apply_appearance(snapshot.selected_language, snapshot.selected_theme)
            self._retranslate_tray()
        self._window.apply_snapshot(snapshot)

    def _apply_appearance(self, language: str, theme: str) -> None:
        self._qt_app.setFont(build_application_font(language))
        self._qt_app.setProperty("theme_id", theme)
        self._qt_app.setStyleSheet(
            build_stylesheet(
                theme_id=theme,
                font_family_stack=build_font_family_stack(language),
                base_font_size_pt=DEFAULT_BASE_FONT_SIZE_PT,
            )
        )

    def _retranslate_tray(self) -> None:
        self._tray.setToolTip(APP_PRODUCT_NAME)
        self._open_action.setText(self._service.tr("tray.open"))
        self._hide_action.setText(self._service.tr("tray.hide"))
        self._quit_action.setText(self._service.tr("tray.quit"))

    def _handle_tray_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
        ):
            if self._window.isVisible():
                self._window.raise_()
                self._window.activateWindow()
            else:
                self._show_window()

    def _show_window(self) -> None:
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _quit(self) -> None:
        if self._is_quitting:
            return

        self._is_quitting = True
        self._window.begin_quit()
        self._service.stop()
        self._tray.hide()
        self._toast.hide()
        self._qt_app.quit()
