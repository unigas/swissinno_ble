"""Helpers for rejecting stale Bluetooth history after integration setup."""


def is_fresh_advertisement(advertisement_time: float, accept_after: float) -> bool:
    """Return whether an advertisement was received during the current setup."""
    return advertisement_time >= accept_after
