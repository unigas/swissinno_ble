"""Battery reading stabilization for SWISSINNO traps."""

from __future__ import annotations

from math import isfinite


class BatteryStabilizer:
    """Publish a battery value only after consecutive matching readings."""

    def __init__(self, *, required_samples: int = 2, tolerance: float = 0.05) -> None:
        self._required_samples = required_samples
        self._tolerance = tolerance
        self._candidate: float | None = None
        self._candidate_count = 0

    def update(self, value: float | None) -> float | None:
        """Return a stable value, or None while a new value is unconfirmed."""
        if value is None or not isfinite(value) or value <= 0:
            self._candidate = None
            self._candidate_count = 0
            return None

        if (
            self._candidate is None
            or abs(value - self._candidate) > self._tolerance
        ):
            self._candidate = value
            self._candidate_count = 1
            return None

        self._candidate = value
        self._candidate_count += 1
        if self._candidate_count < self._required_samples:
            return None

        return value
