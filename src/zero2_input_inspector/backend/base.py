from __future__ import annotations

from abc import ABC, abstractmethod

from .models import BackendState, BackendUpdate


class InputBackend(ABC):
    """Abstract controller backend contract."""

    @abstractmethod
    def start(self) -> BackendState:
        """Initialize the backend and return the first available state."""

    @abstractmethod
    def poll(self) -> BackendUpdate:
        """Read the latest input state and any new backend events."""

    @abstractmethod
    def stop(self) -> None:
        """Release any controller resources owned by the backend."""
