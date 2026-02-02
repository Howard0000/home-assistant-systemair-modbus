# Home Assistant – Systemair Modbus (SAVE)

> [Les denne guiden på norsk](README.md)

This is a **Home Assistant integration for Systemair SAVE ventilation units**
using **Modbus TCP**.

⚠️ This is an unofficial community project and is not developed, supported, or
maintained by Systemair.

---

## ✨ Features

- Full monitoring of the ventilation unit
  - Temperatures, fan speeds, heat recovery, and alarms
- Mode and fan speed control
  - Auto, Manual (Low / Normal / High), Party, Boost, Away, and Holiday
- Built-in **action buttons** for common operations
- **Pressure Guard** exposed as a dedicated status (read-only safety function)
- Norwegian and English user interface (follows Home Assistant language settings)
- Robust handling of temporary Modbus connection loss

The image below shows an example of a Lovelace card that can be built manually
in Home Assistant using entities provided by this integration.
The card itself is not included with the integration.

![Ventilation Card Example](image/Ventilasjon%20kort.png)

---

## 📦 Installation (HACS)

### Requirements
- Home Assistant **2024.6** or newer
- Systemair SAVE unit with Modbus access
- Modbus TCP (built-in or via external gateway)
- HACS (Home Assistant Community Store)

### Installing the integration
1. Go to **HACS → Integrations**
2. Select **Custom repositories**
3. Add this repository as an **Integration**
4. Install **Systemair Modbus**
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration**
7. Select **Systemair Modbus** and enter:
   - IP address
   - Port (usually 502)
   - Modbus slave ID

---

## ℹ️ Important information

### Pressure Guard
Pressure Guard is an **internal safety function** in the ventilation unit and
cannot be manually enabled or disabled.
The integration only indicates whether Pressure Guard is **active or inactive**.

### Stop function
Not all Systemair units support a full stop via Modbus.
For this reason, **Stop** may be implemented as a *soft stop*
(low fan speed) when a full stop is not available.

---

## 🔌 Physical installation – Elfin EW11 (Modbus RTU → TCP)

This section is relevant **if the ventilation unit does not have built-in
Modbus TCP** and an external gateway is used, such as the **Elfin EW11**.

### ⚠️ WARNING
Always disconnect power to the ventilation unit before opening it.  
If unsure, consult a qualified professional.

### 1. Connect Modbus on the Systemair unit
Locate the external communication terminal on the main control board, labeled:
- `A(+)`
- `B(-)`
- `24V`
- `GND`

![Example wiring (VTR-500)](image/koblingsskjemaVTR-500.png)

### 2. Connect the Elfin EW11
Wire the Elfin EW11 according to the diagram below:

![Elfin EW11 wiring](image/koblings%20skjema%20EW11.png)

---

### 3. Configure the Elfin EW11

1. Connect to the Wi-Fi network `EW1x_...` (open network)
2. Open the web interface: `http://10.10.100.254`
3. Log in using:
   - Username: `admin`
   - Password: `admin`
4. Go to **System Settings → WiFi Settings**
   - Set **WiFi Mode** to `STA`
   - Connect to your home network
5. Restart the device and assign a **static IP address**
6. Go to **Serial Port Settings** and configure as shown:

![Serial Port Settings EW11](image/serial%20port%20settings%20EW11.png)

7. Go to **Communication Settings** and add a Modbus profile:

![Communication Settings EW11](image/communication%20settings%20EW11.png)

8. On the **Status** page, packet counters should start increasing:

![EW11 communication status](image/kommunikasjon%20EW11.png)

Once communication is confirmed, the IP address can be used directly in the
Home Assistant integration.

---

## 🙏 Acknowledgements

The Elfin EW11 (Modbus RTU → TCP) installation guide is based on work published on
[domotics.no](https://www.domotics.no/) by Mads Nedrehagen.

In addition, an AI assistant was used as a supporting tool for troubleshooting,
refactoring, and improving documentation during development.

This integration is **independently developed** as a modern Home Assistant
integration.

---

## 📝 License
MIT – see `LICENSE`.
