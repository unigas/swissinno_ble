from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATOR, DOMAIN
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
