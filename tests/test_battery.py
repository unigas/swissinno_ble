"""Tests for battery reading stabilization."""

import importlib.util
import sys
import unittest
from pathlib import Path

BATTERY_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "swissinno_ble"
    / "battery.py"
)

spec = importlib.util.spec_from_file_location("swissinno_battery", BATTERY_PATH)
battery = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = battery
spec.loader.exec_module(battery)


class BatteryStabilizerTests(unittest.TestCase):
    def test_requires_two_consistent_readings(self):
        stabilizer = battery.BatteryStabilizer()
        self.assertIsNone(stabilizer.update(2.96))
        self.assertEqual(stabilizer.update(2.97), 2.97)

    def test_transient_dip_does_not_replace_stable_value(self):
        stabilizer = battery.BatteryStabilizer()
        self.assertIsNone(stabilizer.update(2.96))
        self.assertEqual(stabilizer.update(2.96), 2.96)
        self.assertIsNone(stabilizer.update(1.64))
        self.assertIsNone(stabilizer.update(2.96))
        self.assertEqual(stabilizer.update(2.96), 2.96)

    def test_zero_and_non_finite_values_are_ignored(self):
        stabilizer = battery.BatteryStabilizer()
        self.assertIsNone(stabilizer.update(2.96))
        self.assertIsNone(stabilizer.update(0.0))
        self.assertIsNone(stabilizer.update(2.96))
        self.assertEqual(stabilizer.update(2.96), 2.96)
        self.assertIsNone(stabilizer.update(float("nan")))
        self.assertIsNone(stabilizer.update(float("inf")))


if __name__ == "__main__":
    unittest.main()
