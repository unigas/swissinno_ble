import logging
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricPotential,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory

from .battery import BatteryStabilizer
from .const import DATA_COORDINATOR, DOMAIN, entity_unique_id, legacy_unique_ids
from .coordinator import TrapObservation, TrapObservationCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Prepare update callback for binary_sensor.py."""
    _LOGGER.info("SWISSINNO BLE: Initializing battery + RSSI sensors")

    battery_sensors: dict[str, SwissinnoBatterySensor] = {}
    battery_stabilizers: dict[str, BatteryStabilizer] = {}
    rssi_sensors: dict[str, SwissinnoRSSISensor] = {}
    last_seen_sensors: dict[str, SwissinnoLastSeenSensor] = {}
    last_triggered_sensors: dict[str, SwissinnoLastTriggeredSensor] = {}
    trigger_count_sensors: dict[str, SwissinnoTriggerCountSensor] = {}
    entity_registry = er.async_get(hass)
    coordinator: TrapObservationCoordinator = hass.data[DOMAIN][DATA_COORDINATOR]

    @callback
    def update_sensors(
        trap_id: str,
        observation: TrapObservation,
    ) -> None:
        if not observation.available:
            if trap_id in battery_sensors:
                battery_sensors[trap_id].set_unavailable()
            if trap_id in rssi_sensors:
                rssi_sensors[trap_id].set_unavailable()
            return

        # Battery readings can briefly be invalid during startup or switching.
        # Keep the last published value until two consecutive readings agree.
        stabilizer = battery_stabilizers.setdefault(trap_id, BatteryStabilizer())
        stable_battery_v = stabilizer.update(observation.battery_v)
        if stable_battery_v is not None:
            if trap_id in battery_sensors:
                battery_sensors[trap_id].update_value(stable_battery_v)
            else:
                _migrate_legacy_unique_id(
                    entity_registry,
                    "sensor",
                    observation.legacy_trap_ids,
                    "battery",
                    entity_unique_id(trap_id, "battery"),
                )
                sensor = SwissinnoBatterySensor(trap_id, stable_battery_v)
                battery_sensors[trap_id] = sensor
                async_add_entities([sensor])

        # RSSI
        if trap_id in rssi_sensors:
            rssi_sensors[trap_id].update_value(observation.rssi)
        else:
            _migrate_legacy_unique_id(
                entity_registry,
                "sensor",
                observation.legacy_trap_ids,
                "rssi",
                entity_unique_id(trap_id, "rssi"),
            )
            sensor = SwissinnoRSSISensor(trap_id, observation.rssi)
            rssi_sensors[trap_id] = sensor
            async_add_entities([sensor])

        # Keep the diagnostic timestamp available even when the trap later
        # becomes unavailable, so users can see when it was last received.
        if observation.last_seen is not None:
            if trap_id in last_seen_sensors:
                last_seen_sensors[trap_id].update_value(observation.last_seen)
            else:
                sensor = SwissinnoLastSeenSensor(trap_id, observation.last_seen)
                last_seen_sensors[trap_id] = sensor
                async_add_entities([sensor])

        if trap_id in last_triggered_sensors:
            last_triggered_sensors[trap_id].update_value(
                observation.last_triggered
            )
        else:
            sensor = SwissinnoLastTriggeredSensor(
                trap_id, observation.last_triggered
            )
            last_triggered_sensors[trap_id] = sensor
            async_add_entities([sensor])

        if trap_id in trigger_count_sensors:
            trigger_count_sensors[trap_id].update_value(
                observation.trigger_count
            )
        else:
            sensor = SwissinnoTriggerCountSensor(
                trap_id, observation.trigger_count
            )
            trigger_count_sensors[trap_id] = sensor
            async_add_entities([sensor])

    entry.async_on_unload(coordinator.register_listener(update_sensors))


def _migrate_legacy_unique_id(
    entity_registry,
    platform: str,
    legacy_trap_ids: tuple[str, ...] | None,
    suffix: str,
    unique_id: str,
) -> None:
    """Migrate a legacy payload-based unique ID when no duplicate exists."""
    if legacy_trap_ids is None or entity_registry.async_get_entity_id(
        platform, DOMAIN, unique_id
    ):
        return

    for legacy_unique_id in legacy_unique_ids(legacy_trap_ids, suffix):
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
    _attr_icon = "mdi:battery"
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_suggested_display_precision = 2
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

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_has_entity_name = True
    _attr_icon = "mdi:wifi"
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


class SwissinnoLastSeenSensor(SensorEntity):
    """Timestamp of the most recent fresh trap advertisement."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_icon = "mdi:clock-outline"
    _attr_translation_key = "last_seen"

    def __init__(self, trap_id: str, last_seen: datetime):
        self._attr_unique_id = entity_unique_id(trap_id, "last_seen")
        self._attr_native_value = last_seen
        self._attr_device_info = {
            "identifiers": {(DOMAIN, trap_id)},
            "manufacturer": "SWISSINNO",
            "name": f"SWISSINNO Trap {trap_id}",
        }

    def update_value(self, last_seen: datetime) -> None:
        self._attr_native_value = last_seen
        self.async_write_ha_state()


class SwissinnoLastTriggeredSensor(SensorEntity):
    """Timestamp of the most recent confirmed trigger transition."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = True
    _attr_icon = "mdi:clock-alert-outline"
    _attr_translation_key = "last_triggered"

    def __init__(self, trap_id: str, last_triggered: datetime | None):
        self._attr_unique_id = entity_unique_id(trap_id, "last_triggered")
        self._attr_native_value = last_triggered
        self._attr_device_info = {
            "identifiers": {(DOMAIN, trap_id)},
            "manufacturer": "SWISSINNO",
            "name": f"SWISSINNO Trap {trap_id}",
        }

    def update_value(self, last_triggered: datetime | None) -> None:
        if self._attr_native_value == last_triggered:
            return
        self._attr_native_value = last_triggered
        self.async_write_ha_state()


class SwissinnoTriggerCountSensor(SensorEntity):
    """Count confirmed trigger transitions observed by Home Assistant."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 0
    _attr_translation_key = "trigger_count"

    def __init__(self, trap_id: str, trigger_count: int):
        self._attr_unique_id = entity_unique_id(trap_id, "trigger_count")
        self._attr_native_value = trigger_count
        self._attr_device_info = {
            "identifiers": {(DOMAIN, trap_id)},
            "manufacturer": "SWISSINNO",
            "name": f"SWISSINNO Trap {trap_id}",
        }

    def update_value(self, trigger_count: int) -> None:
        if self._attr_native_value == trigger_count:
            return
        self._attr_native_value = trigger_count
        self.async_write_ha_state()
