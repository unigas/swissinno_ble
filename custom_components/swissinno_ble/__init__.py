from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.storage import Store

from .const import DATA_COORDINATOR, DOMAIN, is_legacy_payload_trap_id
from .coordinator import (
    TrapObservationCoordinator,
    TriggerHistoryStorage,
    trigger_history_from_storage,
)

_STORAGE_VERSION = 1
_STORAGE_KEY = f"{DOMAIN}.trigger_history"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SWISSINNO BLE integration."""
    store = Store[TriggerHistoryStorage](hass, _STORAGE_VERSION, _STORAGE_KEY)
    trigger_history = trigger_history_from_storage(await store.async_load())

    def schedule_history_save(data: TriggerHistoryStorage) -> None:
        store.async_delay_save(lambda: data, 1)

    hass.data.setdefault(DOMAIN, {})[DATA_COORDINATOR] = TrapObservationCoordinator(
        trigger_history, schedule_history_save
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
