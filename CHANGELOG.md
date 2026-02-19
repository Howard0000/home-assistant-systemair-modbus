# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.1] – 2026-02-19
### 🐛 Bugfix release

### Fixed
- Fixed 500 error in Options / settings dialog (Config Flow options now open correctly)
- Removed duplicate entries in the Modbus register list
- Minor internal cleanup related to options handling

### Notes
- This is a maintenance release with no functional changes to entities or services
- Recommended update for all users (restores ability to change scan interval from UI)
  
---

## [1.1.0] – 2026-02-18
### 🧹 Register cleanup and fixes (SAVE)

### Changed
- Cleaned up and corrected the SAVE register map
- Fixed several incorrect or inconsistent register definitions (address/type/scale)
- Improved internal consistency in register handling

### Added
- Added `hvac_action` (Heating / Fan / Off) based on TRIAC register (heating element) — community contribution

### Fixed
- Climate heating state handling (removed invalid heating MODE)
- UI/HA semantics for climate state now reflect actual device state

### Notes
- No CD4 legacy support in this release (still under testing)
- This release focuses on correctness and stability of the SAVE register map

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

