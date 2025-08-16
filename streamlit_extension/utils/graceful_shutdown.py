"""Simple graceful shutdown helpers.

This is a lightweight abstraction that mimics the behaviour of a more
sophisticated shutdown handler.  It is intentionally small – the
existing project already contains a comprehensive implementation in the
``monitoring`` package.  This variant exists so that components within
``streamlit_extension`` can depend on a minimal interface during tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List


class ShutdownPhase(Enum):
    STOP_ACCEPTING_REQUESTS = auto()
    DRAIN_CONNECTIONS = auto()
    CLEANUP_RESOURCES = auto()
    FINAL_SHUTDOWN = auto()


@dataclass
class GracefulShutdownHandler:
    """Coordinate a simple shutdown sequence."""

    cleanup_handlers: Dict[str, Callable[[], None]]

    def __init__(self) -> None:
        self.cleanup_handlers = {}
        self._sequence: List[ShutdownPhase] = []

    def register_signal_handlers(self) -> None:  # pragma: no cover - OS interaction
        """Placeholder for installing signal handlers."""
        self._sequence.append(ShutdownPhase.STOP_ACCEPTING_REQUESTS)

    def shutdown_sequence(self) -> List[ShutdownPhase]:
        self._sequence.append(ShutdownPhase.DRAIN_CONNECTIONS)
        self._sequence.append(ShutdownPhase.CLEANUP_RESOURCES)
        self.cleanup_resources()
        self._sequence.append(ShutdownPhase.FINAL_SHUTDOWN)
        return list(self._sequence)

    def cleanup_resources(self) -> None:
        for handler in self.cleanup_handlers.values():
            handler()

    def wait_for_completion(self) -> bool:
        return True

    def add_cleanup_handler(self, name: str, handler: Callable[[], None]) -> None:
        self.cleanup_handlers[name] = handler
