import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricPotential,
)
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Prepare update callback for binary_sensor.py."""
    _LOGGER.info("SWISSINNO BLE: Initializing battery + RSSI sensors")

    battery_sensors: dict[str, SwissinnoBatterySensor] = {}
    rssi_sensors: dict[str, SwissinnoRSSISensor] = {}

    @callback
    def update_sensors(
        trap_id: str,
        *,
        rssi: int | None = None,
        battery_v: float | None = None,
        available: bool,
    ) -> None:
        if not available:
            if trap_id in battery_sensors:
                battery_sensors[trap_id].set_unavailable()
            if trap_id in rssi_sensors:
                rssi_sensors[trap_id].set_unavailable()
            return

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

    @callback
    def remove_updater() -> None:
        domain_data = hass.data.get(DOMAIN)
        if domain_data and domain_data.get("update_sensors") is update_sensors:
            domain_data.pop("update_sensors")

    entry.async_on_unload(remove_updater)


class SwissinnoBatterySensor(SensorEntity):
    """Battery voltage sensor."""

    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_translation_key = "battery_voltage"

    def __init__(self, trap_id: str, battery_v: float | None):
        self._trap_id = trap_id
        self._value = battery_v
        self._attr_available = True

        self._attr_unique_id = f"swissinno_trap_{trap_id}_battery"
        self._attr_native_value = battery_v

        self._attr_device_info = {
            "identifiers": {(DOMAIN, trap_id)},
            "manufacturer": "SWISSINNO",
            "name": f"SWISSINNO Trap {trap_id}",
        }

    def update_value(self, value: float | None):
        self._attr_native_value = value
        self._attr_available = True
        self.async_write_ha_state()

    @callback
    def set_unavailable(self) -> None:
        self._attr_available = False
        self.async_write_ha_state()


class SwissinnoRSSISensor(SensorEntity):
    """RSSI sensor."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_translation_key = "signal_strength"

    def __init__(self, trap_id: str, rssi: int | None):
        self._trap_id = trap_id
        self._value = rssi
        self._attr_available = True

        self._attr_unique_id = f"swissinno_trap_{trap_id}_rssi"
        self._attr_native_value = rssi

        self._attr_device_info = {
            "identifiers": {(DOMAIN, trap_id)},
            "manufacturer": "SWISSINNO",
            "name": f"SWISSINNO Trap {trap_id}",
        }

    def update_value(self, rssi: int | None):
        self._attr_native_value = rssi
        self._attr_available = True
        self.async_write_ha_state()

    @callback
    def set_unavailable(self) -> None:
        self._attr_available = False
        self.async_write_ha_state()
