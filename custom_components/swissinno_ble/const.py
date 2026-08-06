DOMAIN = "swissinno_ble"

MANUFACTURER_ID = 3003


def normalized_address(address: str) -> str:
    """Return a stable identifier derived from a Bluetooth address."""
    return address.replace(":", "").replace("-", "").lower()


STATUS_IDLE = 0x00
STATUS_ARMED = 0x01
STATUS_TRIGGERED = 0x02
STATUS_KILL = 0x03
STATUS_READY = 0x04
