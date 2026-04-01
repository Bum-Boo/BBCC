from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from ..backend.models import ControllerInfo
from ..domain.profiles import DeviceProfile
from .device_templates import (
    DEVICE_TEMPLATES_BY_FAMILY,
    GENERIC_STANDARD_TEMPLATE,
    SUPPORTED_DEVICE_TEMPLATES,
    UNKNOWN_DEVICE_TEMPLATE,
    DeviceTemplate,
)


@dataclass(frozen=True)
class ResolvedDeviceFamily:
    template: DeviceTemplate
    source: str
    trace: Tuple[str, ...]


class DeviceRegistry:
    def __init__(self, templates: Iterable[DeviceTemplate] = SUPPORTED_DEVICE_TEMPLATES) -> None:
        self._templates = tuple(templates)

    def template_for_family(self, family_id: str) -> Optional[DeviceTemplate]:
        return DEVICE_TEMPLATES_BY_FAMILY.get(family_id)

    def shape_signature(
        self,
        *,
        axes_count: int,
        buttons_count: int,
        hats_count: int,
        is_standard_controller: bool,
    ) -> str:
        return "std:{std}|axes:{axes}|buttons:{buttons}|hats:{hats}".format(
            std=int(is_standard_controller),
            axes=axes_count,
            buttons=buttons_count,
            hats=hats_count,
        )

    def shape_signature_from_info(self, info: ControllerInfo) -> str:
        return self.shape_signature(
            axes_count=info.axes_count,
            buttons_count=info.buttons_count,
            hats_count=info.hats_count,
            is_standard_controller=info.is_standard_controller,
        )

    def resolve_runtime(
        self,
        info: ControllerInfo,
        saved_device: Optional[DeviceProfile] = None,
    ) -> ResolvedDeviceFamily:
        shape_signature = self.shape_signature_from_info(info)
        trace: List[str] = [
            "runtime name={name}".format(name=info.name or "-"),
            "guid={guid}".format(guid=info.guid or "-"),
            "shape={shape}".format(shape=shape_signature),
        ]

        saved_match = self._resolve_saved_family(saved_device)
        if saved_match is not None:
            trace.append("saved family={family}".format(family=saved_match.family_id))
            return ResolvedDeviceFamily(saved_match, "saved_family", tuple(trace))

        guid_match = self._match_by_guid(info.guid)
        if guid_match is not None:
            trace.append("guid match={family}".format(family=guid_match.family_id))
            return ResolvedDeviceFamily(guid_match, "guid", tuple(trace))

        name_match = self._match_by_name(info.name, info.is_standard_controller)
        if name_match is not None:
            trace.append("name match={family}".format(family=name_match.family_id))
            return ResolvedDeviceFamily(name_match, "name", tuple(trace))

        shape_match = self._match_by_shape(
            axes_count=info.axes_count,
            buttons_count=info.buttons_count,
            hats_count=info.hats_count,
            is_standard_controller=info.is_standard_controller,
        )
        if shape_match is not None:
            trace.append("shape match={family}".format(family=shape_match.family_id))
            return ResolvedDeviceFamily(shape_match, "shape", tuple(trace))

        if info.is_standard_controller:
            trace.append("SDL standard controller")
            return ResolvedDeviceFamily(GENERIC_STANDARD_TEMPLATE, "standard", tuple(trace))

        trace.append("unknown layout")
        return ResolvedDeviceFamily(UNKNOWN_DEVICE_TEMPLATE, "unknown", tuple(trace))

    def resolve_saved_profile(self, device_profile: DeviceProfile) -> ResolvedDeviceFamily:
        trace: List[str] = [
            "saved name={name}".format(name=device_profile.last_seen_name or device_profile.display_name),
            "saved guid={guid}".format(guid=device_profile.guid or "-"),
            "saved shape={shape}".format(shape=device_profile.shape_signature or "-"),
        ]

        saved_match = self._resolve_saved_family(device_profile)
        if saved_match is not None:
            trace.append("saved family={family}".format(family=saved_match.family_id))
            return ResolvedDeviceFamily(saved_match, "saved_family", tuple(trace))

        guid_match = self._match_by_guid(device_profile.guid)
        if guid_match is not None:
            trace.append("guid match={family}".format(family=guid_match.family_id))
            return ResolvedDeviceFamily(guid_match, "guid", tuple(trace))

        parsed_shape = self._parse_shape_signature(device_profile.shape_signature)
        is_standard_controller = parsed_shape[3] if parsed_shape is not None else False
        name_match = self._match_by_name(
            device_profile.last_seen_name or device_profile.display_name,
            is_standard_controller,
        )
        if name_match is not None:
            trace.append("name match={family}".format(family=name_match.family_id))
            return ResolvedDeviceFamily(name_match, "name", tuple(trace))

        shape_match = self._match_saved_shape(device_profile.shape_signature)
        if shape_match is not None:
            trace.append("shape match={family}".format(family=shape_match.family_id))
            return ResolvedDeviceFamily(shape_match, "shape", tuple(trace))

        trace.append("unknown layout")
        return ResolvedDeviceFamily(UNKNOWN_DEVICE_TEMPLATE, "unknown", tuple(trace))

    def find_matching_profile(
        self,
        *,
        info: ControllerInfo,
        existing_devices: Iterable[DeviceProfile],
    ) -> Optional[DeviceProfile]:
        device_list = list(existing_devices)

        direct_match = next((device for device in device_list if device.device_id == info.device_id), None)
        if direct_match is not None:
            return direct_match

        if info.guid:
            guid_match = next((device for device in device_list if device.guid and device.guid == info.guid), None)
            if guid_match is not None:
                return guid_match

        resolved_family = self.resolve_runtime(info)
        if resolved_family.template.family_id in {"unknown_controller", "standard_controller"}:
            return None

        shape_signature = self.shape_signature_from_info(info)
        family_candidates = [
            device
            for device in device_list
            if device.shape_signature == shape_signature
            and self._saved_or_override_family(device) == resolved_family.template.family_id
        ]
        if len(family_candidates) == 1:
            return family_candidates[0]
        return None

    def _resolve_saved_family(self, device_profile: Optional[DeviceProfile]) -> Optional[DeviceTemplate]:
        if device_profile is None:
            return None
        family_id = self._saved_or_override_family(device_profile)
        if not family_id:
            return None
        return self.template_for_family(family_id)

    def _saved_or_override_family(self, device_profile: DeviceProfile) -> str:
        return device_profile.family_override_id or device_profile.saved_family_id

    def _match_by_guid(self, guid: str) -> Optional[DeviceTemplate]:
        normalized_guid = (guid or "").lower()
        if not normalized_guid:
            return None
        for template in self._templates:
            if any(fragment in normalized_guid for fragment in template.guid_fragments):
                return template
        return None

    def _match_by_name(self, device_name: str, is_standard_controller: bool) -> Optional[DeviceTemplate]:
        normalized_name = (device_name or "").lower()
        if not normalized_name:
            return None
        for template in self._templates:
            if template.name_match_requires_standard_controller and not is_standard_controller:
                continue
            if any(token in normalized_name for token in template.name_tokens):
                return template
        return None

    def _match_by_shape(
        self,
        *,
        axes_count: int,
        buttons_count: int,
        hats_count: int,
        is_standard_controller: bool,
    ) -> Optional[DeviceTemplate]:
        for template in self._templates:
            if not template.allow_shape_only_match:
                continue
            if any(
                pattern.matches(
                    axes_count=axes_count,
                    buttons_count=buttons_count,
                    hats_count=hats_count,
                    is_standard_controller=is_standard_controller,
                )
                for pattern in template.shape_patterns
            ):
                return template
        return None

    def _match_saved_shape(self, shape_signature: str) -> Optional[DeviceTemplate]:
        parsed = self._parse_shape_signature(shape_signature)
        if parsed is None:
            return None
        axes_count, buttons_count, hats_count, is_standard_controller = parsed
        return self._match_by_shape(
            axes_count=axes_count,
            buttons_count=buttons_count,
            hats_count=hats_count,
            is_standard_controller=is_standard_controller,
        )

    def _parse_shape_signature(self, signature: str) -> Optional[Tuple[int, int, int, bool]]:
        if not signature:
            return None
        parts = {}
        for item in signature.split("|"):
            if ":" not in item:
                return None
            key, value = item.split(":", 1)
            parts[key] = value
        try:
            return (
                int(parts["axes"]),
                int(parts["buttons"]),
                int(parts["hats"]),
                bool(int(parts["std"])),
            )
        except (KeyError, TypeError, ValueError):
            return None
