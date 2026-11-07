"""Tests for payload-ID based trap identity."""

import importlib.util
import sys
import unittest
from pathlib import Path

IDENTITY_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "swissinno_ble"
    / "identity.py"
)

spec = importlib.util.spec_from_file_location("swissinno_identity", IDENTITY_PATH)
identity = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = identity
spec.loader.exec_module(identity)


class TrapIdentityMapTests(unittest.TestCase):
    def test_first_address_becomes_canonical_and_is_saved(self):
        saved = []
        identities = identity.TrapIdentityMap({}, saved.append)

        self.assertEqual(
            identities.resolve("9E010400", "cdfe65e69f48"), "cdfe65e69f48"
        )
        self.assertEqual(saved, [{"9E010400": "cdfe65e69f48"}])

    def test_changed_or_corrupted_address_maps_to_existing_trap(self):
        saved = []
        identities = identity.TrapIdentityMap(
            {"9E010400": "cdfe65e69f48"}, saved.append
        )

        for address in (
            "cd23cde174c1",
            "cdfe65e68f48",
            "cafe65869f48",
            "f09e9e453d0a",
        ):
            self.assertEqual(
                identities.resolve("9E010400", address), "cdfe65e69f48"
            )
        self.assertEqual(saved, [])

    def test_distinct_payload_ids_remain_separate_traps(self):
        identities = identity.TrapIdentityMap({}, lambda _data: None)

        self.assertEqual(
            identities.resolve("9E010400", "cdfe65e69f48"), "cdfe65e69f48"
        )
        self.assertEqual(
            identities.resolve("3FCE0304", "c8aedc738048"), "c8aedc738048"
        )

    def test_invalid_storage_is_ignored(self):
        self.assertEqual(identity.identities_from_storage(None), {})
        self.assertEqual(
            identity.identities_from_storage({"9E010400": "cdfe65e69f48", 1: 2}),
            {"9E010400": "cdfe65e69f48"},
        )


if __name__ == "__main__":
    unittest.main()
