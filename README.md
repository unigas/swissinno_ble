# 🐀 SWISSINNO BLE Trap Integration for Home Assistant

A **custom Home Assistant integration** for **SWISSINNO Connect SuperCat and electronic SuperCat traps**, enabling real-time monitoring over Bluetooth Low Energy (BLE).

Supported Connect/legacy devices also expose **remote trap reset**. Electronic high-voltage traps require a physical power cycle for safety, as documented by SWISSINNO, and therefore do not expose a reset button.

![image](https://github.com/user-attachments/assets/99f7ad4c-0344-4547-89e7-5c4329c465a4)

---

If you like this integration please consider:  
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support%20Me!-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/unigas)

---

# 🚀 Features

### ✔️ Automatic BLE Scanning  
Detects traps instantly — no pairing or manual configuration required.

### ✔️ Trap Status Monitoring  
Real-time detection of **caught vs. ready** state.

### ✔️ Battery Voltage Sensor  
Accurate battery readings with automatic updates and transient-value filtering.

### ✔️ RSSI (Signal Strength) Sensor  
Helps you place traps for optimal Bluetooth coverage.

### ✔️ Remote BLE Reset
Supported Connect/legacy traps expose a **Reset Trap** button in Home Assistant.
Electronic high-voltage traps intentionally require switching off and on again.

### ✔️ Lovelace UI Support  
Includes example cards with icons, states, and reset control.

### ✔️ Fully Plug-and-Play  
No YAML needed. Everything is auto-discovered.

### ✔️ Localized UI
Setup, entity names, and Ready/Caught states are available in English, German,
French, Italian, Swedish, Norwegian Bokmål, Danish, Finnish, Icelandic,
Estonian, Latvian, Lithuanian, Polish, and Ukrainian.

---

# 📥 Installation

## 1️⃣ Manual Installation
1. Download (or clone) the `custom_components/swissinno_ble` folder.  
2. Place it inside your Home Assistant:  

```
config/custom_components/
```

3. Restart Home Assistant.  
4. Go to **Settings → Devices & Services → Add Integration → SWISSINNO BLE**.

---

## 2️⃣ HACS Installation
1. Open **HACS → Integrations**  
2. Click **+ Explore & Add Repositories**  
3. Add this repository:

```
https://github.com/unigas/swissinno_ble
```

4. Choose **Integration**  
5. Install and restart Home Assistant  
6. Add the integration from **Settings → Devices & Services**

The integration will immediately begin scanning for nearby traps.

---

# ⚙️ Configuration

No YAML configuration is needed.
When a trap is detected, Home Assistant creates a **Ready/Caught status**,
**battery voltage**, **Bluetooth signal strength**, and, for supported
Connect/legacy devices, a **Reset Trap** button.

The integration uses the following stable unique IDs internally:

| Entity | Unique ID |
| --- | --- |
| Status | `swissinno_trap_<MAC>` |
| Battery voltage | `swissinno_trap_<MAC>_battery` |
| Signal strength | `swissinno_trap_<MAC>_rssi` |
| Reset button | `swissinno_trap_<MAC>_reset` |

`<MAC>` is the Bluetooth address without separators, in lowercase. This makes
the unique identity stable when advertisement counters or state bytes change.
Upgrades migrate legacy payload-based unique IDs when possible and preserve the
existing Home Assistant entity ID. The visible `entity_id` can therefore differ
from the internal unique ID, especially after an upgrade or a manual rename.
Always copy the actual entity ID from Home Assistant when creating automations.
If both an old and a MAC-based entity already exist, the integration leaves both
registry entries untouched to avoid changing automations destructively; the
unavailable legacy duplicate can then be removed manually after the MAC-based
entity has been verified.

