# Home Assistant – Systemair Modbus (SAVE)

**English** · [Les på norsk](README.no.md)

[![HACS](https://img.shields.io/badge/HACS-Default-green.svg)](https://hacs.xyz/)

This is a **Home Assistant integration for Systemair SAVE air handling units**
with support for **Modbus TCP**.

The integration provides structured monitoring and control of the ventilation
system in Home Assistant, with a focus on **correct airflow, energy-efficient
operation, and stable entity handling**.

⚠️ **Notice:**  
This is an **unofficial community project** and is **not developed, supported,
or maintained by Systemair**.

⚠️ **Disclaimer:**  
This integration is provided **as-is**, without any warranty of any kind.  
You use it **at your own risk**. The author is not responsible for any damage, data loss, or malfunction of your ventilation system, equipment, or property.

Always verify changes directly on the unit and ensure your system is correctly configured.  
If in doubt, consult a qualified technician.

---

## ✨ Features

### Ventilation and operation
- Display of actual operation based on the unit’s configuration
- Temperatures (outdoor, supply air, extract air, reheater, etc.)
- Fan speeds and operating status
- Heat recovery
- Filter status and alarms

### Energy efficiency
- **Eco mode**
- Demand-controlled ventilation (where supported by the unit)
- Away and Holiday modes
- Energy-efficient operation based on load and unit configuration

### Comfort
- **Free cooling** when conditions are met
- Party and Boost modes
- Manual fan speed control (Low / Normal / High)

### User experience
- Norwegian and English language support (follows Home Assistant language)
- Consistent and stable entities
- Built-in **buttons** for common actions
- Robust handling of temporary Modbus connection loss

---

## 📋 Systemair SAVE – supported models

**Airflow estimation (m³/h)** is only available for models that are explicitly defined in the code and share the expected Modbus register layout.

**Legend:**
- ✅ = Yes / available  
- ⚙️ = Supported, but not tested  
- ❌ = Not available  

> ⚠️ Note: Older units with **CD4 controller** may use a different Modbus register map than units with **SAVE Touch**.
> These units are not fully verified yet and may require adjustments. Please open an Issue if you test such a unit.

> Have you tested the integration with a model that is not marked as tested?
> Please let me know by opening an Issue so this list can be updated.

| Series | Model / Type | Modbus support | Airflow estimation (m³/h) | Tested |
|--------|--------------|----------------|----------------------------|--------|
| VSR | VSR 150/B | ✅ | ✅ | ❌ |
| VSR | VSR 200/B | ✅ | ✅ | ❌ |
| VSR | VSR 300 | ✅ | ✅ | ❌ |
| VSR | VSR 400 | ✅ | ✅ | ❌ |
| VSR | VSR 500 | ✅ | ✅ | ❌ |
| VSR | VSR 700 | ✅ | ✅ | ❌ |
| VTR | VTR 100/B | ✅ | ✅ | ❌ |
| VTR | VTR 150/B | ✅ | ✅ | ❌ |
| VTR | VTR 250/B | ✅ | ✅ | ❌ |
| VTR | VTR 275/B | ✅ | ✅ | ❌ |
| VTR | VTR 300 | ✅ | ✅ | ✅ |
| VTR | VTR 350/B | ✅ | ✅ | ❌ |
| VTR | VTR 500 | ✅ | ✅ | ✅ |
| VTR | VTR 700 | ✅ | ✅ | ❌ |
| VTC | VTC 200–1 | ✅ | ❌ | ❌ |
| VTC | VTC 300 | ✅ | ❌ | ❌ |
| VTC | VTC 500 | ✅ | ❌ | ❌ |
| VTC | VTC 700 | ✅ | ❌ | ❌ |
| VSC | VSC 100 | ✅ | ❌ | ❌ |
| VSC | VSC 200 | ✅ | ❌ | ❌ |
| VSC | VSC 300 | ✅ | ❌ | ❌ |

> ✅ VTR 300: Confirmed working by a community user (**SAVE Touch**, original Systemair Modbus gateway, Modbus TCP).  
> ✅ VTR 500: Confirmed working by a community user (tested with external Modbus TCP gateway).  
> ⚠️ CD4 units: Not verified yet and may require a different register map.

---

## 🏗️ Prerequisites – unit selection and airflow

This integration assumes that the ventilation system is **properly designed
and correctly dimensioned**.

- The air handling unit must be selected based on actual airflow requirements (m³/h)
- Airflows per zone must be correctly balanced and commissioned
- Home Assistant does **not** replace professional ventilation design

The integration builds on the unit’s existing configuration and provides:
- monitoring
- control
- automation

Incorrect unit selection or airflow configuration cannot be compensated for by software.

---

## 🖥️ Example Lovelace card

The image below shows an example Lovelace card built manually in Home Assistant
using entities provided by this integration.

> The card itself is **not included** and can be freely customized to suit your setup.

![Ventilation Card](image/Ventilasjon%20kort.png)

---

## 📦 Installation (HACS)

### Requirements
- Home Assistant **2024.6** or newer
- Systemair SAVE unit with Modbus access
- Modbus TCP  
  - Built-in to the unit **or**
  - Via an external gateway (e.g. Elfin EW11)
- HACS (Home Assistant Community Store)

---

### Method 1: Install via HACS (recommended)

1. Open **HACS**
2. Go to **Integrations**
3. Search for **Systemair Modbus**
4. Click **Download**
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add integration**
7. Select **Systemair Modbus** and enter:
   - IP address
   - Port (usually `502`)
   - Modbus slave ID

---

### Method 2: Install as a custom repository (manual)

> This method is mainly intended for development, testing, or early access to changes.

1. Open **HACS**
2. Go to **Integrations**
3. Open the menu (three dots) → **Custom repositories**
4. Add this repository as an **Integration**
5. Install **Systemair Modbus**
6. Restart Home Assistant
7. Go to **Settings → Devices & Services → Add integration**
8. Select **Systemair Modbus** and enter:
   - IP address
   - Port (usually `502`)
   - Modbus slave ID

---

## ℹ️ Limitations and technical notes

- **Pressure Guard** is an internal safety function of the unit  
  → exposed as status only (read-only)
- Not all SAVE models support full stop via Modbus  
  → where full stop is unavailable, the lowest possible fan speed is used
- Available features depend on unit model and configuration

---

## 🔌 Physical installation – Elfin EW11 (Modbus RTU → TCP)

This section is only relevant if the unit does **not** have built-in Modbus TCP.

### ⚠️ WARNING
Always disconnect power to the air handling unit before opening it.  
If unsure, contact a qualified professional.

### 1. Modbus connection on Systemair SAVE
Locate the external communication terminals on the main control board:
- `A (+)`
- `B (–)`
- `24V`
- `GND`

![Example wiring diagram (VTR-500)](image/koblingsskjemaVTR-500.png)

### 2. Connect the Elfin EW11
Wire the connections according to the diagram below:

![EW11 wiring diagram](image/koblings%20skjema%20EW11.png)

---

### 3. Configure the Elfin EW11

1. Connect to the Wi-Fi network `EW1x_...` (open network)
2. Open the web interface: `http://10.10.100.254`
3. Log in with:
   - Username: `admin`
   - Password: `admin`
4. Go to **System Settings → WiFi Settings**
   - Set **WiFi Mode** to `STA`
   - Connect to your local network
5. Restart the device and assign a **static IP**
6. Open **Serial Port Settings** and configure as shown:

![Serial Port Settings EW11](image/serial%20port%20settings%20EW11.png)

7. Open **Communication Settings** and add a Modbus profile:

![Communication Settings EW11](image/communication%20settings%20EW11.png)

8. Under **Status**, packet counters should increase:

![EW11 communication status](image/kommunikasjon%20EW11.png)

Once communication is confirmed, the IP address can be used directly in Home Assistant.

---

## 🙏 Acknowledgements

The Elfin EW11 (Modbus RTU → TCP) installation guide is based on work published on
[domotics.no](https://www.domotics.no/), written by **Mads Nedrehagen**.

An AI assistant has been used to support troubleshooting, refactoring,
and documentation improvements during development.

This integration is **independently developed** as a modern Home Assistant integration.

---

## 📝 License
MIT – see `LICENSE`
