from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from zero2_input_inspector.backend.models import BackendState, BackendUpdate
from zero2_input_inspector.domain.profiles import (
    MAPPING_ACTION_STICK_MODE,
    RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
    RIGHT_STICK_MODE_WHEEL_STEP_VERTICAL,
    XBOX_MEDIA_FALLBACK_LEGACY_ASSIGNMENTS,
)
from zero2_input_inspector.domain.controls import (
    RIGHT_STICK_EFFECTIVE_DOWN,
    RIGHT_STICK_EFFECTIVE_LEFT,
    RIGHT_STICK_EFFECTIVE_RIGHT,
    RIGHT_STICK_EFFECTIVE_UP,
)
from zero2_input_inspector.services.mapper_service import MapperService
from zero2_input_inspector.services.normalization import InputNormalizer
from zero2_input_inspector.services.settings_store import SettingsStore


class _DummyBackend:
    def start(self) -> BackendState:
        return BackendState.empty("test")

    def poll(self) -> BackendUpdate:
        return BackendUpdate(state=BackendState.empty("test"))

    def stop(self) -> None:
        return None


class _DummyMonitor:
    def current_process_name(self) -> str:
        return "chrome.exe"


class _RecordingOutput:
    def release_all(self) -> None:
        return None

    def send(self, shortcut: str):
        return None

    def move_mouse(self, dx: int, dy: int) -> None:
        return None

    def scroll_mouse(self, dx: int, dy: int) -> None:
        return None

    def click_mouse(self, button: str, count: int = 1):
        return None


class _DummyAutoStart:
    def is_enabled(self) -> bool:
        return False

    def set_enabled(self, enabled: bool) -> None:
        return None


def _legacy_xbox_payload() -> dict:
    preset_mappings = {}
    for control, assignment in XBOX_MEDIA_FALLBACK_LEGACY_ASSIGNMENTS.items():
        preset_mappings[control] = {
            "shortcut": assignment.shortcut,
            "label": assignment.label,
            "action_kind": assignment.action_kind,
        }

    return {
        "version": 1,
        "selected_device_id": "device-1",
        "settings": {
            "language": "en",
            "theme": "gquuuuuux",
            "auto_start": False,
        },
        "devices": [
            {
                "device_id": "device-1",
                "display_name": "Xbox Controller",
                "guid": "",
                "last_seen_name": "Xbox Controller",
                "saved_family_id": "",
                "family_override_id": "",
                "shape_signature": "",
                "selected_app_profile_id": "app-1",
                "preset_switch": {
                    "previous_control": "SELECT",
                    "next_control": "START",
                },
                "app_profiles": [
                    {
                        "app_profile_id": "app-1",
                        "name": "YouTube",
                        "process_name": "*",
                        "family_id": "",
                        "active_preset_index": 0,
                        "mouse_sensitivity": 1.0,
                        "scroll_sensitivity": 1.0,
                        "analog_deadzone": 0.16,
                        "scroll_deadzone": 0.32,
                        "scroll_activation_threshold": 0.6,
                        "analog_curve": 1.7,
                        "slow_speed_multiplier": 0.45,
                        "fast_speed_multiplier": 1.75,
                        "slow_modifier_control": "",
                        "fast_modifier_control": "",
                        "presets": [
                            {
                                "preset_id": "preset-1",
                                "name": "YouTube",
                                "mappings": preset_mappings,
                            }
                        ],
                    }
                ],
            }
        ],
    }


