"""Tests for SWISSINNO advertisement decoding and identity."""

import importlib.util
import sys
import unittest
from pathlib import Path

COMPONENT_DIR = Path(__file__).parents[1] / "custom_components" / "swissinno_ble"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, COMPONENT_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


decoder = load_module("decoder")
const = load_module("const")


class DecoderTests(unittest.TestCase):
    def test_new_frame(self):
        frame = decoder.decode_frame(bytes.fromhex("00 3F CE 03 04 00 01 DA 03 00"))
        self.assertIsNotNone(frame)
        self.assertFalse(frame.is_tripped)
        self.assertEqual(frame.event_counter, 0x03CE)
        self.assertEqual(frame.battery_volts, 3.08)

    def test_short_frame_is_rejected(self):
        self.assertIsNone(decoder.decode_frame(b"\x01"))
        self.assertIsNone(decoder.decode_frame(b"\x01\x02\x03\x04\x05"))

    def test_legacy_frame(self):
        frame = decoder.decode_frame(bytes.fromhex("01 00 AA BB CC DD 00 FF"))
        self.assertIsNotNone(frame)
        self.assertTrue(frame.is_tripped)
        self.assertEqual(frame.trap_id, "AABBCCDD")
        self.assertEqual(frame.battery_volts, 3.6)

    def test_address_identity_is_format_independent(self):
        self.assertEqual(const.normalized_address("AA:BB:CC:DD:EE:FF"), "aabbccddeeff")
        self.assertEqual(const.normalized_address("AA-BB-CC-DD-EE-FF"), "aabbccddeeff")


if __name__ == "__main__":
    unittest.main()
