from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

from ..backend.models import RawControllerState
from ..domain.controls import (
    CONTROL_ORDER,
    DPAD_DOWN,
    DPAD_LEFT,
    DPAD_RIGHT,
    DPAD_UP,
    LEFT_STICK_DOWN,
    LEFT_STICK_LEFT,
    LEFT_STICK_RIGHT,
    LEFT_STICK_UP,
    LEFT_TRIGGER,
    RIGHT_STICK_DOWN,
    RIGHT_STICK_LEFT,
    RIGHT_STICK_RIGHT,
    RIGHT_STICK_UP,
    RIGHT_TRIGGER,
)
from ..domain.profiles import DeviceProfile
from ..domain.state import LogicalControlState, NormalizedControllerState
from .device_registry import DeviceRegistry
from .device_templates import DeviceTemplate, RawFallbackLayout, ZERO2_TEMPLATE, XBOX_TEMPLATE

MAPPING_TOKEN_RE = re.compile(r"^(?P<sign>[+-]?)(?P<kind>[abh])(?P<index>\d+)(?:\.(?P<hat>\d+))?(?P<invert>~)?$")


class InputNormalizer:
    def __init__(
        self,
        device_registry: Optional[DeviceRegistry] = None,
        deadzone: float = 0.25,
        threshold: float = 0.55,
    ) -> None:
        self._device_registry = device_registry or DeviceRegistry()
        self._deadzone = deadzone
        self._threshold = threshold

    @property
    def device_registry(self) -> DeviceRegistry:
        return self._device_registry

    def describe_saved_device(self, device_profile: DeviceProfile):
        return self._device_registry.resolve_saved_profile(device_profile)

    def normalize(
        self,
        raw_state: RawControllerState,
        saved_device: Optional[DeviceProfile] = None,
    ) -> NormalizedControllerState:
        resolved_family = self._device_registry.resolve_runtime(raw_state.info, saved_device)
        template = resolved_family.template
        controls = self._empty_controls()
        mapping_by_control: Dict[str, str] = {}
        mapping_origin = ""

        standard_mapping = dict(raw_state.info.standard_mapping)
        if standard_mapping and template.standard_control_map:
            mapping_by_control = self._canonicalize_standard_mapping(template, standard_mapping)
            if mapping_by_control:
                mapping_origin = "SDL standard mapping"

        if (
            not mapping_by_control
            and template.raw_fallback is not None
            and template.family_id in {ZERO2_TEMPLATE.family_id, XBOX_TEMPLATE.family_id}
        ):
            mapping_by_control = self._raw_fallback_mapping(template.raw_fallback)
            if mapping_by_control:
                mapping_origin = "{title} raw template".format(title=template.title)

        for control, mapping_token in mapping_by_control.items():
            controls[control] = self._resolve_control_state(raw_state, control, mapping_token)

        left_stick = self._raw_stick_vector(raw_state, template.raw_fallback.left_stick_axes if template.raw_fallback else None)
        right_stick = self._raw_stick_vector(raw_state, template.raw_fallback.right_stick_axes if template.raw_fallback else None)
        visible_controls = self._visible_controls(
            template.visible_controls,
            mapping_by_control,
            template.has_exact_diagram,
            template.show_all_controls_when_unverified,
        )
        return NormalizedControllerState(
            device_id=raw_state.info.device_id,
            device_family_id=template.family_id,
            device_title=template.title,
            layout_name=template.title,
            diagram_kind=template.diagram_kind,
            has_exact_diagram=template.has_exact_diagram,
            has_canonical_mapping=bool(mapping_by_control),
            resolution_source=resolved_family.source,
            resolution_trace=resolved_family.trace,
            mapping_origin=mapping_origin,
            visible_controls=visible_controls,
            control_labels=dict(template.control_labels),
            controls=controls,
            left_stick=left_stick,
            right_stick=right_stick,
            deadzone=self._deadzone,
            threshold=self._threshold,
        )

    def _empty_controls(self) -> Dict[str, LogicalControlState]:
        return {
            control: LogicalControlState(
                control=control,
                value=0.0,
                is_active=False,
                source="-",
            )
            for control in CONTROL_ORDER
        }

    def _canonicalize_standard_mapping(
        self,
        template: DeviceTemplate,
        standard_mapping: Dict[str, str],
    ) -> Dict[str, str]:
        mapping_by_control: Dict[str, str] = {}
        for mapping_key, control in template.standard_control_map.items():
            mapping_token = str(standard_mapping.get(mapping_key, "")).strip()
            if mapping_token:
                mapping_by_control[control] = mapping_token

        for axis_key, (negative_control, positive_control) in template.standard_axis_map.items():
            axis_token = str(standard_mapping.get(axis_key, "")).strip()
            if not axis_token:
                continue
            mapping_by_control.setdefault(negative_control, self._directional_axis_token(axis_token, negative=True))
            mapping_by_control.setdefault(positive_control, self._directional_axis_token(axis_token, negative=False))

        dpad_axes = template.raw_fallback.standard_dpad_axes if template.raw_fallback else None
        if dpad_axes is not None:
            x_axis_key, y_axis_key = dpad_axes
            x_axis_token = str(standard_mapping.get(x_axis_key, "")).strip()
            y_axis_token = str(standard_mapping.get(y_axis_key, "")).strip()
            if x_axis_token:
                mapping_by_control.setdefault(DPAD_LEFT, self._directional_axis_token(x_axis_token, negative=True))
                mapping_by_control.setdefault(DPAD_RIGHT, self._directional_axis_token(x_axis_token, negative=False))
            if y_axis_token:
                mapping_by_control.setdefault(DPAD_UP, self._directional_axis_token(y_axis_token, negative=True))
                mapping_by_control.setdefault(DPAD_DOWN, self._directional_axis_token(y_axis_token, negative=False))
        return mapping_by_control

    def _raw_fallback_mapping(self, raw_fallback: RawFallbackLayout) -> Dict[str, str]:
        mapping_by_control = {
            control: "b{index}".format(index=index)
            for index, control in raw_fallback.button_map.items()
        }
        for axis_index, control in raw_fallback.trigger_axes.items():
            mapping_by_control[control] = "a{index}".format(index=axis_index)

        for axis_pair, controls in (
            (raw_fallback.left_stick_axes, (LEFT_STICK_LEFT, LEFT_STICK_RIGHT, LEFT_STICK_UP, LEFT_STICK_DOWN)),
            (raw_fallback.right_stick_axes, (RIGHT_STICK_LEFT, RIGHT_STICK_RIGHT, RIGHT_STICK_UP, RIGHT_STICK_DOWN)),
        ):
            if axis_pair is None:
                continue
            axis_x, axis_y = axis_pair
            left_control, right_control, up_control, down_control = controls
            mapping_by_control.setdefault(left_control, "-a{index}".format(index=axis_x))
            mapping_by_control.setdefault(right_control, "+a{index}".format(index=axis_x))
            mapping_by_control.setdefault(up_control, "-a{index}".format(index=axis_y))
            mapping_by_control.setdefault(down_control, "+a{index}".format(index=axis_y))

        if raw_fallback.dpad_hat_index is not None:
            mapping_by_control.setdefault(DPAD_UP, "h{index}.1".format(index=raw_fallback.dpad_hat_index))
            mapping_by_control.setdefault(DPAD_RIGHT, "h{index}.2".format(index=raw_fallback.dpad_hat_index))
            mapping_by_control.setdefault(DPAD_DOWN, "h{index}.4".format(index=raw_fallback.dpad_hat_index))
            mapping_by_control.setdefault(DPAD_LEFT, "h{index}.8".format(index=raw_fallback.dpad_hat_index))
        elif raw_fallback.dpad_axis_pair is not None:
            axis_x, axis_y = raw_fallback.dpad_axis_pair
            mapping_by_control.setdefault(DPAD_LEFT, "-a{index}".format(index=axis_x))
            mapping_by_control.setdefault(DPAD_RIGHT, "+a{index}".format(index=axis_x))
            mapping_by_control.setdefault(DPAD_UP, "-a{index}".format(index=axis_y))
            mapping_by_control.setdefault(DPAD_DOWN, "+a{index}".format(index=axis_y))
        return mapping_by_control

    def _raw_stick_vector(
        self,
        raw_state: RawControllerState,
        axis_pair: Optional[Tuple[int, int]],
    ) -> Tuple[float, float]:
        if axis_pair is None:
            return (0.0, 0.0)
        axis_x, axis_y = axis_pair
        x_value = raw_state.axes[axis_x] if axis_x < len(raw_state.axes) else 0.0
        y_value = raw_state.axes[axis_y] if axis_y < len(raw_state.axes) else 0.0
        return (float(x_value), float(-y_value))

    def _visible_controls(
        self,
        preferred_controls: Tuple[str, ...],
        mapping_by_control: Dict[str, str],
        has_exact_diagram: bool,
        show_all_controls_when_unverified: bool,
    ) -> Tuple[str, ...]:
        if has_exact_diagram or show_all_controls_when_unverified:
            return preferred_controls
        if not mapping_by_control:
            return ()
        return tuple(control for control in preferred_controls if control in mapping_by_control)

    def _directional_axis_token(self, mapping_token: str, *, negative: bool) -> str:
        base_token = mapping_token.lstrip("+-")
        sign = "-" if negative else "+"
        return "{sign}{token}".format(sign=sign, token=base_token)

    def _resolve_control_state(
        self,
        raw_state: RawControllerState,
        control: str,
        mapping_token: str,
    ) -> LogicalControlState:
        parsed = self._parse_mapping_token(mapping_token)
        if parsed is None:
            return LogicalControlState(control=control, value=0.0, is_active=False, source=mapping_token)

        kind, index, direction, invert = parsed
        if kind == "b":
            pressed = index < len(raw_state.buttons) and bool(raw_state.buttons[index])
            return LogicalControlState(
                control=control,
                value=1.0 if pressed else 0.0,
                is_active=pressed,
                source="Button {index}".format(index=index),
            )

        if kind == "h":
            hat_value = raw_state.hats[index] if index < len(raw_state.hats) else (0, 0)
            is_active = self._hat_matches(hat_value, direction)
            return LogicalControlState(
                control=control,
                value=1.0 if is_active else 0.0,
                is_active=is_active,
                source=self._hat_source_label(index, direction),
            )

        axis_value = raw_state.axes[index] if index < len(raw_state.axes) else 0.0
        if invert:
            axis_value = -axis_value

        if direction == -1:
            return self._digital_axis_state(
                control=control,
                value=axis_value,
                active_when="negative",
                source="Axis {index}-".format(index=index),
            )
        if direction == 1:
            return self._digital_axis_state(
                control=control,
                value=axis_value,
                active_when="positive",
                source="Axis {index}+".format(index=index),
            )
        if control in (LEFT_TRIGGER, RIGHT_TRIGGER):
            return self._trigger_state(
                control=control,
                value=axis_value,
                source="Axis {index}".format(index=index),
            )
        return self._analog_button_state(
            control=control,
            value=axis_value,
            source="Axis {index}".format(index=index),
        )

    def _parse_mapping_token(self, mapping_token: str) -> Optional[Tuple[str, int, int, bool]]:
        match = MAPPING_TOKEN_RE.match(mapping_token.strip())
        if match is None:
            return None

        sign = match.group("sign") or ""
        kind = match.group("kind")
        index = int(match.group("index"))
        hat_code = int(match.group("hat") or "0")
        invert = bool(match.group("invert"))

        if kind == "a":
            direction = -1 if sign == "-" else 1 if sign == "+" else 0
            return kind, index, direction, invert
        if kind == "h":
            return kind, index, hat_code, invert
        return kind, index, 0, invert

    def _hat_matches(self, hat_value: Tuple[int, int], requested_code: int) -> bool:
        current_code = 0
        if hat_value[1] > 0:
            current_code |= 1
        if hat_value[0] > 0:
            current_code |= 2
        if hat_value[1] < 0:
            current_code |= 4
        if hat_value[0] < 0:
            current_code |= 8
        return (current_code & requested_code) == requested_code

    def _hat_source_label(self, hat_index: int, direction_code: int) -> str:
        direction_name = {
            1: "Up",
            2: "Right",
            4: "Down",
            8: "Left",
        }.get(direction_code, str(direction_code))
        return "Hat {index} {direction}".format(index=hat_index, direction=direction_name)

    def _digital_axis_state(
        self,
        control: str,
        value: float,
        active_when: str,
        source: str,
    ) -> LogicalControlState:
        signed_value = self._apply_deadzone(value)
        if active_when == "negative":
            active_value = max(0.0, -signed_value)
        else:
            active_value = max(0.0, signed_value)
        is_active = active_value >= self._threshold
        return LogicalControlState(
            control=control,
            value=active_value if is_active else 0.0,
            is_active=is_active,
            source=source,
        )

    def _trigger_state(self, control: str, value: float, source: str) -> LogicalControlState:
        normalized_value = value
        if normalized_value < 0.0:
            normalized_value = (normalized_value + 1.0) / 2.0
        normalized_value = max(0.0, normalized_value)
        is_active = normalized_value >= self._threshold
        return LogicalControlState(
            control=control,
            value=normalized_value if is_active else 0.0,
            is_active=is_active,
            source=source,
        )

    def _analog_button_state(self, control: str, value: float, source: str) -> LogicalControlState:
        normalized_value = abs(self._apply_deadzone(value))
        is_active = normalized_value >= self._threshold
        return LogicalControlState(
            control=control,
            value=normalized_value if is_active else 0.0,
            is_active=is_active,
            source=source,
        )

    def _apply_deadzone(self, value: float) -> float:
        if abs(value) < self._deadzone:
            return 0.0
        return value
