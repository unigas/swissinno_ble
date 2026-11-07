"""Bind each trap's payload ID to the first BLE address that claimed it."""

from __future__ import annotations

import logging
from collections.abc import Callable

_LOGGER = logging.getLogger(__name__)

IdentityStorage = dict[str, str]


def identities_from_storage(data: object) -> IdentityStorage:
    if not isinstance(data, dict):
        return {}
    return {
        k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)
    }


class TrapIdentityMap:
    """Bind payload IDs to the first address seen."""

    def __init__(
        self, data: IdentityStorage, save: Callable[[IdentityStorage], None]
    ) -> None:
        self._map = dict(data)
        self._save = save

    def resolve(self, payload_id: str, observed: str) -> str | None:
        if (canonical := self._map.get(payload_id)) is None:
            if observed in self._map.values():
                _LOGGER.debug(
                    "Ignoring payload %s at address %s already claimed by another trap",
                    payload_id,
                    observed,
                )
                return None
            self._map[payload_id] = observed
            self._save(dict(self._map))
            return observed
        if canonical != observed:
            _LOGGER.debug(
                "Trap payload %s seen as %s; using canonical %s",
                payload_id,
                observed,
                canonical,
            )
        return canonical
