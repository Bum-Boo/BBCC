from __future__ import annotations

import hashlib
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

import pygame
try:
    import pygame._sdl2.controller as sdl_controller
except Exception:  # pragma: no cover - optional pygame SDL2 controller bridge
    sdl_controller = None

from .base import InputBackend
from .models import BackendLogEvent, BackendState, BackendUpdate, ControllerInfo, RawControllerState

JoystickHandle = Any
ControllerHandle = Any


def _stable_device_id(
    name: str,
    guid: str,
    axes_count: int,
    buttons_count: int,
    hats_count: int,
) -> str:
    normalized_name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "controller"
    if guid:
        digest_source = guid.lower().encode("utf-8")
        prefix = "guid"
    else:
        digest_source = "{name}|{axes}|{buttons}|{hats}".format(
            name=name.lower(),
            axes=axes_count,
            buttons=buttons_count,
            hats=hats_count,
        ).encode("utf-8")
        prefix = normalized_name
    digest = hashlib.sha1(digest_source).hexdigest()[:8]
    return "{prefix}-{digest}".format(prefix=prefix, digest=digest)


class PygameJoystickBackend(InputBackend):
    """SDL2-backed joystick reader for Windows-friendly controller inspection."""

    def __init__(
        self,
        preferred_name_tokens: Tuple[str, ...] = (),
    ) -> None:
        self._backend_name = "pygame / SDL2 joystick"
        self._preferred_name_tokens = tuple(token.lower() for token in preferred_name_tokens)
        self._started = False
        self._joysticks: Dict[int, JoystickHandle] = {}
        self._controllers: Dict[int, ControllerHandle] = {}
        self._last_axis_values: Dict[Tuple[int, int], float] = {}
        self._last_button_values: Dict[Tuple[int, int], bool] = {}
        self._last_hat_values: Dict[Tuple[int, int], Tuple[int, int]] = {}
        self._pending_events: List[BackendLogEvent] = []
        self._controller_eventstate_disabled = False
        self._sdl_controller_available = sdl_controller is not None

    def start(self) -> BackendState:
        if self._started:
            return self._build_state()

        pygame.init()
        if not pygame.display.get_init():
            pygame.display.init()
        self._ensure_hidden_display()

        if not pygame.joystick.get_init():
            pygame.joystick.init()
        if sdl_controller is not None:
            try:
                if not sdl_controller.get_init():
                    sdl_controller.init()
                sdl_controller.set_eventstate(False)
                self._controller_eventstate_disabled = True
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                self._log(
                    "SDL2 controller bridge setup error ({exc_type}): {error}".format(
                        exc_type=exc.__class__.__name__,
                        error=exc,
                    )
                )

        self._refresh_connected_joysticks()
        self._safe_event_get("start")
        self._log_startup_diagnostics()
        self._started = True
        return self._build_state()

    def poll(self) -> BackendUpdate:
        if not self._started:
            return BackendUpdate(state=self.start())

        backend_events: List[BackendLogEvent] = self._drain_pending_events()

        for event in self._safe_event_get("poll"):
            event_type = getattr(event, "type", None)

            if event_type == pygame.JOYDEVICEADDED:
                joystick = pygame.joystick.Joystick(event.device_index)
                instance_id = joystick.get_instance_id()
                self._joysticks[instance_id] = joystick
                controller = self._open_controller_for_device_index(int(event.device_index))
                if controller is not None:
                    self._controllers[instance_id] = controller
                backend_events.append(
                    self._log_event(
                        "Controller connected: {name} (instance {instance_id})".format(
                            name=joystick.get_name(),
                            instance_id=instance_id,
                        )
                    )
                )
                continue

            if event_type == pygame.JOYDEVICEREMOVED:
                instance_id = int(event.instance_id)
                joystick = self._joysticks.pop(instance_id, None)
                controller = self._controllers.pop(instance_id, None)
                name = joystick.get_name() if joystick is not None else "Unknown controller"
                if joystick is not None:
                    self._safe_close_joystick(joystick)
                if controller is not None:
                    self._safe_close_controller(controller)
                self._forget_instance(instance_id)
                backend_events.append(
                    self._log_event(
                        "Controller disconnected: {name} (instance {instance_id})".format(
                            name=name,
                            instance_id=instance_id,
                        )
                    )
                )
                continue

            if event_type == pygame.JOYAXISMOTION:
                event_instance_id = int(event.instance_id)
                axis_value = round(float(event.value), 3)
                cache_key = (event_instance_id, int(event.axis))
                if self._last_axis_values.get(cache_key) != axis_value:
                    self._last_axis_values[cache_key] = axis_value
                    backend_events.append(
                        self._log_event(
                            "[{instance_id}] axis {axis_index} -> {axis_value:+0.3f}".format(
                                instance_id=event_instance_id,
                                axis_index=int(event.axis),
                                axis_value=axis_value,
                            )
                        )
                    )
                continue

            if event_type == pygame.JOYBUTTONDOWN:
                event_instance_id = int(event.instance_id)
                button_index = int(event.button)
                cache_key = (event_instance_id, button_index)
                if self._last_button_values.get(cache_key) is not True:
                    self._last_button_values[cache_key] = True
                    backend_events.append(
                        self._log_event(
                            "[{instance_id}] button {button_index} down".format(
                                instance_id=event_instance_id,
                                button_index=button_index,
                            )
                        )
                    )
                continue

            if event_type == pygame.JOYBUTTONUP:
                event_instance_id = int(event.instance_id)
                button_index = int(event.button)
                cache_key = (event_instance_id, button_index)
                if self._last_button_values.get(cache_key) is not False:
                    self._last_button_values[cache_key] = False
                    backend_events.append(
                        self._log_event(
                            "[{instance_id}] button {button_index} up".format(
                                instance_id=event_instance_id,
                                button_index=button_index,
                            )
                        )
                    )
                continue

            if event_type == pygame.JOYHATMOTION:
                event_instance_id = int(event.instance_id)
                hat_index = int(event.hat)
                hat_value = (int(event.value[0]), int(event.value[1]))
                cache_key = (event_instance_id, hat_index)
                if self._last_hat_values.get(cache_key) != hat_value:
                    self._last_hat_values[cache_key] = hat_value
                    backend_events.append(
                        self._log_event(
                            "[{instance_id}] hat {hat_index} -> {hat_value}".format(
                                instance_id=event_instance_id,
                                hat_index=hat_index,
                                hat_value=hat_value,
                            )
                        )
                    )
                continue

        backend_events.extend(self._drain_pending_events())
        return BackendUpdate(state=self._build_state(), events=tuple(backend_events))

    def stop(self) -> None:
        if not self._started:
            return

        for joystick in list(self._joysticks.values()):
            self._safe_close_joystick(joystick)
        for controller in list(self._controllers.values()):
            self._safe_close_controller(controller)

        self._joysticks.clear()
        self._controllers.clear()
        self._last_axis_values.clear()
        self._last_button_values.clear()
        self._last_hat_values.clear()
        self._pending_events.clear()

        if pygame.joystick.get_init():
            pygame.joystick.quit()
        if sdl_controller is not None and sdl_controller.get_init():
            sdl_controller.quit()
        if pygame.display.get_init():
            pygame.display.quit()
        pygame.quit()
        self._started = False

    def _ensure_hidden_display(self) -> None:
        if pygame.display.get_surface() is not None:
            return

        try:
            pygame.display.set_mode((1, 1), flags=getattr(pygame, "HIDDEN", 0))
        except pygame.error:
            pass

    def _safe_event_get(self, phase: str) -> List[Any]:
        try:
            return list(pygame.event.get())
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            self._log(
                "pygame.event.get() failed during {phase} ({exc_type}): {error}; controller_events_disabled={disabled}".format(
                    phase=phase,
                    exc_type=exc.__class__.__name__,
                    error=exc,
                    disabled=self._controller_eventstate_disabled,
                )
            )
            return []

    def _drain_pending_events(self) -> List[BackendLogEvent]:
        pending = list(self._pending_events)
        self._pending_events.clear()
        return pending

    def _log(self, message: str) -> None:
        self._pending_events.append(BackendLogEvent(timestamp=datetime.now(), message=message))

    def _controller_eventstate_status(self) -> str:
        if sdl_controller is None:
            return "unavailable"
        try:
            return "disabled" if not sdl_controller.get_eventstate() else "enabled"
        except Exception:
            return "unknown"

    def _controller_count(self) -> str:
        try:
            return str(getattr(sdl_controller, "get_count", lambda: "n/a")()) if sdl_controller is not None else "n/a"
        except Exception:
            return "unknown"

    def _log_startup_diagnostics(self) -> None:
        pygame_version = getattr(pygame, "version", None)
        version_text = getattr(pygame_version, "ver", "unknown")
        self._log(
            "Backend startup -> python={python} pygame={pygame} sdl2_controller={sdl2} controller_eventstate={eventstate} joystick_count={joysticks} controller_count={controllers}".format(
                python=sys.version.split()[0],
                pygame=version_text,
                sdl2=bool(self._sdl_controller_available),
                eventstate=self._controller_eventstate_status(),
                joysticks=pygame.joystick.get_count(),
                controllers=self._controller_count(),
            )
        )

    def _refresh_connected_joysticks(self) -> None:
        self._joysticks.clear()
        self._controllers.clear()
        for device_index in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(device_index)
            instance_id = joystick.get_instance_id()
            self._joysticks[instance_id] = joystick
            controller = self._open_controller_for_device_index(device_index)
            if controller is not None:
                self._controllers[instance_id] = controller

    def _build_state(self) -> BackendState:
        raw_states = tuple(
            self._build_raw_state(instance_id, joystick)
            for instance_id, joystick in self._sorted_joystick_items()
        )
        return BackendState(
            backend_name=self._backend_name,
            controllers=raw_states,
            last_updated=datetime.now(),
        )

    def _sorted_joystick_items(self) -> List[Tuple[int, JoystickHandle]]:
        def sort_key(item: Tuple[int, JoystickHandle]) -> Tuple[int, int]:
            instance_id, joystick = item
            name = joystick.get_name().lower()
            priority = 0 if any(token in name for token in self._preferred_name_tokens) else 1
            return (priority, instance_id)

        return sorted(self._joysticks.items(), key=sort_key)

    def _build_raw_state(self, instance_id: int, joystick: JoystickHandle) -> RawControllerState:
        info = self._build_controller_info(instance_id, joystick, self._controllers.get(instance_id))
        return RawControllerState(
            info=info,
            axes=tuple(float(joystick.get_axis(index)) for index in range(joystick.get_numaxes())),
            buttons=tuple(
                bool(joystick.get_button(index)) for index in range(joystick.get_numbuttons())
            ),
            hats=tuple(
                (int(value[0]), int(value[1]))
                for value in (joystick.get_hat(index) for index in range(joystick.get_numhats()))
            ),
            last_updated=datetime.now(),
        )

    def _build_controller_info(
        self,
        instance_id: int,
        joystick: JoystickHandle,
        controller: Optional[ControllerHandle],
    ) -> ControllerInfo:
        power_level = "unknown"
        if hasattr(joystick, "get_power_level"):
            try:
                power_level = str(joystick.get_power_level())
            except pygame.error:
                power_level = "unknown"

        guid = ""
        if hasattr(joystick, "get_guid"):
            try:
                guid = str(joystick.get_guid())
            except pygame.error:
                guid = ""

        axes_count = int(joystick.get_numaxes())
        buttons_count = int(joystick.get_numbuttons())
        hats_count = int(joystick.get_numhats())
        device_id = _stable_device_id(
            str(joystick.get_name()),
            guid,
            axes_count,
            buttons_count,
            hats_count,
        )
        standard_mapping: Tuple[Tuple[str, str], ...] = ()
        is_standard_controller = controller is not None
        if controller is not None:
            try:
                mapping_dict = controller.get_mapping() or {}
            except pygame.error:
                mapping_dict = {}
            standard_mapping = tuple(
                sorted(
                    (str(key), str(value))
                    for key, value in mapping_dict.items()
                    if value is not None and str(value)
                )
            )

        return ControllerInfo(
            device_id=device_id,
            instance_id=instance_id,
            name=str(joystick.get_name()),
            guid=guid,
            is_standard_controller=is_standard_controller,
            standard_mapping=standard_mapping,
            power_level=power_level,
            axes_count=axes_count,
            buttons_count=buttons_count,
            hats_count=hats_count,
        )

    def _safe_close_joystick(self, joystick: JoystickHandle) -> None:
        try:
            joystick.quit()
        except pygame.error:
            pass

    def _safe_close_controller(self, controller: ControllerHandle) -> None:
        try:
            controller.quit()
        except pygame.error:
            pass

    def _open_controller_for_device_index(self, device_index: int) -> Optional[ControllerHandle]:
        if sdl_controller is None or not sdl_controller.get_init():
            return None
        try:
            if not sdl_controller.is_controller(device_index):
                return None
            return sdl_controller.Controller(device_index)
        except pygame.error:
            return None

    def _forget_instance(self, instance_id: int) -> None:
        self._last_axis_values = {
            key: value for key, value in self._last_axis_values.items() if key[0] != instance_id
        }
        self._last_button_values = {
            key: value for key, value in self._last_button_values.items() if key[0] != instance_id
        }
        self._last_hat_values = {
            key: value for key, value in self._last_hat_values.items() if key[0] != instance_id
        }

    def _log_event(self, message: str) -> BackendLogEvent:
        return BackendLogEvent(timestamp=datetime.now(), message=message)
