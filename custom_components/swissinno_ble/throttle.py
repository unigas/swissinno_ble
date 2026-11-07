"""Limit how often frequently changing diagnostic values are published."""

from __future__ import annotations

from time import monotonic

DIAGNOSTIC_UPDATE_INTERVAL = 60.0


class UpdateThrottle:
    def __init__(self, interval: float = DIAGNOSTIC_UPDATE_INTERVAL) -> None:
        self._interval = interval
        self._last: float | None = None

    def ready(self, now: float | None = None) -> bool:
        now = monotonic() if now is None else now
        if self._last is not None and now - self._last < self._interval:
            return False
        self._last = now
        return True

    def reset(self) -> None:
        self._last = None
