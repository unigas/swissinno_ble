"""Share the latest trap observations between entity platforms."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class TrapObservation:
    """Values decoded from one real Bluetooth advertisement."""

    rssi: int | None
    battery_v: float | None
    legacy_trap_ids: tuple[str, ...]
    available: bool = True


ObservationListener = Callable[[str, TrapObservation], None]


class TrapObservationCoordinator:
    """Cache observations and replay them to late platform listeners."""

    def __init__(self) -> None:
        self._latest: dict[str, TrapObservation] = {}
        self._listeners: set[ObservationListener] = set()

    def update(self, trap_id: str, observation: TrapObservation) -> None:
        """Store and publish an observation."""
        self._latest[trap_id] = observation
        for listener in tuple(self._listeners):
            listener(trap_id, observation)

    def set_unavailable(self, trap_id: str) -> None:
        """Mark a previously observed trap unavailable."""
        if (observation := self._latest.get(trap_id)) is None:
            return
        self.update(trap_id, replace(observation, available=False))

    def register_listener(self, listener: ObservationListener) -> Callable[[], None]:
        """Register a listener and immediately replay the latest observations."""
        self._listeners.add(listener)
        for trap_id, observation in tuple(self._latest.items()):
            listener(trap_id, observation)

        def remove_listener() -> None:
            self._listeners.discard(listener)

        return remove_listener
