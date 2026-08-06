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
        self.assertIn("issue_tracker", manifest)
        self.assertIn("bluetooth_adapters", manifest["dependencies"])

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
            {"manufacturer_id": const.MANUFACTURER_ID, "connectable": False},
        )

    def test_custom_integration_uses_translation_file_only(self):
        translations = json.loads(
            (INTEGRATION / "translations" / "en.json").read_text(encoding="utf-8")
        )
        self.assertIn("entity", translations)
        self.assertFalse((INTEGRATION / "strings.json").exists())


if __name__ == "__main__":
    unittest.main()
