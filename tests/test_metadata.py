"""Tests for Home Assistant and HACS repository metadata."""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
INTEGRATION = ROOT / "custom_components" / "swissinno_ble"


class MetadataTests(unittest.TestCase):
    def test_hacs_manifest_is_at_repository_root(self):
        hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
        self.assertEqual(hacs["name"], "SWISSINNO BLE")
        self.assertFalse((INTEGRATION / "hacs.json").exists())

    def test_home_assistant_manifest_declares_current_features(self):
        manifest = json.loads(
            (INTEGRATION / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertTrue(manifest["config_flow"])
        self.assertTrue(manifest["single_config_entry"])
        self.assertEqual(manifest["integration_type"], "hub")
        self.assertEqual(manifest["version"], "1.0.20")
        self.assertIn("issue_tracker", manifest)
        self.assertIn("bluetooth_adapters", manifest["dependencies"])
        self.assertTrue((ROOT / "CHANGELOG.md").exists())

    def test_proxy_advertisements_are_discoverable(self):
        manifest = json.loads(
            (INTEGRATION / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertTrue(manifest["bluetooth"])
        self.assertTrue(
            all(matcher["connectable"] is False for matcher in manifest["bluetooth"])
        )

        spec = importlib.util.spec_from_file_location(
            "swissinno_ble_const", INTEGRATION / "const.py"
        )
        const = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(const)
        self.assertEqual(
            const.ADVERTISEMENT_MATCHER,
            {
                "manufacturer_id": const.MANUFACTURER_ID,
                "service_uuid": const.SERVICE_UUID,
                "connectable": False,
            },
        )
        self.assertEqual(manifest["bluetooth"], [const.ADVERTISEMENT_MATCHER])
        self.assertEqual(
            const.CONNECTABLE_ADVERTISEMENT_MATCHER,
            {
                **const.ADVERTISEMENT_MATCHER,
                "connectable": True,
            },
        )

    def test_custom_integration_uses_translation_file_only(self):
        translations = json.loads(
            (INTEGRATION / "translations" / "en.json").read_text(encoding="utf-8")
        )
        self.assertIn("entity", translations)
        self.assertFalse((INTEGRATION / "strings.json").exists())

    def test_problem_binary_sensor_uses_decoder_state_directly(self):
        source = (INTEGRATION / "binary_sensor.py").read_text(encoding="utf-8")
        self.assertIn(
            "_attr_device_class = BinarySensorDeviceClass.PROBLEM", source
        )
        self.assertIn("def is_on(self) -> bool | None:", source)
        self.assertIn("return self._state", source)


if __name__ == "__main__":
    unittest.main()
