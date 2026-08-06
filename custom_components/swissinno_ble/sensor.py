import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricPotential,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .battery import BatteryStabilizer
from .const import DOMAIN, entity_unique_id, legacy_unique_ids

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Prepare update callback for binary_sensor.py."""
    _LOGGER.info("SWISSINNO BLE: Initializing battery + RSSI sensors")

    battery_sensors: dict[str, SwissinnoBatterySensor] = {}
    battery_stabilizers: dict[str, BatteryStabilizer] = {}
    rssi_sensors: dict[str, SwissinnoRSSISensor] = {}
    entity_registry = er.async_get(hass)

    @callback
    def update_sensors(
        trap_id: str,
        *,
        rssi: int | None = None,
        battery_v: float | None = None,
        legacy_trap_id: str | None = None,
        available: bool,
    ) -> None:
        if not available:
            if trap_id in battery_sensors:
                battery_sensors[trap_id].set_unavailable()
            if trap_id in rssi_sensors:
                rssi_sensors[trap_id].set_unavailable()
            return

        # Battery readings can briefly be invalid during startup or switching.
        # Keep the last published value until two consecutive readings agree.
        stabilizer = battery_stabilizers.setdefault(trap_id, BatteryStabilizer())
        stable_battery_v = stabilizer.update(battery_v)
        if stable_battery_v is not None:
            if trap_id in battery_sensors:
                battery_sensors[trap_id].update_value(stable_battery_v)
            else:
                _migrate_legacy_unique_id(
                    entity_registry,
                    "sensor",
                    legacy_trap_id,
                    "battery",
                    entity_unique_id(trap_id, "battery"),
                )
                sensor = SwissinnoBatterySensor(trap_id, stable_battery_v)
                battery_sensors[trap_id] = sensor
                async_add_entities([sensor])

        # RSSI
        if trap_id in rssi_sensors:
            rssi_sensors[trap_id].update_value(rssi)
        else:
            _migrate_legacy_unique_id(
                entity_registry,
                "sensor",
                legacy_trap_id,
                "rssi",
                entity_unique_id(trap_id, "rssi"),
            )
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


def _migrate_legacy_unique_id(
    entity_registry,
    platform: str,
    legacy_trap_id: str | None,
    suffix: str,
    unique_id: str,
) -> None:
    """Migrate a legacy payload-based unique ID when no duplicate exists."""
    if legacy_trap_id is None or entity_registry.async_get_entity_id(
        platform, DOMAIN, unique_id
    ):
        return

    for legacy_unique_id in legacy_unique_ids(legacy_trap_id, suffix):
        legacy_entity_id = entity_registry.async_get_entity_id(
            platform, DOMAIN, legacy_unique_id
        )
        if legacy_entity_id:
            entity_registry.async_update_entity(
                legacy_entity_id, new_unique_id=unique_id
            )
            return


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

        self._attr_unique_id = entity_unique_id(trap_id, "battery")
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

        self._attr_unique_id = entity_unique_id(trap_id, "rssi")
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
