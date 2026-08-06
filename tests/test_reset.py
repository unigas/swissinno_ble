"""Tests for the Bluetooth reset helper."""

import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock

RESET_PATH = (
    Path(__file__).parents[1] / "custom_components" / "swissinno_ble" / "reset.py"
)


class ResetHelperTests(unittest.TestCase):
    def _load_module(self, properties):
        characteristic = Mock(properties=properties)
        services = Mock()
        services.get_characteristic.return_value = characteristic
        client = Mock(services=services)
        client.write_gatt_char = AsyncMock()
        client.disconnect = AsyncMock()

        device = Mock(name="Trap")
        bluetooth = types.ModuleType("homeassistant.components.bluetooth")
        bluetooth.async_ble_device_from_address = Mock(return_value=device)
        connector = types.ModuleType("bleak_retry_connector")
        connector.BleakClientWithServiceCache = object
        connector.establish_connection = AsyncMock(return_value=client)

        sys.modules["homeassistant"] = types.ModuleType("homeassistant")
        sys.modules["homeassistant.components"] = types.ModuleType(
            "homeassistant.components"
        )
        sys.modules["homeassistant.components.bluetooth"] = bluetooth
        sys.modules["bleak_retry_connector"] = connector

        spec = importlib.util.spec_from_file_location("swissinno_reset", RESET_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, connector, client, characteristic

    def test_prefers_write_without_response(self):
        module, connector, client, characteristic = self._load_module(
            ["write", "write-without-response"]
        )
        asyncio.run(module.async_reset_trap(object(), "aa:bb"))
        connector.establish_connection.assert_awaited_once()
        client.write_gatt_char.assert_awaited_once_with(
            characteristic, b"\x00", response=False
        )
        client.disconnect.assert_awaited_once()

    def test_uses_response_when_required(self):
        module, _, client, characteristic = self._load_module(["write"])
        asyncio.run(module.async_reset_trap(object(), "aa:bb"))
        client.write_gatt_char.assert_awaited_once_with(
            characteristic, b"\x00", response=True
        )

    def test_disconnects_after_write_failure(self):
        module, _, client, _ = self._load_module(["write"])
        client.write_gatt_char.side_effect = RuntimeError("failed")
        with self.assertRaisesRegex(RuntimeError, "failed"):
            asyncio.run(module.async_reset_trap(object(), "aa:bb"))
        client.disconnect.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
