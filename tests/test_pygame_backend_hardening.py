from __future__ import annotations

import importlib
import sys
import types
import unittest
from unittest.mock import patch


def _install_pygame_stub() -> types.ModuleType:
    pygame = types.ModuleType("pygame")
    pygame.HIDDEN = 0
    pygame.error = RuntimeError
    pygame.version = types.SimpleNamespace(ver="2.6.1")
    pygame.JOYDEVICEADDED = 1541
    pygame.JOYDEVICEREMOVED = 1542
    pygame.JOYAXISMOTION = 1536
    pygame.JOYBUTTONDOWN = 1539
    pygame.JOYBUTTONUP = 1540
    pygame.JOYHATMOTION = 1538
    pygame.init = lambda: None
    pygame.quit = lambda: None

    display = types.SimpleNamespace()
    display._surface = None
    display.get_init = lambda: True
    display.init = lambda: None
    display.get_surface = lambda: display._surface
    display.set_mode = lambda *args, **kwargs: None
    display.quit = lambda: None
    pygame.display = display

    joystick = types.SimpleNamespace()
    joystick._count = 0
    joystick.get_init = lambda: True
    joystick.init = lambda: None
    joystick.quit = lambda: None
    joystick.get_count = lambda: joystick._count

    class _Joystick:
        def __init__(self, device_index: int) -> None:
            self._device_index = device_index

        def get_instance_id(self) -> int:
            return self._device_index

        def get_name(self) -> str:
            return "Xbox Controller"

        def get_numaxes(self) -> int:
            return 0

        def get_numbuttons(self) -> int:
            return 0

        def get_numhats(self) -> int:
            return 0

        def get_axis(self, index: int) -> float:
            return 0.0

        def get_button(self, index: int) -> bool:
            return False

        def get_hat(self, index: int):
            return (0, 0)

        def get_power_level(self) -> str:
            return "unknown"

        def get_guid(self) -> str:
            return ""

    joystick.Joystick = _Joystick
    pygame.joystick = joystick

    event = types.SimpleNamespace()
    event.get = lambda: []
    pygame.event = event

    controller = types.SimpleNamespace()
    controller._init = False
    controller._eventstate = True
    controller._count = 0
    controller.get_init = lambda: controller._init
    controller.init = lambda: setattr(controller, "_init", True)
    controller.quit = lambda: setattr(controller, "_init", False)
    controller.set_eventstate = lambda enabled: setattr(controller, "_eventstate", bool(enabled))
    controller.get_eventstate = lambda: controller._eventstate
    controller.get_count = lambda: controller._count
    controller.is_controller = lambda device_index: True
    controller.Controller = lambda device_index: types.SimpleNamespace(
        get_mapping=lambda: {},
        quit=lambda: None,
    )
    sdl2 = types.ModuleType("pygame._sdl2")
    sdl2.controller = controller
    pygame._sdl2 = sdl2

    sys.modules["pygame"] = pygame
    sys.modules["pygame._sdl2"] = sdl2
    sys.modules["pygame._sdl2.controller"] = controller
    return pygame


class PygameBackendHardeningTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pygame = _install_pygame_stub()
        self.module = importlib.reload(importlib.import_module("zero2_input_inspector.backend.pygame_backend"))

    def test_start_disables_controller_event_posting_and_logs_diagnostics(self) -> None:
        backend = self.module.PygameJoystickBackend()

        state = backend.start()
        update = backend.poll()

        self.assertEqual(state.backend_name, "pygame / SDL2 joystick")
        self.assertEqual(update.state.backend_name, "pygame / SDL2 joystick")
        self.assertFalse(self.pygame._sdl2.controller.get_eventstate())
        self.assertTrue(backend._controller_eventstate_disabled)
        self.assertTrue(any("Backend startup ->" in event.message for event in update.events))
        self.assertTrue(any("controller_eventstate=disabled" in event.message for event in update.events))

    def test_poll_catches_event_queue_exceptions(self) -> None:
        backend = self.module.PygameJoystickBackend()
        backend.start()

        def _raise():
            raise KeyError(0)

        self.pygame.event.get = _raise

        update = backend.poll()

        self.assertEqual(update.state.backend_name, "pygame / SDL2 joystick")
        self.assertTrue(
            any("pygame.event.get() failed during poll" in event.message for event in update.events),
            update.events,
        )
        self.assertTrue(
            any("controller_events_disabled=True" in event.message for event in update.events),
            update.events,
        )


if __name__ == "__main__":
    unittest.main()
