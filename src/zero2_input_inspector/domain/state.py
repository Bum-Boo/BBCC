from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from ..backend.models import RawControllerState
from .profiles import AppProfile, DeviceProfile, Preset


@dataclass(frozen=True)
class LogicalControlState:
    control: str
    value: float
    is_active: bool
    source: str


@dataclass(frozen=True)
class NormalizedControllerState:
    device_id: str
    device_family_id: str
    device_title: str
    layout_name: str
    diagram_kind: str
    has_exact_diagram: bool
    has_canonical_mapping: bool
    resolution_source: str
    resolution_trace: Tuple[str, ...]
    mapping_origin: str
    visible_controls: Tuple[str, ...]
    control_labels: Dict[str, str]
    controls: Dict[str, LogicalControlState]
    left_stick: Tuple[float, float] = (0.0, 0.0)
    right_stick: Tuple[float, float] = (0.0, 0.0)
    deadzone: float = 0.25
    threshold: float = 0.55


@dataclass(frozen=True)
class MappingRow:
    control: str
    button_name: str
    shortcut: str
    label: str
    is_active: bool
    action_kind: str = "keyboard"
    action_text: str = ""
    is_system_action: bool = False
    system_text: str = ""


@dataclass(frozen=True)
class DeviceListEntry:
    device_id: str
    display_name: str
    subtitle: str
    is_connected: bool
    is_selected: bool


@dataclass(frozen=True)
class UiSnapshot:
    backend_name: str
    current_process_name: str
    selected_language: str
    selected_theme: str
    has_connected_devices: bool
    focused_control: str
    selected_device_id: str
    device_entries: Tuple[DeviceListEntry, ...]
    selected_device_profile: Optional[DeviceProfile]
    selected_app_profile: Optional[AppProfile]
    selected_preset: Optional[Preset]
    raw_state: Optional[RawControllerState]
    normalized_state: Optional[NormalizedControllerState]
    mapping_rows: Tuple[MappingRow, ...]
    logs: Tuple[str, ...]
    available_languages: Tuple[Tuple[str, str], ...]
    auto_start_enabled: bool
