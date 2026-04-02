from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

if "pygame" not in sys.modules:
    pygame_stub = ModuleType("pygame")
    pygame_stub._sdl2 = ModuleType("pygame._sdl2")
    sys.modules["pygame"] = pygame_stub
    sys.modules["pygame._sdl2"] = pygame_stub._sdl2

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from zero2_input_inspector.domain.controls import (
    RIGHT_STICK_EFFECTIVE_DOWN,
    RIGHT_STICK_EFFECTIVE_LEFT,
    RIGHT_STICK_EFFECTIVE_RIGHT,
    RIGHT_STICK_EFFECTIVE_UP,
)
from zero2_input_inspector.gui.main_window import EDITOR_MAPPING_TYPE_STICK, MainWindow
from zero2_input_inspector.services.mapper_service import MapperService
from zero2_input_inspector.services.normalization import InputNormalizer
from zero2_input_inspector.services.settings_store import SettingsStore

from tests.test_xbox_media_fallback_load_path import (
    _DummyAutoStart,
    _DummyBackend,
    _DummyMonitor,
    _RecordingOutput,
    _legacy_xbox_payload,
)


class MainWindowMappingSelectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication(sys.argv)

    def _build_window(self) -> MainWindow:
        self._temp_dir = tempfile.TemporaryDirectory()
        config_dir = Path(self._temp_dir.name) / "zero2-input-inspector"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(
            __import__("json").dumps(_legacy_xbox_payload()),
            encoding="utf-8",
        )
        patcher = patch.dict(os.environ, {"APPDATA": self._temp_dir.name, "QT_QPA_PLATFORM": "offscreen"}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._temp_dir.cleanup)
        service = MapperService(
            backend=_DummyBackend(),
            normalizer=InputNormalizer(),
            store=SettingsStore(),
            app_monitor=_DummyMonitor(),
            output=_RecordingOutput(),
            auto_start=_DummyAutoStart(),
        )
        window = MainWindow(service=service, tray_icon=QIcon())
        window.apply_snapshot(service.current_snapshot())
        self.addCleanup(window.close)
        return window

    def _select_control(self, window: MainWindow, control: str) -> None:
        row_index = window._control_to_row[control]
        window._mapping_table.selectRow(row_index)
        window._on_mapping_selection_changed()

    def test_selecting_lb_shows_lb_editor_fields(self) -> None:
        window = self._build_window()

        self._select_control(window, "L")

        self.assertEqual(window._selected_control, "L")
        self.assertTrue(window._selected_button_value.text().endswith("LB"))
        self.assertNotEqual(window._edit_type_combo.currentData(), EDITOR_MAPPING_TYPE_STICK)
        self.assertEqual(window._current_editor_mapping_value(), ("Arrow Left", "keyboard"))
        self.assertEqual(window._edit_label.text(), "Back 5s")

    def test_selecting_right_stick_shows_stick_mode_editor_fields(self) -> None:
        window = self._build_window()

        self._select_control(window, "RIGHT_STICK_MODE")

        self.assertEqual(window._selected_control, "RIGHT_STICK_MODE")
        self.assertTrue(window._selected_button_value.text().endswith("Right Stick"))
        self.assertEqual(window._edit_type_combo.currentData(), EDITOR_MAPPING_TYPE_STICK)
        self.assertEqual(window._current_editor_mapping_value(), ("wheel_step_4way", "stick_mode"))

    def test_selecting_r3_remains_separate_from_right_stick_mode(self) -> None:
        window = self._build_window()

        self._select_control(window, "RIGHT_STICK_PRESS")

        self.assertEqual(window._selected_control, "RIGHT_STICK_PRESS")
        self.assertTrue(window._selected_button_value.text().endswith("R3"))
        self.assertNotEqual(window._edit_type_combo.currentData(), EDITOR_MAPPING_TYPE_STICK)
        self.assertEqual(window._current_editor_mapping_value(), ("Enter", "keyboard"))
        self.assertEqual(window._edit_label.text(), "Activate")

    def test_right_stick_direction_diagram_selection_resolves_to_stick_row_without_row_index_drift(self) -> None:
        window = self._build_window()

        window._on_diagram_control_selected("RIGHT_STICK_UP")

        self.assertEqual(window._selected_control, "RIGHT_STICK_MODE")
        self.assertTrue(window._selected_button_value.text().endswith("Right Stick"))
        self.assertIn("Derived row selected", window._editor_note.text())
        self.assertTrue(window._save_mapping_button.isEnabled())

    def test_selecting_horizontal_right_stick_breakdown_shows_horizontal_scroll(self) -> None:
        window = self._build_window()

        self._select_control(window, RIGHT_STICK_EFFECTIVE_LEFT)

        self.assertEqual(window._selected_control, "RIGHT_STICK_MODE")
        self.assertTrue(window._selected_button_value.text().endswith("Right Stick"))
        self.assertIn("Derived row selected", window._editor_note.text())
        self.assertTrue(window._save_mapping_button.isEnabled())

    def test_derived_right_stick_breakdown_rows_are_visible(self) -> None:
        window = self._build_window()

        row_map = {
            str(window._mapping_table.item(row_index, 0).data(0x0100)): row_index
            for row_index in range(window._mapping_table.rowCount())
        }

        self.assertIn("RIGHT_STICK_MODE", row_map)
        self.assertIn(RIGHT_STICK_EFFECTIVE_UP, row_map)
        self.assertIn(RIGHT_STICK_EFFECTIVE_DOWN, row_map)
        self.assertIn(RIGHT_STICK_EFFECTIVE_LEFT, row_map)
        self.assertIn(RIGHT_STICK_EFFECTIVE_RIGHT, row_map)
        self.assertLess(row_map["RIGHT_STICK_MODE"], row_map[RIGHT_STICK_EFFECTIVE_UP])
        self.assertLess(row_map["RIGHT_STICK_MODE"], row_map[RIGHT_STICK_EFFECTIVE_DOWN])
        self.assertLess(row_map["RIGHT_STICK_MODE"], row_map[RIGHT_STICK_EFFECTIVE_LEFT])
        self.assertLess(row_map["RIGHT_STICK_MODE"], row_map[RIGHT_STICK_EFFECTIVE_RIGHT])


if __name__ == "__main__":
    unittest.main()
