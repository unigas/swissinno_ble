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
    def test_connect_ready_frame(self):
        frame = decoder.decode_frame(bytes.fromhex("00 3F CE 03 04 00 01 DA 03 00"))
        self.assertIsNotNone(frame)
        self.assertFalse(frame.is_tripped)
        self.assertEqual(frame.status, 0x00)
        self.assertEqual(frame.device_type, 0x01)
        self.assertIsNone(frame.event_counter)
        self.assertEqual(frame.trap_id, "CE030400")
        self.assertEqual(frame.legacy_trap_ids, ("CE030400", "3FCE03"))
        self.assertEqual(frame.battery_volts, 3.08)

    def test_connect_triggered_frame(self):
        frame = decoder.decode_frame(bytes.fromhex("01 3F CE 03 04 00 01 DA 03 00"))
        self.assertIsNotNone(frame)
        self.assertTrue(frame.is_tripped)
        self.assertEqual(frame.status, 0x01)
        self.assertEqual(frame.trap_id, "CE030400")

    def test_connect_id_bytes_are_not_interpreted_as_status(self):
        # These values were previously named idle/armed/triggered/kill/ready.
        # Byte 4 is actually part of payload[2:6], the stable hardware ID.
        status_like_id_bytes = {
            "idle": 0x00,
            "armed": 0x01,
            "triggered": 0x02,
            "kill": 0x03,
            "ready": 0x04,
        }
        for name, id_byte in status_like_id_bytes.items():
            with self.subTest(name=name):
                payload = bytes(
                    [
                        0x00,
                        0x3F,
                        0xCE,
                        0x03,
                        id_byte,
                        0x00,
                        0x01,
                        0xDA,
                        0x03,
                        0x00,
                    ]
                )
                frame = decoder.decode_frame(payload)
                self.assertIsNotNone(frame)
                self.assertFalse(frame.is_tripped)
                self.assertEqual(frame.status, 0x00)

    def test_reported_ready_traps_with_03_id_byte_are_not_problem(self):
        for payload_hex, expected_id in (
            ("00 3F DC 14 03 00 01 DA 03 00", "DC140300"),
            ("00 3F 5E 10 03 00 01 DA 03 00", "5E100300"),
        ):
            with self.subTest(trap_id=expected_id):
                frame = decoder.decode_frame(bytes.fromhex(payload_hex))
                self.assertIsNotNone(frame)
                self.assertFalse(frame.is_tripped)
                self.assertEqual(frame.trap_id, expected_id)

    def test_connect_unknown_status_is_unknown(self):
        frame = decoder.decode_frame(bytes.fromhex("02 3F CE 03 04 00 01 DA 03 00"))
        self.assertIsNotNone(frame)
        self.assertIsNone(frame.is_tripped)

    def test_newer_frame_ready(self):
        frame = decoder.decode_frame(bytes.fromhex("10 00 68 07 07 00 02 D4 01 00"))
        self.assertIsNotNone(frame)
        self.assertFalse(frame.is_tripped)
        self.assertEqual(frame.status, 0x00)
        self.assertEqual(frame.trap_id, "68070700")
        self.assertEqual(frame.battery_raw, 468)
        self.assertEqual(frame.battery_volts, 3.0)

    def test_newer_frame_triggered(self):
        frame = decoder.decode_frame(bytes.fromhex("40 00 68 07 07 00 02 D4 01 01"))
        self.assertIsNotNone(frame)
        self.assertTrue(frame.is_tripped)
        self.assertEqual(frame.status, 0x01)
        self.assertEqual(frame.trap_id, "68070700")
        self.assertEqual(frame.battery_raw, 468)
        self.assertEqual(frame.battery_volts, 3.0)

    def test_electronic_trap_does_not_offer_remote_reset(self):
        payload = bytes.fromhex("40 00 68 07 07 00 02 D4 01 01")
        self.assertFalse(decoder.supports_remote_reset(payload))

    def test_connect_trap_offers_remote_reset(self):
        payload = bytes.fromhex("00 3F CE 03 04 00 01 DA 03 00")
        self.assertTrue(decoder.supports_remote_reset(payload))

    def test_newer_frame_with_empty_trap_id_is_rejected(self):
        frame = decoder.decode_frame(bytes.fromhex("10 00 00 00 00 00 02 D4 01 00"))
        self.assertIsNone(frame)

    def test_short_frame_is_rejected(self):
        self.assertIsNone(decoder.decode_frame(b"\x01"))
        self.assertIsNone(decoder.decode_frame(b"\x01\x02\x03\x04\x05"))
        self.assertFalse(decoder.supports_remote_reset(b"\x01"))

    def test_legacy_frame(self):
        frame = decoder.decode_frame(bytes.fromhex("01 00 AA BB CC DD 00 FF"))
        self.assertIsNotNone(frame)
        self.assertTrue(frame.is_tripped)
        self.assertEqual(frame.trap_id, "AABBCCDD")
        self.assertEqual(frame.battery_volts, 3.6)

    def test_legacy_ready_frame(self):
        frame = decoder.decode_frame(bytes.fromhex("00 00 AA BB CC DD 00 FF"))
        self.assertIsNotNone(frame)
        self.assertFalse(frame.is_tripped)

    def test_address_identity_is_format_independent(self):
        self.assertEqual(const.normalized_address("AA:BB:CC:DD:EE:FF"), "aabbccddeeff")
        self.assertEqual(const.normalized_address("AA-BB-CC-DD-EE-FF"), "aabbccddeeff")
        self.assertEqual(
            const.entity_unique_id("C8:AE:DC:73:80:48"),
            "swissinno_trap_c8aedc738048",
        )
        self.assertEqual(
            const.entity_unique_id("CB:BA:EB:63:57:FB", "battery"),
            "swissinno_trap_cbbaeb6357fb_battery",
        )
        self.assertEqual(
            const.legacy_unique_ids("DC140300"),
            ("swissinno_trap_DC140300", "swissinno_trap_dc140300"),
        )
        self.assertEqual(
            const.legacy_unique_ids(("CE030400", "3FCE03")),
            (
                "swissinno_trap_CE030400",
                "swissinno_trap_ce030400",
                "swissinno_trap_3FCE03",
                "swissinno_trap_3fce03",
            ),
        )
        self.assertEqual(const.STATUS_READY, 0x00)
        self.assertEqual(const.STATUS_TRIGGERED, 0x01)
        self.assertFalse(hasattr(const, "STATUS_ARMED"))
        self.assertFalse(hasattr(const, "STATUS_KILL"))


if __name__ == "__main__":
    unittest.main()
