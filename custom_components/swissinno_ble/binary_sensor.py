import logging
from datetime import UTC, datetime
from time import monotonic

from homeassistant.components import bluetooth
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
    async_track_unavailable,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    ADVERTISEMENT_MATCHER,
    DATA_COORDINATOR,
    DOMAIN,
    MANUFACTURER_ID,
    entity_unique_id,
    legacy_unique_ids,
    normalized_address,
)
from .coordinator import TrapObservation, TrapObservationCoordinator
from .decoder import decode_frame
from .freshness import is_fresh_advertisement

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up SWISSINNO BLE binary sensors."""
    _LOGGER.info("SWISSINNO BLE: Registering Bluetooth scanner callback...")

    sensors: dict[str, SwissinnoTrapSensor] = {}
    entity_registry = er.async_get(hass)
    coordinator: TrapObservationCoordinator = hass.data[DOMAIN][DATA_COORDINATOR]
    accept_after = monotonic()

    @callback
    def detection_callback(service_info: BluetoothServiceInfoBleak, change):
        """Handle BLE advertisements."""
        if not is_fresh_advertisement(service_info.time, accept_after):
            _LOGGER.debug(
                "Ignoring cached advertisement for %s from before integration setup",
                service_info.address,
            )
            _clear_advertisement_history(hass, service_info.address)
            return

        man = service_info.manufacturer_data
        if MANUFACTURER_ID not in man:
            return

        frame = decode_frame(man[MANUFACTURER_ID])
        if not frame:
            return

        trap_id = normalized_address(service_info.address)
        rssi = service_info.rssi

        # Versions before 1.0.16 used manufacturer-data bytes in the unique ID.
        # Preserve the user's existing entity_id when the MAC-based identity is
        # not already registered. Existing duplicate entities are left alone so
        # Home Assistant configuration is never destructively rewritten.
        old_unique_ids = legacy_unique_ids(frame.legacy_trap_ids)
        unique_id = entity_unique_id(service_info.address)
        if not entity_registry.async_get_entity_id(
            "binary_sensor", DOMAIN, unique_id
        ):
            for legacy_unique_id in old_unique_ids:
                legacy_entity_id = entity_registry.async_get_entity_id(
                    "binary_sensor", DOMAIN, legacy_unique_id
                )
                if legacy_entity_id:
                    entity_registry.async_update_entity(
                        legacy_entity_id, new_unique_id=unique_id
                    )
                    break

        _LOGGER.debug(
            "Trap %s: status=0x%02X, tripped=%s, RSSI=%s dBm, battery=%s V",
            trap_id,
            frame.status,
            frame.is_tripped,
            rssi,
            frame.battery_volts,
        )

        if trap_id in sensors:
            sensors[trap_id].update_state(frame.is_tripped)
        else:
            entity = SwissinnoTrapSensor(trap_id, frame.is_tripped)
            sensors[trap_id] = entity
            async_add_entities([entity], update_before_add=True)

            @callback
            def unavailable_callback(_service_info, trap_id=trap_id):
                sensors[trap_id].set_unavailable()
                coordinator.set_unavailable(trap_id)

            entry.async_on_unload(
                async_track_unavailable(
                    hass,
                    unavailable_callback,
                    service_info.address,
                    connectable=False,
                )
            )

        # Cache before publishing so sensor setup can safely finish after the
        # synchronous Bluetooth history replay performed during registration.
        coordinator.update(
            trap_id,
            TrapObservation(
                rssi=rssi,
                battery_v=frame.battery_volts,
                legacy_trap_ids=frame.legacy_trap_ids,
                last_seen=datetime.now(UTC),
            ),
        )
        _clear_advertisement_history(hass, service_info.address)

    cancel_callback = async_register_callback(
        hass,
        detection_callback,
        ADVERTISEMENT_MATCHER,
        BluetoothScanningMode.PASSIVE,
    )

    entry.async_on_unload(cancel_callback)

    _LOGGER.info("SWISSINNO BLE: Bluetooth scanner callback registered.")


def _clear_advertisement_history(hass: HomeAssistant, address: str) -> None:
    """Ensure the next identical trap advertisement reaches the callback."""
    if clear_history := getattr(
        bluetooth, "async_clear_advertisement_history", None
    ):
        clear_history(hass, address)


class SwissinnoTrapSensor(BinarySensorEntity):
    """Representation of a SWISSINNO BLE trap."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:rodent"
    _attr_translation_key = "trap_status"

    def __init__(self, trap_id: str, tripped: bool | None):
        self._trap_id = trap_id
        self._state = tripped
        self._attr_available = True

        self._attr_unique_id = entity_unique_id(trap_id)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, trap_id)},
            manufacturer="SWISSINNO",
            name=f"SWISSINNO Trap {trap_id}",
        )

    @property
    def is_on(self) -> bool | None:
        return self._state

    def update_state(self, tripped: bool | None):
        self._state = tripped
        self._attr_available = True
        self.async_write_ha_state()

    @callback
    def set_unavailable(self) -> None:
        """Mark the trap unavailable when advertisements stop."""
        self._attr_available = False
        self.async_write_ha_state()
