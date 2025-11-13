from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the SWISSINNO BLE integration via YAML (legacy method)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SWISSINNO BLE integration."""
    await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor", "sensor", "button"])
    return True

