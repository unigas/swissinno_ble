# Changelog

## 1.0.30

- Corrected Electronic SuperCat battery decoding to use its battery-related
  byte on an estimated 0–6 V scale. The following byte is no longer treated as
  a battery high byte because captures show it changes after app configuration
  writes without a corresponding battery change.
- Added regression coverage for Electronic configuration-byte changes and the
  battery ordering observed in the official SWISSINNO app.
- Added a persistent Last triggered timestamp and Trigger count for every trap.
- Count only confirmed Ready-to-Caught transitions; repeated caught packets and
  the initial state after setup or reload do not create false trigger events.
- Marked Trigger count as a total-increasing sensor for Home Assistant long-term
  statistics.
- Added localized entity names in all 24 supported languages and documented
  built-in Home Assistant device triggers and resettable Counter helpers.
- Show Connect SuperCat, Electronic SuperCat or the legacy protocol family as
  the device model in Home Assistant.
- Include the complete manufacturer payload in debug logs so unknown status or
  fault advertisements can be investigated without adding permanent logging.

## 1.0.29

- Restricted manual device removal to stale legacy payload-ID devices.
- Protected active MAC-based devices from removal while their runtime entities
  are loaded, ensuring they cannot disappear until the integration is reloaded.

## 1.0.28

- Added Home Assistant device-removal support for dynamically discovered traps.
- Users can now delete stale legacy payload-ID devices from the device page
  without removing the integration or affecting current MAC-based devices.
- Accepts manufacturer-only proxy advertisements and clears Home Assistant's
  deduplication history after valid packets so repeated advertisements update
  Last seen and RSSI on supported Home Assistant versions.
- Added regression coverage and cleanup instructions for legacy duplicates.

## 1.0.27

- Ignore Bluetooth history cached before integration setup so trap status and
  RSSI remain unavailable until a fresh advertisement is received.
- Added a diagnostic Last seen timestamp that updates for every valid fresh
  advertisement and remains visible when the trap becomes unavailable.
- Kept battery voltage unavailable until two consistent fresh samples confirm
  the reading.
- Added Last seen translations for all 24 supported languages and regression
  coverage for cached-advertisement filtering and timestamp retention.

## 1.0.26

- Added a packaged integration ZIP to every new GitHub release and configured
  HACS to install that counted release asset.
- Added a public total release-download badge to the README.
- Added regression coverage for the release packaging and HACS ZIP settings.

## 1.0.25

- Added complete Dutch, Spanish, Portuguese, Czech, Romanian, Hungarian,
  Slovak, Bulgarian, Slovenian, and Croatian translations.
- Expanded translation parity and Ready/Caught state tests to all 24 supported
  languages.

## 1.0.24

- Added complete Norwegian Bokmål, Danish, Finnish, Icelandic, Estonian,
  Latvian, Lithuanian, Polish, and Ukrainian translations.
- Documented all supported languages and Home Assistant's entity-name language
  behavior.
- Corrected stale entity examples and documented the separate battery formulas
  used by Connect/legacy and electronic traps.

## 1.0.23

- Suggested two decimal places for battery voltage so Home Assistant displays
  readings such as 2.37 V instead of rounding them to 2 V.

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
