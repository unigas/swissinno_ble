"""Tests for cross-platform trap observation replay."""

import importlib.util
import sys
import unittest
from pathlib import Path

COORDINATOR_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "swissinno_ble"
    / "coordinator.py"
)
BATTERY_PATH = COORDINATOR_PATH.with_name("battery.py")

spec = importlib.util.spec_from_file_location(
    "swissinno_observation_coordinator", COORDINATOR_PATH
)
coordinator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = coordinator
spec.loader.exec_module(coordinator)

battery_spec = importlib.util.spec_from_file_location(
    "swissinno_observation_battery", BATTERY_PATH
)
battery = importlib.util.module_from_spec(battery_spec)
sys.modules[battery_spec.name] = battery
battery_spec.loader.exec_module(battery)


class TrapObservationCoordinatorTests(unittest.TestCase):
    def test_replays_observation_to_late_listener(self):
        store = coordinator.TrapObservationCoordinator()
        observation = coordinator.TrapObservation(
            rssi=-61,
            battery_v=3.08,
            legacy_trap_ids=("5E100300", "3F5E10"),
        )
        store.update("cbbaeb6357fb", observation)

        received = []
        store.register_listener(
            lambda trap_id, value: received.append((trap_id, value))
        )

        self.assertEqual(received, [("cbbaeb6357fb", observation)])

    def test_publishes_future_observations_and_can_unsubscribe(self):
        store = coordinator.TrapObservationCoordinator()
        received = []
        remove = store.register_listener(
            lambda trap_id, value: received.append((trap_id, value))
        )
        observation = coordinator.TrapObservation(
            rssi=-70,
            battery_v=3.0,
            legacy_trap_ids=("DC140300",),
        )

        store.update("c8aedc738048", observation)
        remove()
        store.update("c8aedc738048", observation)

        self.assertEqual(received, [("c8aedc738048", observation)])

    def test_unavailable_state_is_replayed(self):
        store = coordinator.TrapObservationCoordinator()
        observation = coordinator.TrapObservation(
            rssi=-65,
            battery_v=3.1,
            legacy_trap_ids=("DC140300",),
        )
        store.update("c8aedc738048", observation)
        store.set_unavailable("c8aedc738048")

        received = []
        store.register_listener(lambda trap_id, value: received.append(value))

        self.assertEqual(len(received), 1)
        self.assertFalse(received[0].available)

    def test_replay_does_not_count_as_two_battery_advertisements(self):
        store = coordinator.TrapObservationCoordinator()
        stabilizer = battery.BatteryStabilizer()
        published = []
        observation = coordinator.TrapObservation(
            rssi=-61,
            battery_v=3.08,
            legacy_trap_ids=("5E100300",),
        )
        store.update("cbbaeb6357fb", observation)

        def listener(_trap_id, value):
            if (stable := stabilizer.update(value.battery_v)) is not None:
                published.append(stable)

        store.register_listener(listener)
        self.assertEqual(published, [])

        # A second real coordinator update confirms the stable battery value.
        store.update("cbbaeb6357fb", observation)
        self.assertEqual(published, [3.08])


if __name__ == "__main__":
    unittest.main()
