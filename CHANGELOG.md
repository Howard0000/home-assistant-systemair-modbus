# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] – 2026-02-13
### 🚀 First stable HACS release

### Added
- First stable release of **Systemair Modbus** available via HACS
- UI-based setup via Home Assistant Config Flow
- Support for Systemair SAVE ventilation units using Modbus TCP
- Sensors for temperatures, operational status, and calculated values
- Binary sensors for alarms and unit states
- Number entities for setpoints and adjustable parameters
- Select entities for operation modes (Auto, Manual, Boost, Away, etc.)
- Full support for the Home Assistant device and entity model
- English and Norwegian translations (`en`, `nb`)
- Local polling (`iot_class: local_polling`)

### Notes
- This is an unofficial community integration and is not affiliated with Systemair


### Community attribution up for approval:
- Added "hvac_action", (Heating / Fan / Off) based on TRIAC register (heating element)
    