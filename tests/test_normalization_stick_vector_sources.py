from __future__ import annotations

import unittest
from unittest.mock import patch

from zero2_input_inspector.backend.models import BackendState, BackendUpdate, ControllerInfo, RawControllerState
from zero2_input_inspector.domain.profiles import (
    AppConfig,
    AppProfile,
    DeviceProfile,
    build_default_device_profile,
    build_default_media_presets_for_family,
)
from zero2_input_inspector.services.mapper_service import MapperService
from zero2_input_inspector.services.normalization import InputNormalizer


def _xbox_info(
    *,
    is_standard_controller: bool,
    standard_mapping=(),
) -> ControllerInfo:
    return ControllerInfo(
        device_id="xbox-1",
        instance_id=1,
        name="Xbox Series X Controller",
        guid="",
        is_standard_controller=is_standard_controller,
        standard_mapping=tuple(standard_mapping),
        power_level="unknown",
        axes_count=6,
        buttons_count=11,
        hats_count=1,
    )


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

    def release_all(self) -> None:
        return None

    def send(self, shortcut: str):
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


class NormalizationStickVectorSourceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.normalizer = InputNormalizer()
        self.saved_device = build_default_device_profile("xbox-1", "Xbox Series X Controller", family_id="xbox")

    def test_standard_mapping_right_stick_vector_uses_same_axes_as_directional_activation(self) -> None:
        info = _xbox_info(
            is_standard_controller=True,
            standard_mapping=(
                ("leftx", "a0"),
                ("lefty", "a1"),
                ("rightx", "a2"),
                ("righty", "a3"),
            ),
        )
        raw_state = RawControllerState(
            info=info,
            axes=(0.2, -0.3, 0.65, -0.75, -1.0, 0.0),
            buttons=(False,) * 11,
            hats=((0, 0),),
        )

        normalized = self.normalizer.normalize(raw_state, self.saved_device)

        self.assertEqual(normalized.mapping_origin, "SDL standard mapping")
        self.assertEqual(normalized.left_stick, (0.2, 0.3))
        self.assertEqual(normalized.right_stick, (0.65, 0.75))
        self.assertEqual(normalized.left_stick_vector_source, "SDL standard mapping")
        self.assertEqual(normalized.right_stick_vector_source, "SDL standard mapping")
        self.assertEqual(normalized.left_stick_axis_indices, (0, 1))
        self.assertEqual(normalized.right_stick_axis_indices, (2, 3))
        self.assertTrue(normalized.controls["RIGHT_STICK_RIGHT"].is_active)
        self.assertTrue(normalized.controls["RIGHT_STICK_UP"].is_active)
        self.assertFalse(normalized.controls["RIGHT_STICK_DOWN"].is_active)

    def test_raw_fallback_right_stick_vector_uses_raw_fallback_axes(self) -> None:
        info = _xbox_info(is_standard_controller=False)
        raw_state = RawControllerState(
            info=info,
            axes=(0.2, -0.3, 0.65, -0.75, -0.4, 0.0),
            buttons=(False,) * 11,
            hats=((0, 0),),
        )

        normalized = self.normalizer.normalize(raw_state, self.saved_device)

        self.assertEqual(normalized.right_stick, (-0.75, 0.4))
        self.assertEqual(normalized.right_stick_vector_source, "raw fallback")
        self.assertEqual(normalized.right_stick_axis_indices, (3, 4))

    def test_regression_standard_mapping_no_longer_uses_mismatched_raw_fallback_axes(self) -> None:
        info = _xbox_info(
            is_standard_controller=True,
            standard_mapping=(
                ("leftx", "a0"),
                ("lefty", "a1"),
                ("rightx", "a2"),
                ("righty", "a3"),
            ),
        )
        raw_state = RawControllerState(
            info=info,
            axes=(0.0, 0.0, 0.82, 0.0, -1.0, 0.0),
            buttons=(False,) * 11,
            hats=((0, 0),),
        )

        normalized = self.normalizer.normalize(raw_state, self.saved_device)

        self.assertTrue(normalized.controls["RIGHT_STICK_RIGHT"].is_active)
        self.assertFalse(normalized.controls["RIGHT_STICK_UP"].is_active)
        self.assertEqual(normalized.right_stick, (0.82, -0.0))
        self.assertNotEqual(normalized.right_stick, (0.0, 1.0))
        self.assertEqual(normalized.right_stick_axis_indices, (2, 3))


class RightStickDispatchConsistencyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.normalizer = InputNormalizer()
        self.saved_device = build_default_device_profile("xbox-1", "Xbox Series X Controller", family_id="xbox")
        self.output = _RecordingOutput()
        self.service = MapperService(
            backend=_DummyBackend(),
            normalizer=self.normalizer,
            store=_DummyStore(),
            app_monitor=_DummyMonitor(),
            output=self.output,
            auto_start=_DummyAutoStart(),
        )
        self.device_profile = DeviceProfile(device_id="xbox-1", display_name="Xbox Series X Controller")

    def test_wheel_dispatch_uses_vector_matching_active_right_stick_direction(self) -> None:
        info = _xbox_info(
            is_standard_controller=True,
            standard_mapping=(
                ("leftx", "a0"),
                ("lefty", "a1"),
                ("rightx", "a2"),
                ("righty", "a3"),
            ),
        )
        raw_state = RawControllerState(
            info=info,
            axes=(0.0, 0.0, 0.82, 0.0, -1.0, 0.0),
            buttons=(False,) * 11,
            hats=((0, 0),),
        )
        normalized = self.normalizer.normalize(raw_state, self.saved_device)
        app_profile = AppProfile(
            app_profile_id="app-rs",
            name="YouTube",
            process_name="*",
            family_id="xbox",
            presets=build_default_media_presets_for_family("xbox"),
        )
        preset = app_profile.presets[0]
        active_controls = {
            control
            for control, control_state in normalized.controls.items()
            if control_state.is_active
        }
        self.service._update_input_diagnostics(
            device_profile=self.device_profile,
            app_profile=app_profile,
            preset=preset,
            normalized_state=normalized,
            active_controls=active_controls,
            rising_controls=active_controls,
        )
        stabilized_vector = self.service._stabilize_right_stick_vector("xbox-1", normalized.right_stick)

        with patch("zero2_input_inspector.services.mapper_service.monotonic", side_effect=[1.0, 1.1, 1.2]):
            self.service._dispatch_right_stick_wheel_mode(
                self.device_profile,
                app_profile,
                normalized,
                preset,
                (0.0, 0.0),
            )
            self.service._dispatch_right_stick_wheel_mode(
                self.device_profile,
                app_profile,
                normalized,
                preset,
                (0.0, 0.0),
            )
            self.service._dispatch_right_stick_wheel_step_mode(
                self.device_profile,
                app_profile,
                normalized,
                preset,
                stabilized_vector,
                preset.right_stick_mode,
            )

        diagnostics = self.service.input_diagnostics("xbox-1")
        self.assertEqual(self.output.scroll_events, [(1, 0)])
        self.assertEqual(diagnostics["raw_vector"], (0.82, -0.0))
        self.assertEqual(diagnostics["wheel_gate_reason"], "emitted_wheel_right")
        self.assertEqual(diagnostics["right_stick_vector_source"], "SDL standard mapping")
        self.assertEqual(diagnostics["right_stick_axis_indices"], (2, 3))


if __name__ == "__main__":
    unittest.main()
