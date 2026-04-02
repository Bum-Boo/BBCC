from __future__ import annotations

import unittest

from zero2_input_inspector.backend.models import BackendState, BackendUpdate
from zero2_input_inspector.domain.profiles import AppConfig, MappingAssignment
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
    def __init__(self) -> None:
        self.saved = None

    def load(self) -> AppConfig:
        return AppConfig()

    def save(self, config: AppConfig) -> None:
        self.saved = config


class _DummyMonitor:
    def current_process_name(self) -> str:
        return ""


class _DummyOutput:
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


class SingleFireMappingRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = MapperService(
            backend=_DummyBackend(),
            normalizer=InputNormalizer(),
            store=_DummyStore(),
            app_monitor=_DummyMonitor(),
            output=_DummyOutput(),
            auto_start=_DummyAutoStart(),
        )

    def test_browser_back_style_mappings_are_single_fire(self) -> None:
        browser_back = MappingAssignment(control="L", shortcut="Alt+Left", label="Browser Back")
        repeatable_seek = MappingAssignment(control="R", shortcut="J", label="Back 10s")

        self.assertTrue(self.service._is_single_fire_assignment(browser_back))
        self.assertFalse(self.service._is_single_fire_assignment(repeatable_seek))

        self.assertTrue(self.service._should_dispatch_assignment("device-1", "L", browser_back))
        self.assertFalse(self.service._should_dispatch_assignment("device-1", "L", browser_back))
        self.assertTrue(self.service._should_dispatch_assignment("device-1", "R", repeatable_seek))
        self.assertTrue(self.service._should_dispatch_assignment("device-1", "R", repeatable_seek))


if __name__ == "__main__":
    unittest.main()
