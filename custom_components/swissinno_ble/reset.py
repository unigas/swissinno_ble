"""Bluetooth GATT helper for resetting SWISSINNO traps."""

import logging

from bleak_retry_connector import (
    BleakClientWithServiceCache,
    establish_connection,
)
from homeassistant.components.bluetooth import async_ble_device_from_address

_LOGGER = logging.getLogger(__name__)

RESET_CHARACTERISTIC_UUID = "02ECC6CD-2B43-4DB5-96E6-EDE92CF8778D"


async def async_reset_trap(hass, address: str) -> None:
    """Reset a SWISSINNO trap by writing 0x00 to the reset characteristic."""
    normalized = address.upper()
    _LOGGER.info("SWISSINNO BLE: Resetting trap at %s", normalized)

    device = async_ble_device_from_address(hass, normalized, connectable=True)
    if device is None:
        raise RuntimeError(f"Bluetooth device {normalized} not found")

    client = await establish_connection(
        BleakClientWithServiceCache,
        device,
        device.name or normalized,
    )

    try:
        characteristic = client.services.get_characteristic(RESET_CHARACTERISTIC_UUID)
        if characteristic is None:
            raise RuntimeError(
                f"Reset characteristic {RESET_CHARACTERISTIC_UUID} not found"
            )

        properties = set(characteristic.properties)
        if "write-without-response" in properties:
            response = False
        elif "write" in properties:
            response = True
        else:
            raise RuntimeError(
                f"Reset characteristic is not writable (properties: {sorted(properties)})"
            )

        await client.write_gatt_char(characteristic, b"\x00", response=response)
        _LOGGER.info("SWISSINNO BLE: Successfully reset trap %s", normalized)
    finally:
        await client.disconnect()
