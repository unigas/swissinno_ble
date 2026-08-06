import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
    async_track_unavailable,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, MANUFACTURER_ID, normalized_address
from .decoder import decode_frame

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up SWISSINNO BLE binary sensors."""
    _LOGGER.info("SWISSINNO BLE: Registering Bluetooth scanner callback...")

    sensors: dict[str, SwissinnoTrapSensor] = {}

    @callback
    def detection_callback(service_info: BluetoothServiceInfoBleak, change):
        """Handle BLE advertisements."""
        man = service_info.manufacturer_data
        if MANUFACTURER_ID not in man:
            return

        frame = decode_frame(man[MANUFACTURER_ID])
        if not frame:
            return

        trap_id = normalized_address(service_info.address)
        rssi = service_info.rssi

        _LOGGER.debug(
            "Trap %s: tripped=%s, RSSI=%s dBm, battery=%s V",
            trap_id,
            frame.is_tripped,
            rssi,
            frame.battery_volts,
        )

        if trap_id in sensors:
            sensors[trap_id].update_state(frame.is_tripped)
        else:
            entity = SwissinnoTrapSensor(
                service_info.address, trap_id, frame.is_tripped
            )
            sensors[trap_id] = entity
            async_add_entities([entity], update_before_add=True)

            @callback
            def unavailable_callback(_service_info, trap_id=trap_id):
                sensors[trap_id].set_unavailable()
                updater = hass.data.get(DOMAIN, {}).get("update_sensors")
                if updater:
                    updater(trap_id, available=False)

            entry.async_on_unload(
                async_track_unavailable(
                    hass,
                    unavailable_callback,
                    service_info.address,
                    connectable=False,
                )
            )

        # Route to battery + RSSI sensors if available
        updater = hass.data.get(DOMAIN, {}).get("update_sensors")
        if updater:
            updater(
                trap_id,
                rssi=rssi,
                battery_v=frame.battery_volts,
                available=True,
            )

    cancel_callback = async_register_callback(
        hass,
        detection_callback,
        {"manufacturer_id": MANUFACTURER_ID},
        BluetoothScanningMode.PASSIVE,
    )

    entry.async_on_unload(cancel_callback)

    _LOGGER.info("SWISSINNO BLE: Bluetooth scanner callback registered.")


class SwissinnoTrapSensor(BinarySensorEntity):
    """Representation of a SWISSINNO BLE trap."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, address: str, trap_id: str, tripped: bool):
        self._trap_id = trap_id
        self._state = tripped
        self._attr_available = True

        self._attr_name = f"SWISSINNO Trap {trap_id}"
        self._attr_unique_id = f"swissinno_trap_{trap_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, trap_id)},
            manufacturer="SWISSINNO",
            name=f"SWISSINNO Trap {trap_id}",
        )

    @property
    def is_on(self) -> bool:
        return self._state

    def update_state(self, tripped: bool):
        self._state = tripped
        self._attr_available = True
        self.async_write_ha_state()

    @callback
    def set_unavailable(self) -> None:
        """Mark the trap unavailable when advertisements stop."""
        self._attr_available = False
        self.async_write_ha_state()
