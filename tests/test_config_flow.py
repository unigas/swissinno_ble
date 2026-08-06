"""Tests for the SWISSINNO config flow."""

import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path

COMPONENT_DIR = (
    Path(__file__).parents[1] / "custom_components" / "swissinno_ble"
)


class FakeConfigFlow:
    def __init_subclass__(cls, **kwargs):
        return super().__init_subclass__()

    def __init__(self):
        self.unique_id = None
        self.abort_checked = False
        self.current_entries = []

    async def async_set_unique_id(self, unique_id):
        self.unique_id = unique_id

    def _abort_if_unique_id_configured(self):
        self.abort_checked = True

    def _async_current_entries(self):
        return self.current_entries

    def async_abort(self, *, reason):
        return {"type": "abort", "reason": reason}

    def async_create_entry(self, *, title, data):
        return {"type": "create_entry", "title": title, "data": data}

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}


def load_config_flow():
    voluptuous = types.ModuleType("voluptuous")
    voluptuous.Required = lambda key, default=None: key
    voluptuous.Schema = lambda schema: schema

    config_entries = types.ModuleType("homeassistant.config_entries")
    config_entries.ConfigFlow = FakeConfigFlow
    config_entries.ConfigFlowResult = dict

    bluetooth = types.ModuleType("homeassistant.components.bluetooth")
    bluetooth.BluetoothServiceInfoBleak = object

    cv = types.ModuleType("homeassistant.helpers.config_validation")
    cv.string = str

    sys.modules["voluptuous"] = voluptuous
    sys.modules["homeassistant"] = types.ModuleType("homeassistant")
    sys.modules["homeassistant"].config_entries = config_entries
    sys.modules["homeassistant.config_entries"] = config_entries
    sys.modules["homeassistant.components"] = types.ModuleType(
        "homeassistant.components"
    )
    sys.modules["homeassistant.components.bluetooth"] = bluetooth
    sys.modules["homeassistant.helpers"] = types.ModuleType("homeassistant.helpers")
    sys.modules["homeassistant.helpers"].config_validation = cv
    sys.modules["homeassistant.helpers.config_validation"] = cv

    package = types.ModuleType("custom_components.swissinno_ble")
    package.__path__ = [str(COMPONENT_DIR)]
    sys.modules["custom_components"] = types.ModuleType("custom_components")
    sys.modules["custom_components.swissinno_ble"] = package

    const_spec = importlib.util.spec_from_file_location(
        "custom_components.swissinno_ble.const", COMPONENT_DIR / "const.py"
    )
    const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = const_module
    const_spec.loader.exec_module(const_module)

    spec = importlib.util.spec_from_file_location(
        "custom_components.swissinno_ble.config_flow",
        COMPONENT_DIR / "config_flow.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


config_flow = load_config_flow()


class ConfigFlowTests(unittest.TestCase):
    def test_bluetooth_discovery_creates_single_entry(self):
        flow = config_flow.SwissinnoBLEConfigFlow()
        result = asyncio.run(flow.async_step_bluetooth(object()))
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["title"], "SWISSINNO BLE")
        self.assertEqual(flow.unique_id, "swissinno_ble")
        self.assertTrue(flow.abort_checked)

    def test_user_step_stores_integration_name(self):
        flow = config_flow.SwissinnoBLEConfigFlow()
        result = asyncio.run(
            flow.async_step_user({"device_name": "Mouse traps"})
        )
        self.assertEqual(result["title"], "Mouse traps")
        self.assertEqual(flow.unique_id, "swissinno_ble")

    def test_user_step_aborts_when_entry_exists(self):
        flow = config_flow.SwissinnoBLEConfigFlow()
        flow.current_entries = [object()]
        result = asyncio.run(flow.async_step_user())
        self.assertEqual(result, {"type": "abort", "reason": "already_configured"})


if __name__ == "__main__":
    unittest.main()
