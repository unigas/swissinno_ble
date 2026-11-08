"""Tests for diagnostic update throttling."""

import importlib.util
import sys
import unittest
from pathlib import Path

THROTTLE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "swissinno_ble"
    / "throttle.py"
)

spec = importlib.util.spec_from_file_location("swissinno_throttle", THROTTLE_PATH)
throttle = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = throttle
spec.loader.exec_module(throttle)


class UpdateThrottleTests(unittest.TestCase):
    def test_publishes_first_update_then_once_per_interval(self):
        limiter = throttle.UpdateThrottle(60)

        self.assertTrue(limiter.ready(1000.0))
        self.assertFalse(limiter.ready(1001.0))
        self.assertFalse(limiter.ready(1059.9))
        self.assertTrue(limiter.ready(1060.0))
        self.assertFalse(limiter.ready(1061.0))

    def test_reset_publishes_next_update_immediately(self):
        limiter = throttle.UpdateThrottle(60)

        self.assertTrue(limiter.ready(1000.0))
        limiter.reset()
        self.assertTrue(limiter.ready(1001.0))


if __name__ == "__main__":
    unittest.main()
