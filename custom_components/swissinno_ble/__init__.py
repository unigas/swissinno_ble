from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DATA_COORDINATOR, DOMAIN, is_legacy_payload_trap_id
from .coordinator import TrapObservationCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SWISSINNO BLE integration."""
    hass.data.setdefault(DOMAIN, {})[DATA_COORDINATOR] = (
        TrapObservationCoordinator()
    )
    await hass.config_entries.async_forward_entry_setups(
        entry, ["binary_sensor", "sensor", "button"]
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a SWISSINNO BLE config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["binary_sensor", "sensor", "button"]
    )
    if unload_ok:
        hass.data.pop(DOMAIN, None)
    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Allow users to remove only stale legacy payload-ID devices."""
    trap_identifiers = [
        identifier
        for domain, identifier in device_entry.identifiers
        if domain == DOMAIN
    ]
    return bool(trap_identifiers) and all(
        is_legacy_payload_trap_id(identifier) for identifier in trap_identifiers
    )
