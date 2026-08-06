# Changelog

## 1.0.20

- Fixed Connect SuperCat status decoding: byte 0 is the ready/triggered flag;
  byte 4 is part of the stable hardware ID and must not determine state.
- Added regression coverage for status-like ID bytes (`idle`, `armed`,
  `triggered`, `kill`, and `ready`), actual Connect ready/triggered frames,
  electronic frames, legacy frames, and unknown statuses.
- Kept electronic high-voltage reset disabled while retaining reset for
  compatible Connect and legacy devices.
- Centralized MAC-based entity unique IDs and added non-destructive migration
  for legacy payload-based binary sensor, battery, RSSI, and reset IDs.
- Expanded protocol, identity migration, and troubleshooting documentation.

## 1.0.19

- Stabilized battery readings by requiring two consistent samples.
- Suppressed unsupported reset buttons for electronic high-voltage traps.
