# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[Unreleased]
Added
- Exposed "Relative moisture extraction" as a standard sensor (enabled by default) for easier tuning of RH control.
- Exposed "Supply air temperature setpoint" as a standard sensor (enabled by default) to show what the unit is targeting.

Changed
- These two values are no longer hidden as diagnostic-only entities.

- Replaced Modbus communication layer with a more robust implementation.
- Added internal request queue, pacing and retry/backoff logic for improved stability on sensitive gateways (e.g. SAVE Connect).
- Improved handling of Modbus read/write collisions between polling and user actions.
- Added fallback logic for input registers (FC04 → FC03) where gateways do not support FC04 correctly.
- No user-facing changes yet (behavior should remain identical for Generic gateway profile).

---

## [1.1.2] – 2026-02-22
### Added
- Added selectable **Gateway profile** option to tune Modbus read strategy:
  - **SAVE Connect (safe mode)**: small batches (uint32-safe), no hole bridging, forces FC03 for logical input registers
  - **Generic gateway** (EW11 etc.): normal/aggressive batching for faster polling
- Gateway profile can be changed from the integration **Options** without reinstalling.

### Changed
- Modbus client now supports profile-based read strategies (defensive vs. aggressive batching).

### Fixed
- Fixed decoding of 32-bit registers (uint32) using correct Systemair L/H word order:
  - Reads 2 registers for uint32 values
  - Decoder now uses `(high << 16) | low`
  - Fixes incorrect values such as `countdown_mode_time` (registers 1110/1111), which are now decoded directly as seconds without any division workaround.


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
