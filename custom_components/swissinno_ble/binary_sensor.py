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

        # Stable trap ID = BLE MAC without colons
        trap_id = service_info.address.replace(":", "").lower()
        rssi = service_info.rssi

        _LOGGER.info(
            f"SWISSINNO BLE: Trap {trap_id} | Tripped={frame.is_tripped} "
            f"RSSI={rssi} dBm | Battery={frame.battery_volts} V"
        )

        if trap_id in sensors:
            sensors[trap_id].update_state(frame.is_tripped)
        else:
            entity = SwissinnoTrapSensor(service_info.address, trap_id, frame.is_tripped)
            sensors[trap_id] = entity
            async_add_entities([entity], update_before_add=True)

        # Route to battery + RSSI sensors if available
        updater = hass.data.get(DOMAIN, {}).get("update_sensors")
        if updater:
            hass.async_create_task(
                updater(trap_id, service_info.address, rssi, frame.battery_volts)
            )

    cancel_callback = async_register_callback(
        hass,
        detection_callback,
        {},  # no additional filter (we use manufacturer ID in code)
        BluetoothScanningMode.PASSIVE,
    )

    hass.bus.async_listen_once("homeassistant_stop", cancel_callback)

    _LOGGER.info("SWISSINNO BLE: Bluetooth scanner callback registered.")
    

class SwissinnoTrapSensor(BinarySensorEntity):
    """Representation of a SWISSINNO BLE trap."""

    _attr_device_class = "problem"

    def __init__(self, address: str, trap_id: str, tripped: bool):
        self._address = address
        self._trap_id = trap_id
        self._state = tripped
        self._last_seen = datetime.utcnow()

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

    @property
    def available(self):
        return datetime.utcnow() - self._last_seen < LAST_SEEN_TIMEOUT

    def update_state(self, tripped: bool):
        self._state = tripped
        self._last_seen = datetime.utcnow()
        self.async_write_ha_state()
