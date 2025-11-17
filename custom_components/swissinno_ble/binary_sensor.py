import asyncio
import logging
from datetime import datetime, timedelta

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_register_callback,
    BluetoothScanningMode,
)
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, MANUFACTURER_ID
from .decoder import decode_frame

_LOGGER = logging.getLogger(__name__)

LAST_SEEN_TIMEOUT = timedelta(minutes=30)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up SWISSINNO BLE binary sensors."""
    _LOGGER.info("SWISSINNO BLE: Registering Bluetooth scanner callback...")

    sensors = {}

    @callback
    def detection_callback(service_info: BluetoothServiceInfoBleak, change):
        """Handle BLE advertisements."""
        manufacturer_data = service_info.manufacturer_data
        if MANUFACTURER_ID not in manufacturer_data:
            return

        frame = decode_frame(manufacturer_data[MANUFACTURER_ID])
        if not frame:
            return

        trap_id = frame.trap_id
        rssi = service_info.rssi

        _LOGGER.info(
            f"SWISSINNO BLE: Trap {trap_id} | Tripped={frame.is_tripped} "
            f"RSSI={rssi} dBm | Battery={frame.battery_volts} V"
        )

        # Update or create the binary sensor
        if trap_id in sensors:
            sensors[trap_id].update_state(frame.is_tripped)
        else:
            sensor = SwissinnoTrapSensor(service_info.address, trap_id, frame.is_tripped)
            sensors[trap_id] = sensor
            async_add_entities([sensor], update_before_add=True)

        # Forward to battery + RSSI sensors if present
        if DOMAIN in hass.data and "update_sensors" in hass.data[DOMAIN]:
            hass.async_create_task(
                hass.data[DOMAIN]["update_sensors"](
                    trap_id,
                    service_info.address,
                    rssi,
                    frame.battery_volts,
                )
            )

    cancel_callback = async_register_callback(
        hass,
        detection_callback,
        {},
        BluetoothScanningMode.PASSIVE,
    )
    hass.bus.async_listen_once("homeassistant_stop", cancel_callback)

    _LOGGER.info("SWISSINNO BLE: Bluetooth scanner callback registered successfully!")


class SwissinnoTrapSensor(BinarySensorEntity):
    """Representation of a SWISSINNO BLE trap state."""

    _attr_device_class = "problem"

    def __init__(self, address: str, trap_id: str, is_tripped: bool):
        _LOGGER.info(f"SWISSINNO BLE: Creating sensor for trap {trap_id}")

        self._attr_name = f"SWISSINNO Trap {trap_id}"
        self._attr_unique_id = f"swissinno_trap_{trap_id}"
        self._state = is_tripped
        self._last_seen = datetime.utcnow()

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, trap_id)},
            name=f"SWISSINNO Trap {trap_id}",
            manufacturer="SWISSINNO",
        )

    @property
    def is_on(self):
        """Device is ON when it is tripped."""
        return self._state

    @property
    def available(self):
        """Trap becomes unavailable if not updated recently."""
        return datetime.utcnow() - self._last_seen < LAST_SEEN_TIMEOUT

    def update_state(self, is_tripped: bool):
        """Update trap state."""
        self._state = is_tripped
        self._last_seen = datetime.utcnow()
        self.async_write_ha_state()
