import logging
from datetime import datetime, timedelta

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_register_callback,
    BluetoothScanningMode,
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, MANUFACTURER_ID
from .decoder import decode_frame

_LOGGER = logging.getLogger(__name__)

LAST_SEEN_TIMEOUT = timedelta(minutes=30)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up BLE battery + RSSI sensors."""
    _LOGGER.info("SWISSINNO BLE: Initializing battery + RSSI sensors")

    battery_sensors = {}
    rssi_sensors = {}

    async def update_sensors(trap_id, address, rssi, battery_v):
        """Update HA sensor entities after binary sensor detection."""
        if trap_id in battery_sensors:
            battery_sensors[trap_id].update_value(battery_v)
        else:
            sensor = SwissinnoBatterySensor(address, trap_id, battery_v)
            battery_sensors[trap_id] = sensor
            async_add_entities([sensor])

        if trap_id in rssi_sensors:
            rssi_sensors[trap_id].update_value(rssi)
        else:
            sensor = SwissinnoRSSISensor(address, trap_id, rssi)
            rssi_sensors[trap_id] = sensor
            async_add_entities([sensor])

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["update_sensors"] = update_sensors


class SwissinnoBatterySensor(SensorEntity):
    """Battery voltage sensor."""

    device_class = "voltage"
    native_unit_of_measurement = "V"

    def __init__(self, address, trap_id, battery_v):
        self._attr_name = f"SWISSINNO Trap {trap_id} Battery"
        self._attr_unique_id = f"swissinno_trap_{trap_id}_battery"
        self._attr_native_value = battery_v
        self._last_seen = datetime.utcnow()

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, trap_id)},
            manufacturer="SWISSINNO",
            name=f"SWISSINNO Trap {trap_id}",
        )

    def update_value(self, battery_v):
        self._attr_native_value = battery_v
        self._last_seen = datetime.utcnow()
        self.async_write_ha_state()


class SwissinnoRSSISensor(SensorEntity):
    """RSSI sensor."""

    native_unit_of_measurement = "dBm"

    def __init__(self, address, trap_id, rssi):
        self._attr_name = f"SWISSINNO Trap {trap_id} RSSI"
        self._attr_unique_id = f"swissinno_trap_{trap_id}_rssi"
        self._attr_native_value = rssi
        self._last_seen = datetime.utcnow()

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, trap_id)},
            manufacturer="SWISSINNO",
            name=f"SWISSINNO Trap {trap_id}",
        )

    def update_value(self, rssi):
        self._attr_native_value = rssi
        self._last_seen = datetime.utcnow()
        self.async_write_ha_state()
