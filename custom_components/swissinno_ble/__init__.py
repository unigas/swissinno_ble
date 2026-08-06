from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SWISSINNO BLE integration."""
    await hass.config_entries.async_forward_entry_setups(
        entry, ["binary_sensor", "sensor", "button"]
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a SWISSINNO BLE config entry."""
    return await hass.config_entries.async_unload_platforms(
        entry, ["binary_sensor", "sensor", "button"]
    )
