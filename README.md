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
Real-time detection of **triggered vs. ready** state.

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
When a trap is detected, the following entities are created automatically:

### Entities per trap:
- `binary_sensor.swissinno_trap_<MAC>` – **Trap triggered / ready**
- `sensor.swissinno_battery_<MAC>` – **Battery voltage**
- `sensor.swissinno_rssi_<MAC>` – **Bluetooth signal strength**
- `button.swissinno_trap_<MAC>_reset` – **Reset Trap** (supported Connect/legacy devices only)

`<MAC>` is the Bluetooth address without separators, in lowercase. This makes
the unique identity stable when advertisement counters or state bytes change.
Upgrades migrate legacy payload-based unique IDs when possible and preserve the
existing Home Assistant entity ID. If both an old and a MAC-based entity already
exist, the integration leaves both registry entries untouched to avoid changing
automations destructively; the unavailable legacy duplicate can then be removed
manually after the MAC-based entity has been verified.

## Advertisement status formats

SWISSINNO devices use two observed 10-byte formats:

| Family | Marker | Status field | Ready | Triggered |
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
      entity_id: button.swissinno_trap_c8aedc738048_reset
```

Replace `c8aedc738048` with your trap's normalized Bluetooth address.

---

# 📊 Lovelace Dashboard Example

```yaml
type: entities
title: 🐀 SWISSINNO Trap — Kitchen
show_header_toggle: false
entities:
  - entity: binary_sensor.swissinno_trap_c8aedc738048
    name: Trap Status
    state_color: true
    icon: mdi:rodent

  - type: custom:template-entity-row
    entity: sensor.swissinno_battery_c8aedc738048
    name: Battery Level
    state: "{{ states('sensor.swissinno_battery_DC140300') | round(2) }} V"

  - entity: sensor.swissinno_rssi_c8aedc738048
    name: Signal Strength

  - entity: button.swissinno_trap_c8aedc738048_reset
    name: Reset Trap
```

💡 Tip: Install **Lovelace Template Entity Row** via HACS.

---

# 🛠 Troubleshooting

### ❓ No traps found?
- Ensure Bluetooth is enabled  
- ESPHome BLE proxies must be online  
- Try restarting Home Assistant  

### ❓ Wrong battery level?
Correct conversion formula:

```
Voltage = (raw * 3.6) / 255
```

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

# 🧭 Roadmap

✔️ BLE Trap Reset Support (v1.0.12)  


---

# 📢 Need Help?

Open an issue on GitHub or reach out via Home Assistant forums.  
Happy automating, and enjoy smarter pest control! 🐭✨