Home Assistant translates new entity names using the system/backend language at
the time each entity is created. Changing only a user's interface language does
not rename existing entities; their display names can be edited safely without
changing entity IDs or automations. See Home Assistant's
[entity naming documentation](https://developers.home-assistant.io/docs/core/entity/#entity-naming).

## Advertisement status formats

SWISSINNO devices use two observed 10-byte formats:

| Family | Marker | Status field | Ready (`off`) | Caught (`on`) |
| --- | --- | --- | --- | --- |
| Connect SuperCat | byte 6 = `0x01` | byte 0 | `0x00` | `0x01` |
| Electronic SuperCat | byte 6 = `0x02` | byte 9 | `0x00` | `0x01` |

For Connect frames, bytes 2–5 are the stable hardware ID. They are not a
counter/status field. Unknown status values are reported as unknown instead of
being guessed as ready or triggered.

---

# 🔘 Reset Trap (BLE Write Support)

Supported Connect/legacy devices include a **Reset Trap** button entity that resets the catch sensor using Bluetooth. SWISSINNO disables app reset on electronic high-voltage traps for safety, so the integration does not create a reset button for those devices.

### BLE Command Details
- **Characteristic UUID:** `02ECC6CD-2B43-4DB5-96E6-EDE92CF8778D`  
- **Payload:** `0x00`  
- **Transport:** Home Assistant Bluetooth (supports proxies like ESPHome)

### Example Automation

```yaml
alias: Auto Reset Trap After Notification
trigger:
  - platform: event
    event_type: mobile_app_notification_action
    event_data:
      action: reset_kitchen_trap
action:
  - service: button.press
    target:
      entity_id: button.your_trap_reset
```

Replace `button.your_trap_reset` with the actual reset-button entity ID shown by
Home Assistant.

---

# 📊 Lovelace Dashboard Example

```yaml
type: entities
title: 🐀 SWISSINNO Trap — Kitchen
show_header_toggle: false
entities:
  - entity: binary_sensor.your_trap_status
    name: Trap Status
    state_color: true
    icon: mdi:rodent

  - entity: sensor.your_trap_battery_voltage
    name: Battery Level

  - entity: sensor.your_trap_signal_strength
    name: Signal Strength

  - entity: button.your_trap_reset
    name: Reset Trap
```

Replace the placeholder entity IDs with the actual IDs shown by Home Assistant.
No custom Lovelace card is required; battery voltage suggests two decimal places
from version 1.0.23 onward.

---

# 🛠 Troubleshooting

### ❓ No traps found?
- Ensure Bluetooth is enabled  
- ESPHome BLE proxies must be online  
- Try restarting Home Assistant  

### ❓ Wrong battery level?
Connect/legacy traps use a one-byte battery value:

```
Voltage = (raw * 3.6) / 255
```

Electronic traps use a two-byte little-endian value:

```
Voltage = raw / 156
```

Version 1.0.23 and later suggest two decimal places, so a decoded reading such
as 2.37 V is no longer normally displayed as 2 V.

### ❓ Trap state updates slowly?
Move the trap closer to the receiver or use more BLE proxies.

### ❓ Battery voltage or signal strength stays unavailable after a reload?
Version 1.0.21 fixes a platform setup race that could make battery and RSSI miss
Home Assistant's cached Bluetooth advertisement while trap status was already
available. RSSI is restored from that advertisement immediately. Battery still
requires two matching real advertisements before its first value is published,
which prevents transient startup readings from being shown as valid.

### ❓ The official app says ready but Home Assistant says caught?
Version 1.0.20 fixes a Connect-frame decoder bug present in 1.0.19. Upgrade the
integration and reload it before changing automations. Home Assistant displays
the states as **Ready/Caught** (localized in the supported languages); their
automation values remain `off`/`on`.

If old payload-based and new MAC-based entities were both created before the
upgrade, Home Assistant can show more devices than physically exist. Verify the
MAC-based entities first, update any automations that still use old entity IDs,
then remove only the unavailable legacy duplicates from Home Assistant.

---

# 🤝 Contributing

Contributions are welcome!
- Found a bug? Open an issue.  
- Want a new feature? Create a pull request.  
- Improvements to decoding or UI are highly appreciated.  

---

# 📜 License

**MIT License** — free to modify and redistribute.

---

# 📢 Need Help?

Open an issue on GitHub or reach out via Home Assistant forums.  
Happy automating, and enjoy smarter pest control! 🐭✨
