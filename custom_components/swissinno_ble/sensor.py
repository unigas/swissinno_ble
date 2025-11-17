import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

LAST_SEEN_TIMEOUT = timedelta(minutes=30)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Prepare update callback for binary_sensor.py."""
    _LOGGER.info("SWISSINNO BLE: Initializing battery + RSSI sensors")

    battery_sensors: dict[str, SwissinnoBatterySensor] = {}
    rssi_sensors: dict[str, SwissinnoRSSISensor] = {}

    async def update_sensors(trap_id: str, address: str, rssi: int, battery_v: float):
        # Battery
        if trap_id in battery_sensors:
            battery_sensors[trap_id].update_value(battery_v)
        else:
            sensor = SwissinnoBatterySensor(trap_id, battery_v)
            battery_sensors[trap_id] = sensor
            async_add_entities([sensor])

        # RSSI
        if trap_id in rssi_sensors:
            rssi_sensors[trap_id].update_value(rssi)
        else:
            sensor = SwissinnoRSSISensor(trap_id, rssi)
            rssi_sensors[trap_id] = sensor
            async_add_entities([sensor])

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["update_sensors"] = update_sensors


class SwissinnoBatterySensor(SensorEntity):
    """Battery voltage sensor."""

    device_class = "voltage"
    native_unit_of_measurement = "V"

    def __init__(self, trap_id: str, battery_v: float):
        self._trap_id = trap_id
        self._value = battery_v
        self._last_seen = datetime.utcnow()

        self._attr_name = f"SWISSINNO Trap {trap_id} Battery"
        self._attr_unique_id = f"swissinno_trap_{trap_id}_battery"
        self._attr_native_value = battery_v

        self._attr_device_info = {
            "identifiers": {(DOMAIN, trap_id)},
            "manufacturer": "SWISSINNO",
            "name": f"SWISSINNO Trap {trap_id}",
        }

    def update_value(self, value: float):
        self._attr_native_value = value
        self._last_seen = datetime.utcnow()
        self.async_write_ha_state()


class SwissinnoRSSISensor(SensorEntity):
    """RSSI sensor."""

    native_unit_of_measurement = "dBm"

    def __init__(self, trap_id: str, rssi: int):
        self._trap_id = trap_id
        self._value = rssi
        self._last_seen = datetime.utcnow()

        self._attr_name = f"SWISSINNO Trap {trap_id} RSSI"
        self._attr_unique_id = f"swissinno_trap_{trap_id}_rssi"
        self._attr_native_value = rssi

        self._attr_device_info = {
            "identifiers": {(DOMAIN, trap_id)},
            "manufacturer": "SWISSINNO",
            "name": f"SWISSINNO Trap {trap_id}",
        }

    def update_value(self, rssi: int):
        self._attr_native_value = rssi
        self._last_seen = datetime.utcnow()
        self.async_write_ha_state()
