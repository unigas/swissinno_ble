"""Share the latest trap observations between entity platforms."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime


@dataclass(frozen=True)
class TrapObservation:
    """Values decoded from one real Bluetooth advertisement."""

    rssi: int | None
    battery_v: float | None
    legacy_trap_ids: tuple[str, ...]
    last_seen: datetime | None = None
    last_triggered: datetime | None = None
    trigger_count: int = 0
    available: bool = True


@dataclass(frozen=True)
class TriggerHistory:
    """Persisted history for confirmed trap transitions."""

    last_triggered: datetime | None = None
    trigger_count: int = 0


TriggerHistoryStorage = dict[str, dict[str, int | str | None]]
TriggerHistorySaveCallback = Callable[[TriggerHistoryStorage], None]


def trigger_history_from_storage(data: object) -> dict[str, TriggerHistory]:
    """Validate and deserialize trigger history from Home Assistant storage."""
    if not isinstance(data, dict):
        return {}

    history: dict[str, TriggerHistory] = {}
    for trap_id, values in data.items():
        if not isinstance(trap_id, str) or not isinstance(values, dict):
            continue

        count = values.get("trigger_count", 0)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            continue

        last_triggered = None
        timestamp = values.get("last_triggered")
        if isinstance(timestamp, str):
            try:
                last_triggered = datetime.fromisoformat(timestamp)
            except ValueError:
                continue
            if last_triggered.tzinfo is None:
                last_triggered = last_triggered.replace(tzinfo=UTC)

        history[trap_id] = TriggerHistory(last_triggered, count)
    return history


def trigger_history_to_storage(
    history: dict[str, TriggerHistory],
) -> TriggerHistoryStorage:
    """Serialize trigger history for Home Assistant storage."""
    return {
        trap_id: {
            "last_triggered": (
                values.last_triggered.isoformat() if values.last_triggered else None
            ),
            "trigger_count": values.trigger_count,
        }
        for trap_id, values in history.items()
    }


ObservationListener = Callable[[str, TrapObservation], None]


class TrapObservationCoordinator:
    """Cache observations and replay them to late platform listeners."""

    def __init__(
        self,
        trigger_history: dict[str, TriggerHistory] | None = None,
        save_trigger_history: TriggerHistorySaveCallback | None = None,
    ) -> None:
        self._latest: dict[str, TrapObservation] = {}
        self._listeners: set[ObservationListener] = set()
        self._trigger_history = dict(trigger_history or {})
        self._save_trigger_history = save_trigger_history
        self._runtime_states: dict[str, bool] = {}

    def update(
        self,
        trap_id: str,
        observation: TrapObservation,
        *,
        is_tripped: bool | None = None,
    ) -> None:
        """Store and publish an observation."""
        history = self._trigger_history.get(trap_id, TriggerHistory())
        previous_state = self._runtime_states.get(trap_id)

        if previous_state is False and is_tripped is True:
            history = TriggerHistory(
                last_triggered=observation.last_seen or datetime.now(UTC),
                trigger_count=history.trigger_count + 1,
            )
            self._trigger_history[trap_id] = history
            if self._save_trigger_history:
                self._save_trigger_history(
                    trigger_history_to_storage(self._trigger_history)
                )

        # Unknown status must not break an otherwise confirmed transition.
        if is_tripped is not None:
            self._runtime_states[trap_id] = is_tripped

        observation = replace(
            observation,
            last_triggered=history.last_triggered,
            trigger_count=history.trigger_count,
        )
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
