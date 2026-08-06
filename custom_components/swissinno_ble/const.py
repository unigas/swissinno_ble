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


STATUS_IDLE = 0x00
STATUS_ARMED = 0x01
STATUS_TRIGGERED = 0x02
STATUS_KILL = 0x03
STATUS_READY = 0x04
