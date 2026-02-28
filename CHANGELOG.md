# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.2.0] – 2026-02-28

### Added
- Writable **Supply air setpoint** (TC_SP / HR 2001 → 0-based 2000).  
  The setpoint can now be adjusted directly from Home Assistant via both the Climate entity and a Number entity.

- Proper **Filter replaced** functionality.  
  The integration now resets the filter timer by writing the current timestamp to HR 7002/7003 (Systemair addressing), instead of only clearing alarms.

- Writable **Filter replacement period** (HR 7001 → 0-based 7000) exposed as a Number entity.

- Calculated **Exhaust air temperature** sensor.  
  Since no native Modbus register for true exhaust temperature is documented, this value is derived from extract temperature, outdoor temperature and heat recovery efficiency.

### Changed
- Auto mode is now represented as a single demand-controlled mode instead of exposing Auto Low / Auto Normal / Auto High variants in Home Assistant.

- Improved filter timer handling and presentation logic.

- Time-based Number entities now use Home Assistant standard time units where applicable.

- Removed remaining hardcoded Norwegian UI strings from backend code. All user-facing labels are now handled via translation files.

### Notes
- The exhaust air temperature sensor is calculated and not read from a native Modbus register.
- No breaking changes to existing entity IDs.
- Fully backwards compatible with existing configurations.
## [1.1.3] – 2026-02-25

### Added
- Exposed "Relative moisture extraction" as a standard sensor (enabled by default) for easier tuning of RH control.
- Exposed "Supply air temperature setpoint" as a standard sensor (enabled by default) to show what the unit is targeting.

### Changed
- These two values are no longer hidden as diagnostic-only entities.
- Replaced Modbus communication layer with a more robust implementation.
- Added internal request queue, pacing and retry/backoff logic for improved stability on sensitive gateways (e.g. SAVE Connect).
- Improved handling of Modbus read/write collisions between polling and user actions.
- Added fallback logic for input registers (FC04 → FC03) where gateways do not support FC04 correctly.
- Config Flow now performs a fast TCP preflight check before Modbus validation to better distinguish network issues from Modbus handshake problems.
- Modbus connection validation now uses the selected Gateway profile (Generic vs SAVE Connect) to match runtime behavior.
- Connection initialization delay is now profile-based:
  - Generic gateway profile no longer applies the 10s post-connect delay.
  - SAVE Connect profile keeps the conservative delay for safe-mode stability.
- Improved robustness of Modbus client shutdown to ensure sockets are properly closed across different pymodbus variants.

### Notes
- No functional changes to existing entities or services beyond the new sensors listed above.
- For the Generic gateway profile, runtime polling behavior should remain identical; changes mainly improve setup reliability and edge-case stability.
- SAVE Connect safe mode remains conservative and unchanged in behavior, aside from internal robustness improvements.

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
