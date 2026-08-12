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
        self.assertTrue(hacs["zip_release"])
        self.assertEqual(hacs["filename"], "swissinno_ble.zip")
        self.assertFalse((INTEGRATION / "hacs.json").exists())

        release_workflow = (
            ROOT / ".github" / "workflows" / "release.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("release:", release_workflow)
        self.assertIn("- published", release_workflow)
        self.assertIn("contents: write", release_workflow)
        self.assertIn("zip -r ../../swissinno_ble.zip", release_workflow)
        self.assertIn("gh release upload", release_workflow)

    def test_home_assistant_manifest_declares_current_features(self):
        manifest = json.loads(
            (INTEGRATION / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertTrue(manifest["config_flow"])
        self.assertTrue(manifest["single_config_entry"])
        self.assertEqual(manifest["integration_type"], "hub")
        self.assertEqual(manifest["version"], "1.0.30")
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

    def test_only_stale_legacy_devices_can_be_removed(self):
        source = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("async def async_remove_config_entry_device(", source)
        self.assertIn("device_entry.identifiers", source)
        self.assertIn("is_legacy_payload_trap_id(identifier)", source)

        spec = importlib.util.spec_from_file_location(
            "swissinno_ble_const_identity", INTEGRATION / "const.py"
        )
        const = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(const)
        self.assertTrue(const.is_mac_based_trap_id("c8aedc738048"))
        self.assertTrue(const.is_mac_based_trap_id("C8AEDC738048"))
        self.assertFalse(const.is_mac_based_trap_id("DC140300"))
        self.assertFalse(const.is_mac_based_trap_id("1BDC14"))
        self.assertFalse(const.is_mac_based_trap_id("not-a-mac-id"))
        self.assertTrue(const.is_legacy_payload_trap_id("DC140300"))
        self.assertTrue(const.is_legacy_payload_trap_id("1BDC14"))
        self.assertFalse(const.is_legacy_payload_trap_id("c8aedc738048"))
        self.assertFalse(const.is_legacy_payload_trap_id("not-a-trap"))

    def test_trap_binary_sensor_uses_translated_state_directly(self):
        source = (INTEGRATION / "binary_sensor.py").read_text(encoding="utf-8")
        self.assertNotIn("_attr_device_class", source)
        self.assertIn("def is_on(self) -> bool | None:", source)
        self.assertIn("return self._state", source)

        expected_states = {
            "bg": {"off": "Готов", "on": "Уловено"},
            "cs": {"off": "Připravena", "on": "Chyceno"},
            "da": {"off": "Klar", "on": "Fanget"},
            "de": {"off": "Bereit", "on": "Gefangen"},
            "en": {"off": "Ready", "on": "Caught"},
            "es": {"off": "Lista", "on": "Capturado"},
            "et": {"off": "Valmis", "on": "Püütud"},
            "fi": {"off": "Valmis", "on": "Saalis"},
            "fr": {"off": "Prêt", "on": "Capturé"},
            "hr": {"off": "Spremna", "on": "Uhvaćeno"},
            "hu": {"off": "Kész", "on": "Elfogva"},
            "is": {"off": "Tilbúin", "on": "Fangað"},
            "it": {"off": "Pronta", "on": "Catturato"},
            "lt": {"off": "Paruošta", "on": "Sugauta"},
            "lv": {"off": "Gatavs", "on": "Noķerts"},
            "nb": {"off": "Klar", "on": "Fanget"},
            "nl": {"off": "Gereed", "on": "Gevangen"},
            "pl": {"off": "Gotowa", "on": "Złapano"},
            "pt": {"off": "Pronta", "on": "Capturado"},
            "ro": {"off": "Pregătită", "on": "Capturat"},
            "sk": {"off": "Pripravená", "on": "Chytené"},
            "sl": {"off": "Pripravljena", "on": "Ujeto"},
            "sv": {"off": "Redo", "on": "Fångad"},
            "uk": {"off": "Готова", "on": "Спіймано"},
        }
        for language, states in expected_states.items():
            translations = json.loads(
                (INTEGRATION / "translations" / f"{language}.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                translations["entity"]["binary_sensor"]["trap_status"]["state"],
                states,
            )

        translation_dir = INTEGRATION / "translations"
        self.assertEqual(
            {path.stem for path in translation_dir.glob("*.json")},
            set(expected_states),
        )

        def flatten_keys(value, prefix=""):
            keys = set()
            for key, child in value.items():
                path = f"{prefix}.{key}" if prefix else key
                if isinstance(child, dict):
                    keys.update(flatten_keys(child, path))
                else:
                    keys.add(path)
            return keys

        english = json.loads(
            (translation_dir / "en.json").read_text(encoding="utf-8")
        )
        expected_keys = flatten_keys(english)
        for language in expected_states:
            translations = json.loads(
                (translation_dir / f"{language}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(flatten_keys(translations), expected_keys, language)

    def test_sensor_platform_replays_late_observations(self):
        binary_source = (INTEGRATION / "binary_sensor.py").read_text(
            encoding="utf-8"
        )
        sensor_source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        self.assertIn("coordinator.update(", binary_source)
        self.assertIn("coordinator.register_listener(update_sensors)", sensor_source)

    def test_cached_status_is_rejected_and_last_seen_is_exposed(self):
        binary_source = (INTEGRATION / "binary_sensor.py").read_text(
            encoding="utf-8"
        )
        sensor_source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        self.assertIn(
            "is_fresh_advertisement(service_info.time, accept_after)", binary_source
        )
        self.assertIn("last_seen=datetime.now(UTC)", binary_source)
        self.assertIn("SensorDeviceClass.TIMESTAMP", sensor_source)
        self.assertIn('_attr_translation_key = "last_seen"', sensor_source)
        update_section, migration_section = sensor_source.split(
            "def _migrate_legacy_unique_id", maxsplit=1
        )
        self.assertIn("observation.last_seen", update_section)
        self.assertNotIn("observation.last_seen", migration_section)

    def test_trigger_history_entities_are_persistent_and_transition_based(self):
        init_source = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
        binary_source = (INTEGRATION / "binary_sensor.py").read_text(
            encoding="utf-8"
        )
        coordinator_source = (INTEGRATION / "coordinator.py").read_text(
            encoding="utf-8"
        )
        sensor_source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")

        self.assertIn("Store[TriggerHistoryStorage]", init_source)
        self.assertIn("store.async_delay_save", init_source)
        self.assertIn("is_tripped=frame.is_tripped", binary_source)
        self.assertIn(
            "previous_state is False and is_tripped is True", coordinator_source
        )
        self.assertIn('_attr_translation_key = "last_triggered"', sensor_source)
        self.assertIn('_attr_translation_key = "trigger_count"', sensor_source)
        self.assertIn(
            "_attr_state_class = SensorStateClass.TOTAL_INCREASING",
            sensor_source,
        )

    def test_repeated_manufacturer_advertisements_are_delivered(self):
        binary_source = (INTEGRATION / "binary_sensor.py").read_text(
            encoding="utf-8"
        )
        manifest = json.loads(
            (INTEGRATION / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            manifest["bluetooth"],
            [{"connectable": False, "manufacturer_id": 3003}],
        )
        self.assertIn("async_clear_advertisement_history", binary_source)
        self.assertGreaterEqual(
            binary_source.count(
                "_clear_advertisement_history(hass, service_info.address)"
            ),
            2,
        )

    def test_entities_have_stable_explicit_icons(self):
        binary_source = (INTEGRATION / "binary_sensor.py").read_text(
            encoding="utf-8"
        )
        sensor_source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        self.assertIn('_attr_icon = "mdi:rodent"', binary_source)
        self.assertIn('_attr_icon = "mdi:battery"', sensor_source)
        self.assertIn("_attr_suggested_display_precision = 2", sensor_source)
        self.assertIn('_attr_icon = "mdi:wifi"', sensor_source)
        self.assertIn(
            "_attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH",
            sensor_source,
        )


if __name__ == "__main__":
    unittest.main()
