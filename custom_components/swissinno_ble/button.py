"""Button platform for SWISSINNO BLE traps."""

import logging

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    CONNECTABLE_ADVERTISEMENT_MATCHER,
    DOMAIN,
    MANUFACTURER_ID,
    normalized_address,
)
from .decoder import decode_frame, supports_remote_reset
from .reset import async_reset_trap

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Reset Trap buttons."""
    _LOGGER.info("SWISSINNO BLE: Setting up Reset Trap buttons")

    buttons = {}
    entity_registry = er.async_get(hass)

    @callback
    def detection_callback(service_info: BluetoothServiceInfoBleak, change):
        manufacturer_data = service_info.manufacturer_data

        if MANUFACTURER_ID not in manufacturer_data:
            return

        payload = manufacturer_data[MANUFACTURER_ID]
        if decode_frame(payload) is None or not supports_remote_reset(payload):
            return

        address = service_info.address
        trap_id = normalized_address(address)

        # Versions before 1.0.16 used changing advertisement bytes in the
        # reset button unique ID. Migrate the currently discoverable ID.
        legacy_trap_id = "".join(f"{byte:02X}" for byte in payload[2:6])
        legacy_unique_id = f"swissinno_trap_{legacy_trap_id}_reset"
        unique_id = f"swissinno_trap_{trap_id}_reset"
        legacy_entity_id = entity_registry.async_get_entity_id(
            "button", DOMAIN, legacy_unique_id
        )
        if legacy_entity_id and not entity_registry.async_get_entity_id(
            "button", DOMAIN, unique_id
        ):
            entity_registry.async_update_entity(
                legacy_entity_id, new_unique_id=unique_id
            )

        if trap_id in buttons:
            return

        _LOGGER.info(
            "SWISSINNO BLE: Adding Reset Trap button for %s (%s)",
            trap_id,
            address,
        )

        button = SwissinnoResetButton(hass, address, trap_id)
        buttons[trap_id] = button

        async_add_entities([button])

    cancel = async_register_callback(
        hass,
        detection_callback,
        CONNECTABLE_ADVERTISEMENT_MATCHER,
        BluetoothScanningMode.PASSIVE,
    )

    entry.async_on_unload(cancel)


class SwissinnoResetButton(ButtonEntity):
    """Button to reset a SWISSINNO trap."""

    _attr_has_entity_name = True
    _attr_translation_key = "reset_trap"

    def __init__(self, hass: HomeAssistant, address: str, trap_id: str):
        self._hass = hass
        self._address = address
        self._trap_id = trap_id

        self._attr_unique_id = f"swissinno_trap_{trap_id}_reset"
        self._attr_icon = "mdi:restart"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, trap_id)},
            name=f"SWISSINNO Trap {trap_id}",
            manufacturer="SWISSINNO",
            model="BLE Trap",
        )

    async def async_press(self) -> None:
        await async_reset_trap(self._hass, self._address)
