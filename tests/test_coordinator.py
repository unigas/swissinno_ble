"""Tests for cross-platform trap observation replay."""

import importlib.util
import sys
import unittest
from datetime import UTC, datetime, timedelta
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
    def test_counts_only_confirmed_ready_to_triggered_transitions(self):
        saved = []
        store = coordinator.TrapObservationCoordinator(
            save_trigger_history=saved.append
        )
        received = []
        store.register_listener(
            lambda _trap_id, observation: received.append(observation)
        )
        started = datetime(2026, 8, 12, 8, 0, tzinfo=UTC)

        states = (False, False, True, True, None, False, True)
        for offset, state in enumerate(states):
            store.update(
                "c8aedc738048",
                coordinator.TrapObservation(
                    rssi=-60,
                    battery_v=3.0,
                    legacy_trap_ids=("DC140300",),
                    last_seen=started + timedelta(minutes=offset),
                ),
                is_tripped=state,
            )

        first_triggered = started + timedelta(minutes=2)
        second_triggered = started + timedelta(minutes=6)
        self.assertEqual(
            [observation.trigger_count for observation in received],
            [0, 0, 1, 1, 1, 1, 2],
        )
        self.assertEqual(received[2].last_triggered, first_triggered)
        self.assertEqual(received[4].last_triggered, first_triggered)
        self.assertEqual(received[-1].last_triggered, second_triggered)
        self.assertEqual(len(saved), 2)
        self.assertEqual(saved[-1]["c8aedc738048"]["trigger_count"], 2)

    def test_first_triggered_observation_after_reload_is_not_counted(self):
        previous_trigger = datetime(2026, 8, 11, 20, 0, tzinfo=UTC)
        history = {
            "cbbaeb6357fb": coordinator.TriggerHistory(previous_trigger, 4)
        }
        store = coordinator.TrapObservationCoordinator(history)
        received = []
        store.register_listener(
            lambda _trap_id, observation: received.append(observation)
        )

        def update(state, minute):
            store.update(
                "cbbaeb6357fb",
                coordinator.TrapObservation(
                    rssi=-65,
                    battery_v=3.1,
                    legacy_trap_ids=("5E100300",),
                    last_seen=previous_trigger + timedelta(minutes=minute),
                ),
                is_tripped=state,
            )

        update(True, 1)
        update(False, 2)
        update(True, 3)

        self.assertEqual([value.trigger_count for value in received], [4, 4, 5])
        self.assertEqual(received[0].last_triggered, previous_trigger)
        self.assertEqual(
            received[-1].last_triggered,
            previous_trigger + timedelta(minutes=3),
        )

    def test_trigger_history_storage_round_trip_and_validation(self):
        last_triggered = datetime(2026, 8, 12, 8, 30, tzinfo=UTC)
        history = {
            "c8aedc738048": coordinator.TriggerHistory(last_triggered, 3)
        }
        serialized = coordinator.trigger_history_to_storage(history)

        self.assertEqual(
            coordinator.trigger_history_from_storage(serialized), history
        )
        self.assertEqual(
            coordinator.trigger_history_from_storage(
                {
                    "bad_count": {"trigger_count": -1},
                    "bad_time": {
                        "trigger_count": 1,
                        "last_triggered": "not-a-time",
                    },
                }
            ),
            {},
        )

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

    def test_unavailable_state_preserves_last_seen(self):
        store = coordinator.TrapObservationCoordinator()
        last_seen = datetime(2026, 8, 11, 14, 30, tzinfo=UTC)
        store.update(
            "c8aedc738048",
            coordinator.TrapObservation(
                rssi=-65,
                battery_v=3.1,
                legacy_trap_ids=("DC140300",),
                last_seen=last_seen,
            ),
        )
        store.set_unavailable("c8aedc738048")

        received = []
        store.register_listener(lambda _trap_id, value: received.append(value))

        self.assertEqual(received[0].last_seen, last_seen)
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
