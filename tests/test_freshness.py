"""Tests for Bluetooth advertisement freshness filtering."""

import importlib.util
import unittest
from pathlib import Path

FRESHNESS_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "swissinno_ble"
    / "freshness.py"
)

spec = importlib.util.spec_from_file_location("swissinno_freshness", FRESHNESS_PATH)
freshness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freshness)


class AdvertisementFreshnessTests(unittest.TestCase):
    def test_cached_advertisement_is_rejected(self):
        self.assertFalse(freshness.is_fresh_advertisement(99.9, 100.0))

    def test_current_advertisement_is_accepted(self):
        self.assertTrue(freshness.is_fresh_advertisement(100.0, 100.0))
        self.assertTrue(freshness.is_fresh_advertisement(100.1, 100.0))


if __name__ == "__main__":
    unittest.main()
