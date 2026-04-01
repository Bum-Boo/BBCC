from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple


@dataclass(frozen=True)
class ControllerInfo:
    device_id: str
    instance_id: int
    name: str
    guid: str
    is_standard_controller: bool
    standard_mapping: Tuple[Tuple[str, str], ...]
    power_level: str
    axes_count: int
    buttons_count: int
    hats_count: int


@dataclass(frozen=True)
class RawControllerState:
    info: ControllerInfo
    axes: Tuple[float, ...] = field(default_factory=tuple)
    buttons: Tuple[bool, ...] = field(default_factory=tuple)
    hats: Tuple[Tuple[int, int], ...] = field(default_factory=tuple)
    last_updated: Optional[datetime] = None


@dataclass(frozen=True)
class BackendState:
    backend_name: str
    controllers: Tuple[RawControllerState, ...] = field(default_factory=tuple)
    last_updated: Optional[datetime] = None

    @classmethod
    def empty(cls, backend_name: str) -> "BackendState":
        return cls(backend_name=backend_name)


@dataclass(frozen=True)
class BackendLogEvent:
    timestamp: datetime
    message: str

    def format_line(self) -> str:
        return "[{stamp}] {message}".format(
            stamp=self.timestamp.strftime("%H:%M:%S.%f")[:-3],
            message=self.message,
        )


@dataclass(frozen=True)
class BackendUpdate:
    state: BackendState
    events: Tuple[BackendLogEvent, ...] = field(default_factory=tuple)
