from __future__ import annotations

import unittest
from unittest.mock import patch

from zero2_input_inspector.backend.models import BackendState, BackendUpdate
from zero2_input_inspector.domain.profiles import (
    AppConfig,
    AppProfile,
    DeviceProfile,
    MappingAssignment,
    RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
    RIGHT_STICK_MODE_WHEEL_STEP_VERTICAL,
    build_default_media_presets_for_family,
)
from zero2_input_inspector.domain.state import LogicalControlState, NormalizedControllerState
from zero2_input_inspector.services.mapper_service import MapperService
from zero2_input_inspector.services.normalization import InputNormalizer


class _DummyBackend:
    def start(self) -> BackendState:
        return BackendState.empty("test")

    def poll(self) -> BackendUpdate:
        return BackendUpdate(state=BackendState.empty("test"))

    def stop(self) -> None:
        return None


class _DummyStore:
    def load(self) -> AppConfig:
        return AppConfig()

    def save(self, config: AppConfig) -> None:
        return None


class _DummyMonitor:
    def current_process_name(self) -> str:
        return ""


class _RecordingOutput:
    def __init__(self) -> None:
        self.scroll_events = []
        self.send_events = []

    def release_all(self) -> None:
        return None

    def send(self, shortcut: str):
        self.send_events.append(shortcut)
        return None

    def move_mouse(self, dx: int, dy: int) -> None:
        return None

    def scroll_mouse(self, dx: int, dy: int) -> None:
        self.scroll_events.append((dx, dy))

    def click_mouse(self, button: str, count: int = 1):
        return None


class _DummyAutoStart:
    def is_enabled(self) -> bool:
        return False

    def set_enabled(self, enabled: bool) -> None:
        return None


class AnalogScrollRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output = _RecordingOutput()
        self.service = MapperService(
            backend=_DummyBackend(),
            normalizer=InputNormalizer(),
            store=_DummyStore(),
            app_monitor=_DummyMonitor(),
            output=self.output,
            auto_start=_DummyAutoStart(),
        )
        self.device = DeviceProfile(device_id="device-1", display_name="Xbox Controller")

    def _normalized_state(self, right_stick=(0.0, 0.0), controls=None) -> NormalizedControllerState:
        return NormalizedControllerState(
            device_id="device-1",
            device_family_id="xbox",
            device_title="Xbox Controller",
            layout_name="Xbox Controller",
            diagram_kind="xbox",
            has_exact_diagram=False,
            has_canonical_mapping=True,
            resolution_source="test",
            resolution_trace=(),
            mapping_origin="test",
            visible_controls=(),
            control_labels={},
            controls=controls or {},
            right_stick=right_stick,
        )

    def _arm_wheel_neutral_latch(self, app_profile: AppProfile, preset) -> None:
        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.0, 1.13]):
            self.service._dispatch_right_stick_wheel_mode(
                self.device,
                app_profile,
                self._normalized_state((0.0, 0.0)),
                preset,
                (0.0, 0.0),
            )
            self.service._dispatch_right_stick_wheel_mode(
                self.device,
                app_profile,
                self._normalized_state((0.0, 0.0)),
                preset,
                (0.0, 0.0),
            )

    def test_vertical_only_scroll_mapping_forces_horizontal_scroll_to_zero(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-1",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            scroll_sensitivity=8.0,
            scroll_deadzone=0.32,
        )

        self.service._dispatch_right_stick_scroll(
            self.device,
            app_profile,
            self._normalized_state((0.9, 0.9)),
            (0.9, 0.9),
            (False, False, True, True),
        )

        self.assertTrue(self.output.scroll_events)
        self.assertTrue(all(dx == 0 for dx, _dy in self.output.scroll_events))
        self.assertTrue(all(dy != 0 for _dx, dy in self.output.scroll_events))

    def test_scroll_deadzone_clears_idle_drift_and_remainders(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-2",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            scroll_sensitivity=8.0,
            scroll_deadzone=0.32,
            scroll_activation_threshold=0.6,
        )
        self.service._mouse_scroll_remainders["device-1"] = (0.7, 0.7)

        self.service._dispatch_right_stick_scroll(
            self.device,
            app_profile,
            self._normalized_state((0.05, 0.2)),
            (0.05, 0.2),
            (False, False, True, True),
        )

        self.assertEqual(self.output.scroll_events, [])
        self.assertNotIn("device-1", self.service._mouse_scroll_remainders)

    def test_xbox_default_preset_uses_wheel_step_4way_mode(self) -> None:
        preset = build_default_media_presets_for_family("xbox")[0]

        self.assertEqual(preset.right_stick_mode, RIGHT_STICK_MODE_WHEEL_STEP_4WAY)
        self.assertEqual(preset.assignment_for("RIGHT_STICK_LEFT").shortcut, "")
        self.assertEqual(preset.assignment_for("RIGHT_STICK_RIGHT").shortcut, "")
        self.assertEqual(preset.assignment_for("LEFT_STICK_LEFT").action_kind, "mouse_move")
        self.assertEqual(preset.assignment_for("LEFT_STICK_RIGHT").action_kind, "mouse_move")

    def test_idle_right_stick_drift_does_not_emit_wheel_without_neutral_latch(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-3",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            scroll_deadzone=0.32,
            scroll_activation_threshold=0.6,
            presets=build_default_media_presets_for_family("xbox"),
        )
        preset = app_profile.presets[0]

        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.0, 1.15, 1.31]):
            self.service._dispatch_right_stick_wheel_mode(
                self.device,
                app_profile,
                self._normalized_state((0.0, 0.82)),
                preset,
                (0.0, 0.82),
            )
            self.service._dispatch_right_stick_wheel_mode(
                self.device,
                app_profile,
                self._normalized_state((0.0, 0.82)),
                preset,
                (0.0, 0.82),
            )
            self.service._dispatch_right_stick_wheel_mode(
                self.device,
                app_profile,
                self._normalized_state((0.0, 0.82)),
                preset,
                (0.0, 0.82),
            )

        diagnostics = self.service.input_diagnostics("device-1")
        self.assertEqual(self.output.scroll_events, [])
        self.assertFalse(diagnostics["wheel_neutral_latch"]["armed"])
        self.assertEqual(diagnostics["wheel_repeat_active_control"], "")
        self.assertEqual(diagnostics["wheel_gate_reason"], "awaiting_neutral_latch")

    def test_xbox_tuned_thresholds_emit_for_normal_intentional_push(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-3a",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            scroll_deadzone=0.32,
            scroll_activation_threshold=0.6,
            presets=build_default_media_presets_for_family("xbox"),
        )
        preset = app_profile.presets[0]
        self._arm_wheel_neutral_latch(app_profile, preset)

        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.14]):
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self._normalized_state((0.04, 0.38)),
                preset,
                (0.04, 0.38),
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
            )

        diagnostics = self.service.input_diagnostics("device-1")
        self.assertEqual(self.output.scroll_events, [(0, 1)])
        self.assertEqual(diagnostics["wheel_gate_config"]["neutral_threshold"], 0.18)
        self.assertEqual(diagnostics["wheel_gate_config"]["activation_threshold"], 0.34)
        self.assertEqual(diagnostics["wheel_gate_config"]["dominance_margin"], 0.03)
        self.assertEqual(diagnostics["wheel_gate_config"]["neutral_latch_seconds"], 0.05)
        self.assertEqual(diagnostics["wheel_gate_reason"], "emitted_wheel_up")

    def test_wheel_repeat_only_starts_after_neutral_latch_and_intentional_movement(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-3b",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            scroll_deadzone=0.32,
            scroll_activation_threshold=0.6,
            presets=build_default_media_presets_for_family("xbox"),
        )
        preset = app_profile.presets[0]
        self._arm_wheel_neutral_latch(app_profile, preset)

        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.14, 1.20, 1.30]):
            self.service._dispatch_right_stick_wheel_mode(
                self.device,
                app_profile,
                self._normalized_state((0.1, 0.86)),
                preset,
                (0.1, 0.86),
            )
            self.service._dispatch_right_stick_wheel_mode(
                self.device,
                app_profile,
                self._normalized_state((0.1, 0.86)),
                preset,
                (0.1, 0.86),
            )
            self.service._dispatch_right_stick_wheel_mode(
                self.device,
                app_profile,
                self._normalized_state((0.1, 0.86)),
                preset,
                (0.1, 0.86),
            )

        self.assertEqual(self.output.scroll_events, [(0, 1), (0, 1)])
        diagnostics = self.service.input_diagnostics("device-1")
        self.assertTrue(diagnostics["wheel_neutral_latch"]["armed"])
        self.assertEqual(diagnostics["wheel_repeat_active_control"], "RIGHT_STICK_UP")
        self.assertEqual(diagnostics["wheel_gate_reason"], "emitted_wheel_up")

    def test_returning_right_stick_to_center_stops_wheel_repeat(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-4",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            scroll_deadzone=0.32,
            scroll_activation_threshold=0.6,
            presets=build_default_media_presets_for_family("xbox"),
        )
        preset = app_profile.presets[0]
        self._arm_wheel_neutral_latch(app_profile, preset)

        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.14, 1.18, 1.32]):
            self.service._dispatch_right_stick_wheel_mode(
                self.device,
                app_profile,
                self._normalized_state((0.0, 0.85)),
                preset,
                (0.0, 0.85),
            )
            self.service._dispatch_right_stick_wheel_mode(
                self.device,
                app_profile,
                self._normalized_state((0.0, 0.0)),
                preset,
                (0.0, 0.0),
            )
            self.service._dispatch_right_stick_wheel_mode(
                self.device,
                app_profile,
                self._normalized_state((0.0, 0.0)),
                preset,
                (0.0, 0.0),
            )

        self.assertEqual(self.output.scroll_events, [(0, 1)])
        self.assertNotIn("device-1", self.service._wheel_repeat_last_fired)
        diagnostics = self.service.input_diagnostics("device-1")
        self.assertEqual(diagnostics["wheel_repeat_reset_reason"], "neutral")
        self.assertEqual(diagnostics["wheel_gate_reason"], "below_deadzone")

    def test_no_false_dpad_up_output_at_idle(self) -> None:
        preset = build_default_media_presets_for_family("xbox")[0]
        app_profile = AppProfile(
            app_profile_id="app-5",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            presets=[preset],
        )
        self.device.app_profiles = [app_profile]
        self.device.selected_app_profile_id = app_profile.app_profile_id
        self.service._config.devices = [self.device]
        self.service._current_process_name = "chrome.exe"
        self.service._normalized_states = {
            "device-1": self._normalized_state(
                controls={
                    "DPAD_UP": LogicalControlState(
                        control="DPAD_UP",
                        value=0.0,
                        is_active=False,
                        source="Hat 0 Up",
                    ),
                    "RIGHT_TRIGGER": LogicalControlState(
                        control="RIGHT_TRIGGER",
                        value=0.0,
                        is_active=False,
                        source="Axis 5",
                    ),
                }
            )
        }

        self.service._run_mappings()

        diagnostics = self.service.input_diagnostics("device-1")
        self.assertEqual(self.output.send_events, [])
        self.assertEqual(diagnostics["active_controls"], [])
        self.assertEqual(diagnostics["upward_candidates"], [])

    def test_diagnostics_identify_upward_action_source_cleanly(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-6",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            presets=build_default_media_presets_for_family("xbox"),
        )
        preset = app_profile.presets[0]
        self._arm_wheel_neutral_latch(app_profile, preset)
        self.service._normalized_states["device-1"] = self._normalized_state(
            (0.0, 0.88),
            controls={
                "RIGHT_STICK_UP": LogicalControlState(
                    control="RIGHT_STICK_UP",
                    value=0.88,
                    is_active=True,
                    source="Axis 4-",
                )
            },
        )
        stabilized = self.service._stabilize_right_stick_vector("device-1", (0.0, 0.88))

        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.14]):
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self.service._normalized_states["device-1"],
                preset,
                stabilized,
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
            )

        diagnostics = self.service.input_diagnostics("device-1")
        self.assertEqual(diagnostics["last_emitted_action"]["source_kind"], "mouse_wheel_up")
        self.assertEqual(diagnostics["last_emitted_action"]["control"], "RIGHT_STICK_UP")
        self.assertEqual(diagnostics["last_emitted_action"]["canonical_source"], "right_stick_mode:wheel_step_4way")
        self.assertEqual(diagnostics["last_upward_emission"]["source_kind"], "mouse_wheel_up")
        self.assertIn("stabilized_vector", diagnostics)
        self.assertEqual(diagnostics["wheel_gate_reason"], "emitted_wheel_up")

    def test_right_stick_left_and_right_emit_horizontal_wheel_in_4way_mode(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-6b",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            presets=build_default_media_presets_for_family("xbox"),
        )
        preset = app_profile.presets[0]
        self._arm_wheel_neutral_latch(app_profile, preset)

        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.14, 1.30]):
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self._normalized_state((0.92, 0.1)),
                preset,
                (0.92, 0.1),
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
            )
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self._normalized_state((-0.92, 0.1)),
                preset,
                (-0.92, 0.1),
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
            )

        self.assertEqual(self.output.scroll_events, [(1, 0), (-1, 0)])
        diagnostics = self.service.input_diagnostics("device-1")
        self.assertEqual(diagnostics["wheel_vector_analysis"]["dominant_axis"], "horizontal")
        self.assertEqual(diagnostics["last_emitted_action"]["canonical_source"], "right_stick_mode:wheel_step_4way")
        self.assertEqual(diagnostics["wheel_gate_reason"], "emitted_wheel_left")

    def test_wheel_step_4way_emits_all_four_directions(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-6b1",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            presets=build_default_media_presets_for_family("xbox"),
        )
        preset = app_profile.presets[0]
        self._arm_wheel_neutral_latch(app_profile, preset)

        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.14, 1.31, 1.48, 1.65]):
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self._normalized_state((0.05, 0.9)),
                preset,
                (0.05, 0.9),
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
            )
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self._normalized_state((0.05, -0.9)),
                preset,
                (0.05, -0.9),
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
            )
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self._normalized_state((0.9, 0.05)),
                preset,
                (0.9, 0.05),
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
            )
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self._normalized_state((-0.9, 0.05)),
                preset,
                (-0.9, 0.05),
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
            )

        diagnostics = self.service.input_diagnostics("device-1")
        self.assertEqual(self.output.scroll_events, [(0, 1), (0, -1), (1, 0), (-1, 0)])
        self.assertEqual(diagnostics["wheel_gate_reason"], "emitted_wheel_left")
        self.assertEqual(diagnostics["last_emitted_action"]["source_kind"], "mouse_wheel_left")
        self.assertEqual(diagnostics["last_emitted_action"]["canonical_source"], "right_stick_mode:wheel_step_4way")

    def test_vertical_only_mode_still_ignores_horizontal_input(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-6c",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            scroll_deadzone=0.32,
            scroll_activation_threshold=0.6,
            presets=build_default_media_presets_for_family("xbox"),
        )
        preset = app_profile.presets[0]
        self._arm_wheel_neutral_latch(app_profile, preset)

        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.14, 1.30]):
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self._normalized_state((0.92, 0.1)),
                preset,
                (0.92, 0.1),
                RIGHT_STICK_MODE_WHEEL_STEP_VERTICAL,
            )
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self._normalized_state((-0.92, 0.1)),
                preset,
                (-0.92, 0.1),
                RIGHT_STICK_MODE_WHEEL_STEP_VERTICAL,
            )

        self.assertEqual(self.output.scroll_events, [])
        diagnostics = self.service.input_diagnostics("device-1")
        self.assertEqual(diagnostics["wheel_gate_reason"], "direction_unassigned")

    def test_directional_dominance_prevents_diagonal_misfire(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-6d",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            scroll_deadzone=0.32,
            scroll_activation_threshold=0.6,
            presets=build_default_media_presets_for_family("xbox"),
        )
        preset = app_profile.presets[0]
        self._arm_wheel_neutral_latch(app_profile, preset)

        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.14]):
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self._normalized_state((0.58, 0.56)),
                preset,
                (0.58, 0.56),
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
            )

        diagnostics = self.service.input_diagnostics("device-1")
        self.assertEqual(self.output.scroll_events, [])
        self.assertEqual(diagnostics["wheel_repeat_active_control"], "")
        self.assertEqual(diagnostics["wheel_vector_analysis"]["dominant_control"], "")
        self.assertEqual(diagnostics["wheel_gate_reason"], "dominance_failed")

    def test_diagnostics_report_below_activation_threshold_reason(self) -> None:
        app_profile = AppProfile(
            app_profile_id="app-6e",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            scroll_deadzone=0.32,
            scroll_activation_threshold=0.6,
            presets=build_default_media_presets_for_family("xbox"),
        )
        preset = app_profile.presets[0]
        self._arm_wheel_neutral_latch(app_profile, preset)

        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.14]):
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device,
                app_profile,
                self._normalized_state((0.02, 0.31)),
                preset,
                (0.02, 0.31),
                RIGHT_STICK_MODE_WHEEL_STEP_4WAY,
            )

        diagnostics = self.service.input_diagnostics("device-1")
        self.assertEqual(self.output.scroll_events, [])
        self.assertEqual(diagnostics["wheel_gate_reason"], "below_activation_threshold")

    def test_diagnostics_classify_keyboard_up_separately(self) -> None:
        self.service._normalized_states["device-1"] = self._normalized_state(
            controls={
                "RIGHT_TRIGGER": LogicalControlState(
                    control="RIGHT_TRIGGER",
                    value=1.0,
                    is_active=True,
                    source="Axis 5",
                )
            }
        )

        self.service._dispatch_assignment(
            self.device,
            "RIGHT_TRIGGER",
            MappingAssignment(
                control="RIGHT_TRIGGER",
                shortcut="Up",
                label="Volume Up",
                action_kind="keyboard",
            ),
        )

        diagnostics = self.service.input_diagnostics("device-1")
        self.assertEqual(diagnostics["last_emitted_action"]["source_kind"], "keyboard_up")
        self.assertEqual(diagnostics["last_emitted_action"]["control"], "RIGHT_TRIGGER")


if __name__ == "__main__":
    unittest.main()
