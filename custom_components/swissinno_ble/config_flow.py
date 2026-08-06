import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("device_name", default="SWISSINNO BLE"): cv.string,
    }
)


class SwissinnoBLEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Swissinno BLE."""

    VERSION = 1

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> config_entries.ConfigFlowResult:
        """Create the single integration entry from Bluetooth discovery."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title="SWISSINNO BLE", data={})

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        # Only one entry is needed because it discovers all supported traps.
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input["device_name"], data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors,
        )
