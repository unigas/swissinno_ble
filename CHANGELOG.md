# Changelog

## 1.0.22

- Restored the explicit rodent icon for trap status.
- Added explicit battery and Wi-Fi icons so voltage and RSSI entities no longer
  depend on Home Assistant's generic default icons.
- Declared RSSI as a signal-strength sensor device class.

## 1.0.21

- Fixed a platform setup race where the status entity received Home Assistant's
  synchronously replayed Bluetooth advertisement before the battery and RSSI
  platform had registered its update callback.
- Added a shared observation coordinator that replays the latest real BLE data
  to late platform listeners, making signal strength available immediately and
  allowing battery stabilization to continue on the next advertisement.

## 1.0.20

- Fixed Connect SuperCat status decoding: byte 0 is the ready/triggered flag;
  byte 4 is part of the stable hardware ID and must not determine state.
- Replaced the misleading Problem/OK presentation with localized Caught/Ready
  labels while preserving the `on`/`off` states used by automations.
- Added regression coverage for status-like ID bytes (`idle`, `armed`,
  `triggered`, `kill`, and `ready`), actual Connect ready/triggered frames,
  electronic frames, legacy frames, and unknown statuses.
- Kept electronic high-voltage reset disabled while retaining reset for
  compatible Connect and legacy devices.
- Centralized MAC-based entity unique IDs and added non-destructive migration
  for legacy payload-based binary sensor, battery, RSSI, and reset IDs,
  including the shorter Connect identity emitted by version 1.0.14.
- Expanded protocol, identity migration, and troubleshooting documentation.

## 1.0.19

- Stabilized battery readings by requiring two consistent samples.
- Suppressed unsupported reset buttons for electronic high-voltage traps.