class XboxMediaFallbackLoadPathTest(unittest.TestCase):
    def test_legacy_saved_xbox_youtube_preset_is_rebuilt_on_load(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "zero2-input-inspector"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.json").write_text(json.dumps(_legacy_xbox_payload()), encoding="utf-8")

            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                store = SettingsStore()
                config = store.load()

        report = store.last_load_report
        device = config.device_by_id("device-1")
        self.assertIsNotNone(device)
        app_profile = device.selected_app_profile()
        preset = app_profile.active_preset()

        self.assertEqual(report["source"], "saved_config")
        self.assertTrue(report["migrated"])
        self.assertTrue(report["legacy_xbox_recognized"])
        self.assertEqual(app_profile.family_id, "xbox")
        self.assertEqual(preset.right_stick_mode, RIGHT_STICK_MODE_WHEEL_STEP_4WAY)
        self.assertEqual(preset.assignment_for("FACE_SOUTH").action_kind, "mouse_left_click")
        self.assertEqual(preset.assignment_for("FACE_SOUTH").label, "Left Click")
        self.assertEqual(preset.assignment_for("RIGHT_STICK_UP").shortcut, "")
        self.assertEqual(preset.assignment_for("RIGHT_STICK_DOWN").shortcut, "")
        self.assertEqual(preset.assignment_for("RIGHT_STICK_LEFT").shortcut, "")
        self.assertEqual(preset.assignment_for("RIGHT_STICK_RIGHT").shortcut, "")

    def test_runtime_snapshot_uses_rebuilt_xbox_media_fallback_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "zero2-input-inspector"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.json").write_text(json.dumps(_legacy_xbox_payload()), encoding="utf-8")

            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                service = MapperService(
                    backend=_DummyBackend(),
                    normalizer=InputNormalizer(),
                    store=SettingsStore(),
                    app_monitor=_DummyMonitor(),
                    output=_RecordingOutput(),
                    auto_start=_DummyAutoStart(),
                )
                snapshot = service.current_snapshot()
                logs = service.current_snapshot().logs

        self.assertIsNotNone(snapshot.selected_preset)
        self.assertEqual(snapshot.selected_preset.right_stick_mode, RIGHT_STICK_MODE_WHEEL_STEP_4WAY)
        self.assertEqual(snapshot.selected_preset.assignment_for("FACE_SOUTH").label, "Left Click")
        self.assertEqual(snapshot.selected_preset.assignment_for("FACE_SOUTH").action_kind, "mouse_left_click")
        self.assertEqual(snapshot.selected_preset.assignment_for("RIGHT_STICK_LEFT").shortcut, "")
        self.assertEqual(snapshot.selected_preset.assignment_for("RIGHT_STICK_RIGHT").shortcut, "")
        right_stick_rows = [row for row in snapshot.mapping_rows if row.control == "RIGHT_STICK_MODE"]
        self.assertEqual(len(right_stick_rows), 1)
        self.assertEqual(right_stick_rows[0].action_kind, MAPPING_ACTION_STICK_MODE)
        self.assertEqual(right_stick_rows[0].shortcut, RIGHT_STICK_MODE_WHEEL_STEP_4WAY)
        self.assertEqual(right_stick_rows[0].action_text, "Wheel Step 4-Way")
        self.assertFalse(any(row.control == "RIGHT_STICK_UP" for row in snapshot.mapping_rows))
        effective_rows = {
            row.control: row for row in snapshot.mapping_rows if row.control.startswith("RIGHT_STICK_EFFECTIVE_")
        }
        self.assertEqual(effective_rows[RIGHT_STICK_EFFECTIVE_UP].action_text, "Wheel Up")
        self.assertEqual(effective_rows[RIGHT_STICK_EFFECTIVE_UP].label, "Wheel Up")
        self.assertEqual(effective_rows[RIGHT_STICK_EFFECTIVE_DOWN].action_text, "Wheel Down")
        self.assertEqual(effective_rows[RIGHT_STICK_EFFECTIVE_DOWN].label, "Wheel Down")
        self.assertEqual(effective_rows[RIGHT_STICK_EFFECTIVE_LEFT].action_text, "Horizontal Scroll Left")
        self.assertEqual(effective_rows[RIGHT_STICK_EFFECTIVE_LEFT].label, "Horizontal Scroll Left")
        self.assertEqual(effective_rows[RIGHT_STICK_EFFECTIVE_RIGHT].action_text, "Horizontal Scroll Right")
        self.assertEqual(effective_rows[RIGHT_STICK_EFFECTIVE_RIGHT].label, "Horizontal Scroll Right")
        self.assertTrue(any("Config load -> source=saved_config" in line for line in logs))
        self.assertTrue(any("legacy_xbox=True" in line for line in logs))

    def test_runtime_snapshot_normalizes_stale_legacy_labels_to_canonical_defaults(self) -> None:
        payload = _legacy_xbox_payload()
        preset_mappings = payload["devices"][0]["app_profiles"][0]["presets"][0]["mappings"]
        preset_mappings["FACE_SOUTH"]["shortcut"] = ""
        preset_mappings["FACE_SOUTH"]["action_kind"] = "mouse_left_click"
        preset_mappings["FACE_SOUTH"]["label"] = "Play/Pause"
        preset_mappings["FACE_EAST"]["shortcut"] = "Alt+Left"
        preset_mappings["FACE_EAST"]["action_kind"] = "keyboard"
        preset_mappings["FACE_EAST"]["label"] = "Forward 10s"

        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "zero2-input-inspector"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.json").write_text(json.dumps(payload), encoding="utf-8")

            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                service = MapperService(
                    backend=_DummyBackend(),
                    normalizer=InputNormalizer(),
                    store=SettingsStore(),
                    app_monitor=_DummyMonitor(),
                    output=_RecordingOutput(),
                    auto_start=_DummyAutoStart(),
                )
                snapshot = service.current_snapshot()

        preset = snapshot.selected_preset
        self.assertIsNotNone(preset)
        self.assertEqual(preset.assignment_for("FACE_SOUTH").label, "Left Click")
        self.assertEqual(preset.assignment_for("FACE_EAST").label, "Browser Back")
        row_map = {row.control: row for row in snapshot.mapping_rows}
        self.assertEqual(row_map["FACE_SOUTH"].label, "Left Click")
        self.assertEqual(row_map["FACE_EAST"].label, "Browser Back")

    def test_reset_to_default_fully_rebuilds_xbox_media_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "zero2-input-inspector"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.json").write_text(json.dumps(_legacy_xbox_payload()), encoding="utf-8")

            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                service = MapperService(
                    backend=_DummyBackend(),
                    normalizer=InputNormalizer(),
                    store=SettingsStore(),
                    app_monitor=_DummyMonitor(),
                    output=_RecordingOutput(),
                    auto_start=_DummyAutoStart(),
                )
                service.reset_selected_app_presets("device-1")
                snapshot = service.current_snapshot()

        preset = snapshot.selected_preset
        self.assertIsNotNone(preset)
        self.assertEqual(preset.right_stick_mode, RIGHT_STICK_MODE_WHEEL_STEP_4WAY)
        self.assertEqual(preset.assignment_for("FACE_SOUTH").action_kind, "mouse_left_click")
        self.assertEqual(preset.assignment_for("FACE_SOUTH").label, "Left Click")
        self.assertEqual(preset.assignment_for("RIGHT_STICK_UP").shortcut, "")
        self.assertEqual(preset.assignment_for("RIGHT_STICK_DOWN").shortcut, "")
        self.assertEqual(preset.assignment_for("RIGHT_STICK_LEFT").shortcut, "")
        self.assertEqual(preset.assignment_for("RIGHT_STICK_RIGHT").shortcut, "")

    def test_reset_mapping_to_default_restores_a_to_left_click(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "zero2-input-inspector"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.json").write_text(json.dumps(_legacy_xbox_payload()), encoding="utf-8")

            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                service = MapperService(
                    backend=_DummyBackend(),
                    normalizer=InputNormalizer(),
                    store=SettingsStore(),
                    app_monitor=_DummyMonitor(),
                    output=_RecordingOutput(),
                    auto_start=_DummyAutoStart(),
                )
                service.update_mapping("device-1", "FACE_SOUTH", "Space", "Play/Pause", "keyboard")
                service.reset_mapping_to_default("device-1", "FACE_SOUTH")
                snapshot = service.current_snapshot()

        preset = snapshot.selected_preset
        self.assertIsNotNone(preset)
        self.assertEqual(preset.assignment_for("FACE_SOUTH").action_kind, "mouse_left_click")
        self.assertEqual(preset.assignment_for("FACE_SOUTH").label, "Left Click")

    def test_save_mapping_resynchronizes_canonical_label_when_action_matches_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "zero2-input-inspector"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.json").write_text(json.dumps(_legacy_xbox_payload()), encoding="utf-8")

            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                service = MapperService(
                    backend=_DummyBackend(),
                    normalizer=InputNormalizer(),
                    store=SettingsStore(),
                    app_monitor=_DummyMonitor(),
                    output=_RecordingOutput(),
                    auto_start=_DummyAutoStart(),
                )
                service.update_mapping("device-1", "FACE_SOUTH", "", "Play/Pause", "mouse_left_click")
                service.update_mapping("device-1", "FACE_EAST", "Alt+Left", "Forward 10s", "keyboard")
                snapshot = service.current_snapshot()

        preset = snapshot.selected_preset
        self.assertIsNotNone(preset)
        self.assertEqual(preset.assignment_for("FACE_SOUTH").label, "Left Click")
        self.assertEqual(preset.assignment_for("FACE_EAST").label, "Browser Back")
        row_map = {row.control: row for row in snapshot.mapping_rows}
        self.assertEqual(row_map["FACE_SOUTH"].label, "Left Click")
        self.assertEqual(row_map["FACE_EAST"].label, "Browser Back")

    def test_reset_mapping_to_default_restores_right_stick_up_to_canonical_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "zero2-input-inspector"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.json").write_text(json.dumps(_legacy_xbox_payload()), encoding="utf-8")

            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                service = MapperService(
                    backend=_DummyBackend(),
                    normalizer=InputNormalizer(),
                    store=SettingsStore(),
                    app_monitor=_DummyMonitor(),
                    output=_RecordingOutput(),
                    auto_start=_DummyAutoStart(),
                )
                service.update_mapping("device-1", "RIGHT_STICK_MODE", "disabled", "", MAPPING_ACTION_STICK_MODE)
                service.reset_mapping_to_default("device-1", "RIGHT_STICK_UP")
                snapshot = service.current_snapshot()

        preset = snapshot.selected_preset
        self.assertIsNotNone(preset)
        self.assertEqual(preset.right_stick_mode, RIGHT_STICK_MODE_WHEEL_STEP_4WAY)
        right_stick_rows = [row for row in snapshot.mapping_rows if row.control == "RIGHT_STICK_MODE"]
        self.assertEqual(len(right_stick_rows), 1)
        self.assertEqual(right_stick_rows[0].action_text, "Wheel Step 4-Way")

    def test_reset_mapping_to_default_shows_explicit_unassigned_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "zero2-input-inspector"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.json").write_text(json.dumps(_legacy_xbox_payload()), encoding="utf-8")

            with patch.dict(os.environ, {"APPDATA": temp_dir}, clear=False):
                service = MapperService(
                    backend=_DummyBackend(),
                    normalizer=InputNormalizer(),
                    store=SettingsStore(),
                    app_monitor=_DummyMonitor(),
                    output=_RecordingOutput(),
                    auto_start=_DummyAutoStart(),
                )
                service.update_mapping("device-1", "GUIDE", "Ctrl+G", "Guide Action", "keyboard")
                service.reset_mapping_to_default("device-1", "GUIDE")
                snapshot = service.current_snapshot()

        preset = snapshot.selected_preset
        self.assertIsNotNone(preset)
        self.assertEqual(preset.assignment_for("GUIDE").shortcut, "")
        guide_rows = [row for row in snapshot.mapping_rows if row.control == "GUIDE"]
        self.assertEqual(len(guide_rows), 1)
        self.assertEqual(guide_rows[0].action_text, "Unassigned")


if __name__ == "__main__":
    unittest.main()
