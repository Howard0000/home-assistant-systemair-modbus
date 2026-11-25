# 🌬️ Systemair Modbus v2.0.0 — One integration. Two protocols. 🚀

**English** · [Les på norsk](README.no.md)

[![HACS](https://img.shields.io/badge/HACS-Default-green.svg)](https://hacs.xyz/) ![Version](https://img.shields.io/badge/Version-2.0.0-blue) ![Modbus TCP](https://img.shields.io/badge/Modbus-TCP%2FIP-0A7EA4) ![Modbus RTU](https://img.shields.io/badge/Modbus-RTU-0A7EA4)

### 🎉 A major milestone for Systemair Modbus

**Modbus TCP/IP + Modbus RTU — together in one Home Assistant integration.**

Version **2.0.0** introduces serial Modbus RTU communication alongside the existing TCP/IP connection, while continuing to support **Systemair SAVE** and **legacy CD4 (experimental)** controllers.

- 🌐 **Modbus TCP/IP:** Connect through an Ethernet/Wi-Fi gateway such as Elfin EW11 or a compatible Systemair gateway.
- 🔌 **Modbus RTU:** Connect through an ESPHome serial interface, including Home Assistant Connect AUX-2 with a USB–RS485 adapter and ESP32-based RS485 devices with a compatible ESPHome serial proxy.
- 🏠 **One integration:** Familiar Home Assistant entities and controls, regardless of connection method, where supported by the controller.
- 🛠️ **Better documentation:** Dedicated [TCP/IP](docs/modbus-tcp.md) and [RTU](docs/modbus-rtu.md) setup guides.

The integration provides monitoring and control of Systemair ventilation units, with an emphasis on reliable communication, energy-efficient operation and stable entities. Features vary by model and configuration; see the compatibility table below for physically verified connections.

⚠️ **Notice:**\
This is an **unofficial community project** and is **not developed,
supported, or maintained by Systemair**.

⚠️ **Disclaimer:**\
This integration is provided **as-is**, without any warranty of any
kind.\
You use it **at your own risk**. The author is not responsible for any
damage, data loss, or malfunction of your ventilation system, equipment,
or property.

Always verify changes directly on the unit and ensure your system is
correctly configured.\
If in doubt, consult a qualified technician.

------------------------------------------------------------------------

## ✨ Features

### Ventilation and operation

-   Display of actual operation based on the unit's configuration
-   Temperatures (outdoor, supply air, extract air, reheater, etc.)
-   Fan speeds and operating status
-   Heat recovery
-   Filter status, remaining time and alarms
-   Proper filter reset (writes timestamp to the unit)
-   Configurable filter replacement period

### Energy efficiency

-   **Eco mode**
-   Demand-controlled ventilation (where supported by the unit)
-   Away and Holiday modes
-   Energy-efficient operation based on load and unit configuration

### Comfort

-   **Free cooling** when conditions are met
-   Party and Boost modes
-   Manual fan speed control (Low / Normal / High)
-   Writable supply air temperature setpoint
-   Calculated exhaust air temperature (derived from system values)

-   Adjustable Fireplace mode duration (SAVE, 1–60 minutes)

### User experience

-   Norwegian and English language support (follows Home Assistant
    language)
-   Consistent and stable entities
-   Built-in **buttons** for common actions
-   Robust handling of temporary Modbus connection loss

------------------------------------------------------------------------

## New in v2.0.0

- Automatic model identification for SAVE and CD4, with model names in device information when available.
- Human-readable heater type for CD4.
- Adjustable Fireplace mode duration (SAVE, 1–60 minutes).
- Eco heating offset (SAVE): 0–10 °C where the register is supported.
- Slave ID 1–247 for TCP and RTU; default 1.

## 🚀 Previous improvements (v1.3.0)

v1.3.0 includes major improvements for both SAVE and legacy CD4 systems:

-   Improved SAVE heater / after-heating status and output entities
-   Improved ECO enabled / active presentation and diagnostics
-   Expanded Free Cooling controls and diagnostics
-   Added Auto / Demand Control diagnostic entities
-   Reduced the default polling interval from 10 to 30 seconds to reduce
    Modbus load and potentially improve physical touch-display stability
-   Significantly expanded legacy CD4 support
-   Native CD4 Fan entity with safe handling of manual fan stop
-   Updated CD4 Climate entity with automatic temperature range based on heater configuration
    -   12--22 °C with a configured heater
    -   15--19 °C without a configured heater
-   CD4 Manual summer / temperature OFF support
-   Expanded CD4 diagnostic register coverage

The integration is under active development with a strong focus on
correctness, stability and transparent entity behavior.

## 📋 Supported models and test status

See the compatibility table below for SAVE and CD4 models, TCP/IP, RTU and airflow estimation.

### 🧪 CD4 (legacy) -- experimental support

Support for older Systemair units using the **CD4 controller** is
included in the integration and has been significantly expanded in
v1.3.0.

⚠️ **Important:**

-   CD4 uses a different Modbus register map than SAVE
-   Support remains **experimental** while testing on real units
    continues
-   Available features may vary between legacy unit models and
    configurations

### What currently works

-   Native Home Assistant **Fan entity** for fan control
    -   Off / Low / Medium / High
    -   Off is only available when manual fan stop is supported by the unit
-   Native Home Assistant **Climate entity**
    -   Supply-air temperature control with an automatically selected range:
        -   12--22 °C with a configured heater
        -   15--19 °C without a configured heater
    -   Off / Manual summer mode
    -   Current supply-air temperature
    -   Fan mode control directly from the Climate entity
    -   Heating state based on actual reheater status
-   Supply, extract, exhaust, outdoor and overheat/frost-protection
    temperatures
-   Actual SF / EF RPM values
-   Rotor, reheater, defrost and alarm status
-   Filter status and basic system values
-   Technical and raw CD4 values are available as diagnostic entities
    where appropriate

**Climate Off and Fan Off are separate functions.**

Climate Off sets the CD4 temperature regulation to Manual summer /
temperature OFF. It does **not** stop the ventilation fans.

Fan Off is only available when the unit reports that manual fan stop is
supported.

### Testing and feedback

Legacy CD4 support has been tested extensively on physical VSR 500/CD4
hardware for v1.3.0.

The following behaviour has been verified on real hardware:

-   Bidirectional temperature control between Home Assistant and the CD4 controller
-   Climate Off / Manual summer mode and return to temperature control
-   Automatic temperature range based on heater configuration:
    -   12--22 °C with the electrical heater enabled/configured
    -   15--19 °C without the electrical heater enabled/configured
-   Heat-recovery status reflecting physical operation of the unit
-   Electrical reheater status reflecting physical operation
-   Fan control and relevant sensor values

CD4 remains marked as experimental because legacy units and configurations
may differ. Additional reports from other CD4-based systems are therefore
still very welcome.

Please report both successful tests and unexpected behaviour via GitHub
Issues.

----------------------------------------------------------------------
 ## ✅ Tested units / compatibility

**✅ = physically tested connection. — = no confirmed physical test (does not mean unsupported).**

**Airflow estimation** indicates a model-specific calculation is available in the integration, not that it has been independently verified against measured airflow. In particular, the maximum airflow value for VTR 300 SAVE has not been independently verified. This calculation is not available for CD4.

| Series | Model / type | Controller | TCP/IP tested | RTU tested | Airflow estimation (m³/h) |
|---|---|---|:---:|:---:|:---:|
| VSR | VSR 150 | CD4 | — | — | ❌ |
| VSR | VSR 150/B | SAVE | — | — | ✅ |
| VSR | VSR 200/B | SAVE | — | — | ✅ |
| VSR | VSR 300 | SAVE | ✅ | — | ✅ |
| VSR | VSR 300 | CD4 | — | — | ❌ |
| VSR | VSR 300DE | CD4 | — | — | ❌ |
| VSR | VSR 400 | SAVE | — | — | ✅ |
| VSR | VSR 500 | SAVE | — | — | ✅ |
| VSR | VSR 500 | CD4 | ✅ | — | ❌ |
| VSR | VSR 700 | SAVE | — | — | ✅ |
| VTR | VTR 100/B | SAVE | — | — | ✅ |
| VTR | VTR 150K | SAVE | — | — | ✅ |
| VTR | VTR 150K | CD4 | ✅ | — | ❌ |
| VTR | VTR 150/B | SAVE | — | — | ✅ |
| VTR | VTR 200B | CD4 | — | — | ❌ |
| VTR | VTR 250/B | SAVE | ✅ | — | ✅ |
| VTR | VTR 275/B | SAVE | — | — | ✅ |
| VTR | VTR 300 | SAVE | ✅ | — | ✅ |
| VTR | VTR 300 | CD4 | — | — | ❌ |
| VTR | VTR 350/B | SAVE | ✅ | — | ✅ |
| VTR | VTR 500 | SAVE | ✅ | ✅ | ✅ |
| VTR | VTR 500 | CD4 | — | — | ❌ |
| VTR | VTR 700 | SAVE | — | — | ✅ |
| VTC | VTC 100 | CD4 | — | — | ❌ |
| VTC | VTC 200 | CD4 | — | — | ❌ |
| VTC | VTC 200-1 | SAVE | — | — | ✅ |
| VTC | VTC 300 | SAVE | — | — | ✅ |
| VTC | VTC 300 | CD4 | — | — | ❌ |
| VTC | VTC 500 | SAVE | — | — | ✅ |
| VTC | VTC 700 | SAVE | — | — | ✅ |
| VTC | VTC 700 | CD4 | — | — | ❌ |
| VSC | VSC 100 | SAVE | — | — | ✅ |
| VSC | VSC 200 | SAVE | — | — | ✅ |
| VSC | VSC 300 | SAVE | — | — | ✅ |
| VR | VR 400 | CD4 | — | — | ❌ |
| VR | VR 700 | CD4 | ✅ | — | ❌ |
| VR | VR 700DK | CD4 | — | — | ❌ |
| VR | VR 400DE | CD4 | — | — | ❌ |

**Previously documented testing:** VSR 300, VTR 250/B, VTR 300 and VTR 500 (SAVE) over TCP/IP, plus VSR 500 (CD4) and VTR 150K (CD4) over TCP/IP. VTR 350/B has been reported working but not fully tested across all features. VTR 500 SAVE has been tested for reads and writes over RTU with both AUX-2 and ESP32-C6.

---

## 🏗️ Prerequisites -- unit selection and airflow

This integration assumes that the ventilation system is **properly
designed and correctly dimensioned**.

-   The air handling unit must be selected based on actual airflow
    requirements (m³/h)
-   Airflows per zone must be correctly balanced and commissioned
-   Home Assistant does **not** replace professional ventilation design

The integration builds on the unit's existing configuration and
provides: - monitoring - control - automation

Incorrect unit selection or airflow configuration cannot be compensated
for by software.

------------------------------------------------------------------------

## 🖥️ Example Lovelace card

The image below shows an example Lovelace card built manually in Home
Assistant using entities provided by this integration.

> The card itself is **not included** and can be freely customized to
> suit your setup.

![Ventilation Card](image/Ventilasjon%20kort.png)

------------------------------------------------------------------------

## 📦 Installation (HACS)

### Requirements

- Home Assistant **2024.6** or newer (requirement from the previous README; check against the current release)
- A Systemair SAVE or CD4 unit with compatible Modbus access
- HACS for the recommended installation method
- A compatible TCP/IP gateway or RTU serial connection

### Install the integration

1. Open **HACS → Integrations**.
2. Search for **Systemair Modbus** and select **Download**. If not available in the HACS search, add the repository as a **Custom repository** of type **Integration**.
3. Restart Home Assistant.
4. Navigate to **Settings → Devices & Services → Add integration → Systemair Modbus**.
5. Select **Modbus TCP/IP (network)** or **Modbus RTU (serial)**.
6. Follow the corresponding connection guide below.

### 🔌 Connection guides

| Connection | Guide | Example hardware |
|---|---|---|
| Modbus TCP/IP | **[TCP/IP – English](docs/modbus-tcp.md)** · [Norsk](docs/modbus-tcp.no.md) | Elfin EW11, Systemair SAVE Connect |
| Modbus RTU | **[RTU – English](docs/modbus-rtu.md)** · [Norsk](docs/modbus-rtu.no.md) | Home Assistant Connect AUX-2 with USB-to-RS485 adapter |

Both guides cover physical wiring, Home Assistant configuration and troubleshooting. **AUX-2 requires an external USB-to-RS485 adapter connected to its USB port** to connect to the ventilation unit's RS485 A/B terminals.

---

## 🔄 Upgrading from earlier versions

### Restore legacy SAVE entity IDs

Under **Settings → Devices & Services → Systemair Modbus → Configure (Options)**, you can find the option **“Restore legacy SAVE entity IDs (one-time operation, backup required)”**.

This one-time option is intended for users who need to restore previous SAVE entity IDs after changes to the integration. It is normally **not required** for installation or upgrades.

**Create a Home Assistant backup before using this option.** Do not enable it if your existing entities already work as expected.

When restoring earlier IDs, Recorder may report warnings if history already exists. History from temporary IDs may not be merged into the original history. This does not affect Modbus communication or control. Verify entities after upgrading.

---

## ℹ️ Limitations and technical notes

-   **Pressure Guard** is an internal safety function of the unit\
    → exposed as status only (read-only)
-   Not all SAVE models support full stop via Modbus\
    → where full stop is unavailable, the lowest possible fan speed is
    used
-   Available features depend on unit model and configuration

## 🙏 Acknowledgements

The Elfin EW11 (Modbus RTU → TCP) installation guide is based on work
published on [domotics.no](https://www.domotics.no/), written by **Mads
Nedrehagen**.

Special thanks to [**Ztaeyn**](https://github.com/Ztaeyn) for
contributing improvements to climate state handling (`hvac_action`)
based on the TRIAC register.

Special thanks to [**larstobi**](https://github.com/larstobi) for
contributions and testing of the CD4 support, including register
information and work on fan control that helped shape the further
development of the new CD4 implementation.

Special thanks to [**stboee**](https://github.com/stboee) for extensive
SAVE register research, feature proposals and testing related to heater
output, ECO, Free Cooling and Auto / Demand Control support.

Special thanks to [**gljo**](https://github.com/gljo) (Glen Tore Johansen)
for extensive and highly valuable testing on physical VSR 500/CD4 hardware.
His testing was a major contribution to the v1.3.0 CD4 implementation and
verified bidirectional temperature control, Manual summer / Off behaviour,
heater-dependent 12--22 °C and 15--19 °C temperature ranges, heat-recovery
status, electrical reheater status, fan control and general CD4 behaviour.

An AI assistant has been used to support troubleshooting, refactoring,
and documentation improvements during development.

This integration is **independently developed** as a modern Home
Assistant integration.

------------------------------------------------------------------------

## 📝 License

MIT -- see `LICENSE`
