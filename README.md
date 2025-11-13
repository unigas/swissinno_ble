# 🐀 SWISSINNO BLE Trap Integration for Home Assistant

A **custom Home Assistant integration** for the **SWISSINNO Connect SuperCat**, enabling real-time monitoring **and wireless control** of your mousetraps over Bluetooth Low Energy (BLE).

This integration now supports **remote trap reset**, allowing you to reset a trap from *“Caught” → “Ready”* without touching it.

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
Accurate battery readings with automatic updates.

### ✔️ RSSI (Signal Strength) Sensor  
Helps you place traps for optimal Bluetooth coverage.

### ✔️ **NEW: Remote BLE Reset**  
Each trap now exposes a **Reset Trap** button in Home Assistant.  
Pressing it sends a BLE write command to clear the “caught” state via GATT.

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
- `binary_sensor.swissinno_trap_<ID>` – **Trap triggered / ready**
- `sensor.swissinno_battery_<ID>` – **Battery voltage**
- `sensor.swissinno_rssi_<ID>` – **Bluetooth signal strength**
- `button.swissinno_trap_<ID>_reset` – **Reset Trap** (BLE GATT write)

---

# 🔘 Reset Trap (BLE Write Support)

Each trap includes a **Reset Trap** button entity that resets the device using Bluetooth.

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
      entity_id: button.swissinno_trap_DC140300_reset
```

Replace `DC140300` with your own trap ID.

---

# 📊 Lovelace Dashboard Example

```yaml
type: entities
title: 🐀 SWISSINNO Trap — Kitchen
show_header_toggle: false
entities:
  - entity: binary_sensor.swissinno_trap_DC140300
    name: Trap Status
    state_color: true
    icon: mdi:rodent

  - type: custom:template-entity-row
    entity: sensor.swissinno_battery_DC140300
    name: Battery Level
    state: "{{ states('sensor.swissinno_battery_DC140300') | round(2) }} V"

  - entity: sensor.swissinno_rssi_DC140300
    name: Signal Strength

  - entity: button.swissinno_trap_DC140300_reset
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
