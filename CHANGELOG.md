# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0-beta.3] – 2026-09-05

### Added

* Added SAVE heater / Y1 output support:
  * Heater analog output percentage
  * Heater active status
* Added SAVE ECO controls and diagnostics:
  * ECO mode enabled
  * ECO mode active
  * ECO function active
  * ECO heat offset
* Expanded SAVE Free Cooling support and diagnostics:
  * Clear distinction between enabled and active states
  * Free Cooling state
  * Reliable temperature status
  * Heater block counter
* Added SAVE Auto / Demand Control diagnostics:
  * Auto mode source
  * Demand control enabled
  * Active demand controller
  * Supply and extract fan demand values
* Expanded CD4 Climate control:
  * Supply-air temperature control from 12–22 °C in 1 °C steps
  * Climate Off / Manual summer support
  * Return from Off to the previous temperature
* Expanded CD4 diagnostic register coverage

### Changed

* Changed the default Modbus polling interval from 10 to 30 seconds to
  reduce Modbus traffic and potentially improve physical touch-display stability
* Improved SAVE entity naming and presentation for ECO, Free Cooling,
  heater output and Demand Control diagnostics
* CD4 Climate temperature handling now follows the complete documented
  OFF / 12–22 °C mapping instead of the previous five-step presentation
* Updated English and Norwegian documentation for the expanded SAVE and CD4 support

### Fixed

* Fixed duplicate / ambiguous Free Cooling entity naming by clearly
  separating enabled and active states
* Improved CD4 Climate handling around temperature Off / Manual summer
* Improved presentation and decoding of several SAVE diagnostic states

### Notes

* CD4 support remains experimental while testing continues on physical legacy units
* The complete CD4 OFF / 12–22 °C register mapping has been verified on
  physical VSR 500/CD4 hardware
* Additional testing of Home Assistant Climate writes to physical CD4
  controllers is especially welcome
* The polling interval remains configurable in the integration options;
  30 seconds is the new default

### Testing wanted

Feedback is especially welcome for:

* SAVE heater / Y1 output
* SAVE ECO enabled / active behaviour
* SAVE Free Cooling states and diagnostics
* SAVE Auto / Demand Control diagnostics
* CD4 Climate control at 12 °C, 17 °C, 20 °C and 22 °C
* CD4 Climate Off / Manual summer and return from Off
* CD4 Fan control
* Long-term Modbus and physical touch-display stability

### Contributors

Special thanks to:

* **@stboee** for extensive SAVE register research, feature proposals and
  testing across #76, #77, #78 and #79
* **@gljo** for hardware testing and verification of the complete CD4
  OFF / 12–22 °C temperature mapping
* **@Ztaeyn** for reporting and helping investigate the physical
  touch-display stability issue in #87
* **@larstobi** for the original CD4 implementation and contributions
  that the expanded CD4 support continues to build on

---

## [1.3.0-beta.2] – 2026-08-13

### Added

* Major expansion of Systemair CD4 / legacy support
* Native Home Assistant Fan entity for CD4 ventilation control
  * Off / Low / Medium / High
  * Stop/Off is only available when supported by the unit
* Native Home Assistant Climate entity for CD4
  * Five-step supply air temperature control
  * Current supply air temperature
  * Heating state indication
  * Fan mode control directly from the Climate entity
* Improved CD4 temperature sensor mapping:
  * Supply air temperature
  * Extract air temperature
  * Exhaust air temperature
  * Outdoor temperature
  * Overheat/frost protection temperature
* Additional CD4 operating status:
  * Alarm relay
  * Defrost status
  * Rotor status
  * Heater status

### Changed

* Reworked CD4 entity organization for a cleaner Home Assistant device page
* Moved technical/raw CD4 values to Diagnostics where appropriate
* Improved Norwegian and English translations for CD4 entities
* Manual fan speed handling now follows Home Assistant conventions
* CD4 fan speed uses Low / Medium / High in the Home Assistant Fan and Climate interfaces
* Improved handling of units where manual fan stop is not allowed
* Climate heating state now reflects actual heater activity instead of only comparing current and target temperature

### Fixed

* Fixed CD4 translation state keys to comply with Home Assistant translation requirements
* Improved CD4 status decoding and presentation
* Removed obsolete and duplicate CD4 entity handling

### Notes

* CD4 support remains in beta while testing continues on real Systemair legacy units
* SAVE functionality is unchanged in this beta
* No additional SAVE register changes are included in this release

### Testing wanted

Feedback from users with real CD4-based units is especially welcome:

* Fan control: Off / Low / Medium / High
* Supply air temperature adjustment across all five available steps
* Climate current and target temperatures
* Heating state indication
* Temperature sensor mapping
* Alarm, rotor, defrost and heater states
* General stability and Modbus communication

## [1.3.0-beta.1] – 2026-04-27

### Added

* Experimental support for Systemair CD4 / legacy units

### Changed

* Unified SAVE and CD4 into a single integration
* Model-based platform loading (CD4 uses a limited feature set)
* Clarified EW11 setup in README: packet counters may remain at 0 until a Modbus client begins polling the unit (suggested in #66)

### Fixed

* Fixed Norwegian translation inconsistency for Boost mode (button vs duration entities)

### Notes

* CD4 support is experimental and under active development
* SAVE functionality is unchanged from previous versions

### Testing wanted

* Verify that existing SAVE setups behave as in v1.2.0
* Test CD4 on real hardware:

  * Fan speed level (Stop / Low / Normal / High)
  * SF / EF RPM values
  * General stability and missing sensors


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
