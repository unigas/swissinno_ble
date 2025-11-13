"""Bluetooth GATT helper for resetting SWISSINNO traps."""

import logging

from homeassistant.components.bluetooth import async_ble_device_from_address
from bleak_retry_connector import BleakClientWithServiceCache

_LOGGER = logging.getLogger(__name__)

RESET_CHARACTERISTIC_UUID = "02ECC6CD-2B43-4DB5-96E6-EDE92CF8778D"


async def async_reset_trap(hass, address: str) -> None:
    """Reset a SWISSINNO trap by writing 0x00 to the reset characteristic."""

    normalized = address.upper()
    _LOGGER.info("SWISSINNO BLE: Resetting trap at %s", normalized)

    device = async_ble_device_from_address(
        hass,
        normalized,
        connectable=True,
    )

    if not device:
        _LOGGER.error("SWISSINNO BLE: Device %s not found for reset", normalized)
        raise RuntimeError(f"Bluetooth device {normalized} not found")

    try:
        async with BleakClientWithServiceCache(device) as client:
            await client.write_gatt_char(
                RESET_CHARACTERISTIC_UUID,
                b"\x00",
                response=True,
            )
        _LOGGER.info("SWISSINNO BLE: Successfully reset trap %s", normalized)

    except Exception as e:
        _LOGGER.error("SWISSINNO BLE: Reset failed for %s: %s", normalized, e)
        raise
