DOMAIN = "swissinno_ble"

MANUFACTURER_ID = 3003
SERVICE_UUID = "0000fcd6-0000-1000-8000-00805f9b34fb"

# Home Assistant treats a missing ``connectable`` matcher as ``True``. BLE
# proxies can report trap advertisements as non-connectable even though the
# manufacturer data is still usable, so accept advertisements from both kinds
# of scanners.
ADVERTISEMENT_MATCHER = {
    "manufacturer_id": MANUFACTURER_ID,
    "service_uuid": SERVICE_UUID,
    "connectable": False,
}

CONNECTABLE_ADVERTISEMENT_MATCHER = {
    **ADVERTISEMENT_MATCHER,
    "connectable": True,
}


def normalized_address(address: str) -> str:
    """Return a stable identifier derived from a Bluetooth address."""
    return address.replace(":", "").replace("-", "").lower()


def entity_unique_id(address: str, suffix: str | None = None) -> str:
    """Return a stable entity unique ID derived from the Bluetooth address."""
    unique_id = f"swissinno_trap_{normalized_address(address)}"
    return f"{unique_id}_{suffix}" if suffix else unique_id


def legacy_unique_ids(
    trap_ids: str | tuple[str, ...], suffix: str | None = None
) -> tuple[str, ...]:
    """Return payload-based unique IDs used before version 1.0.16."""
    identifiers: list[str] = []
    for trap_id in (trap_ids,) if isinstance(trap_ids, str) else trap_ids:
        for value in (trap_id, trap_id.lower()):
            identifier = f"swissinno_trap_{value}"
            if identifier not in identifiers:
                identifiers.append(identifier)
    if suffix:
        return tuple(f"{identifier}_{suffix}" for identifier in identifiers)
    return tuple(identifiers)


# Both observed advertisement families expose a binary ready/triggered flag,
# but at different byte offsets. These are not the values stored in the stable
# trap ID at payload[2:6].
STATUS_READY = 0x00
STATUS_TRIGGERED = 0x01
