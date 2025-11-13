"""Button platform for SWISSINNO BLE traps."""

import logging

from homeassistant.components.bluetooth import async_register_callback, BluetoothScanningMode
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .reset import async_reset_trap

_LOGGER = logging.getLogger(__name__)

SWISSINNO_MANUFACTURER_ID = 3003


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Reset Trap buttons."""
    _LOGGER.info("SWISSINNO BLE: Setting up Reset Trap buttons")

    buttons = {}

    @callback
    def detection_callback(service_info, change):
        manufacturer_data = service_info.manufacturer_data

        if SWISSINNO_MANUFACTURER_ID not in manufacturer_data:
            return

        data = manufacturer_data[SWISSINNO_MANUFACTURER_ID]
        if len(data) < 6:
            return

        trap_id = f"{data[2]:02X}{data[3]:02X}{data[4]:02X}{data[5]:02X}"

        if trap_id in buttons:
            return

        address = service_info.address
        _LOGGER.info("SWISSINNO BLE: Adding Reset Trap button for %s (%s)", trap_id, address)

        button = SwissinnoResetButton(hass, address, trap_id)
        buttons[trap_id] = button

        async_add_entities([button])

    cancel = async_register_callback(
        hass,
        detection_callback,
        {},
        BluetoothScanningMode.PASSIVE,
    )

    hass.bus.async_listen_once("homeassistant_stop", cancel)


class SwissinnoResetButton(ButtonEntity):
    """Button to reset a SWISSINNO trap."""

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, address: str, trap_id: str):
        self._hass = hass
        self._address = address
        self._trap_id = trap_id

        self._attr_unique_id = f"swissinno_trap_{trap_id}_reset"
        self._attr_name = "Reset Trap"
        self._attr_icon = "mdi:restart"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=f"SWISSINNO Trap {trap_id}",
            manufacturer="SWISSINNO",
            model="BLE Trap",
        )

    async def async_press(self):
        await async_reset_trap(self._hass, self._address)
