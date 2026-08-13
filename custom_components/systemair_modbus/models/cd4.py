"""Systemair CD4 / D24810 legacy model.

The model exposes the documented CD4 fan controls, five-step supply-air
temperature control and selected operating diagnostics while keeping the
legacy register map conservative.

Addresses below are Modbus client register offsets (0-based), i.e. Systemair
documentation address minus 1.
"""

from __future__ import annotations

from typing import Any

from .save import RegisterDef


def r(modbus_offset: int) -> int:
    """Return an already converted 0-based Modbus register offset."""
    return modbus_offset


class Cd4Model:
    model_id = "legacy_cd4"
    model_name = "Systemair CD4 (legacy)"
    manufacturer = "Systemair"

    # --- Manual fan speed control (CD4) ---
    # CD4 uses the same register for status and command.
    ADDR_MANUAL_SPEED_COMMAND = r(100)

    MANUAL_SPEED_OPTIONS: dict[str, int] = {
        "stop": 0,
        "low": 1,
        "normal": 2,
        "high": 3,
    }
    MANUAL_SPEED_OPTIONS_INV: dict[int, str] = {
        v: k for k, v in MANUAL_SPEED_OPTIONS.items()
    }

    # Ordered manual speeds exposed through Home Assistant's fan percentage API.
    # "Stop" is deliberately excluded: percentage 0 is handled as off.
    MANUAL_SPEED_ORDER: tuple[str, ...] = ("low", "normal", "high")
    MANUAL_SPEED_STOP_OPTION = "stop"

    # --- Supply-air temperature control (CD4) ---
    # Systemair CD panel documentation describes five discrete supply-air
    # temperature steps. Level 0 is manual summer mode.
    #
    # Register list:
    #   REG_HC_TEMP_LVL   PDF 207 -> Modbus offset 206, R/W command
    #   REG_HC_TEMP_SP    PDF 208 -> Modbus offset 207, read active level
    #   REG_HC_TEMP_LVL1..5 PDF 209..213 -> offsets 208..212, 0.1 °C
    ADDR_TEMPERATURE_LEVEL_COMMAND = r(206)

    # Raw registers enabled by default in Home Assistant.
    # Existing keys are intentionally preserved.
    DEFAULT_ENABLED_RAW_KEYS = {
        # Existing fan/control values
        "saf_speed_rpm",
        "eaf_speed_rpm",

        # Phase 1 fan diagnostics

        # Phase 1 temperature inputs.
        # Mapping is documented by Systemair:
        # TEMP_IN1=SS (supply), TEMP_IN2=ETS (extract),
        # TEMP_IN3=EHS (exhaust), TEMP_IN4=OT/FPS, TEMP_IN5=outdoor.
        "temperature_sensor_1",
        "temperature_sensor_2",
        "temperature_sensor_3",
        "temperature_sensor_4",
        "temperature_sensor_5",

        # Phase 1 operating diagnostics.
        # rotor_state and temperature_sensor_state are still read, but kept
        # disabled by default until their bit/state mappings are verified.
        # The relay/capability values are exposed as binary_sensor entities.
        "defrost_state",

        # Existing system/filter values
        "filter_replacement_period",
        "filter_days",
    }

    def __init__(self, *, qv_max: int | None = None) -> None:
        self._qv_max = qv_max

    REGISTERS: list[RegisterDef] = [
        # ---------------------------------------------------------------------
        # Fan
        # Systemair docs 101..114 -> Modbus offsets 100..113
        # ---------------------------------------------------------------------
        RegisterDef(
            key="manual_mode_command_register",
            address=r(100),
            input_type="holding",
            data_type="uint16",
        ),
        RegisterDef(
            key="saf_speed_low_rpm",
            address=r(101),
            input_type="holding",
            data_type="uint16",
            unit="rpm",
        ),
        RegisterDef(
            key="eaf_speed_low_rpm",
            address=r(102),
            input_type="holding",
            data_type="uint16",
            unit="rpm",
        ),
        RegisterDef(
            key="saf_speed_normal",
            address=r(103),
            input_type="holding",
            data_type="uint16",
            unit="rpm",
        ),
        RegisterDef(
            key="eaf_speed_normal",
            address=r(104),
            input_type="holding",
            data_type="uint16",
            unit="rpm",
        ),
        RegisterDef(
            key="saf_speed_high",
            address=r(105),
            input_type="holding",
            data_type="uint16",
            unit="rpm",
        ),
        RegisterDef(
            key="eaf_speed_high",
            address=r(106),
            input_type="holding",
            data_type="uint16",
            unit="rpm",
        ),

        # New in CD4 phase 1
        # REG_FAN_SF_PWM / docs 109
        RegisterDef(
            key="saf_pwm",
            address=r(108),
            input_type="holding",
            data_type="uint16",
            unit="%",
            state_class="measurement",
        ),
        # REG_FAN_EF_PWM / docs 110
        RegisterDef(
            key="eaf_pwm",
            address=r(109),
            input_type="holding",
            data_type="uint16",
            unit="%",
            state_class="measurement",
        ),

        RegisterDef(
            key="saf_speed_rpm",
            address=r(110),
            input_type="holding",
            data_type="uint16",
            unit="rpm",
            state_class="measurement",
        ),
        RegisterDef(
            key="eaf_speed_rpm",
            address=r(111),
            input_type="holding",
            data_type="uint16",
            unit="rpm",
            state_class="measurement",
        ),

        # REG_FAN_SPEED_LVL_CD / docs 113
        RegisterDef(
            key="fan_speed_level_cd",
            address=r(112),
            input_type="holding",
            data_type="uint16",
        ),
        RegisterDef(
            key="fan_manual_stop_allowed_register",
            address=r(113),
            input_type="holding",
            data_type="uint16",
        ),

        # ---------------------------------------------------------------------
        # Supply-air temperature setting
        # Systemair docs 207..213 -> Modbus offsets 206..212
        # ---------------------------------------------------------------------
        RegisterDef(
            key="temperature_level_command_register",
            address=r(206),
            input_type="holding",
            data_type="uint16",
        ),
        RegisterDef(
            key="temperature_setpoint_level",
            address=r(207),
            input_type="holding",
            data_type="uint16",
        ),
        RegisterDef(
            key="temperature_level_1",
            address=r(208),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),
        RegisterDef(
            key="temperature_level_2",
            address=r(209),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),
        RegisterDef(
            key="temperature_level_3",
            address=r(210),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),
        RegisterDef(
            key="temperature_level_4",
            address=r(211),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),
        RegisterDef(
            key="temperature_level_5",
            address=r(212),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),

        # ---------------------------------------------------------------------
        # Heating/cooling temperature inputs
        # Systemair docs 214..219 -> Modbus offsets 213..218
        #
        # Systemair documents the physical mapping as:
        # TEMP_IN1=SS (supply), TEMP_IN2=ETS (extract),
        # TEMP_IN3=EHS (exhaust), TEMP_IN4=OT/FPS,
        # TEMP_IN5=OS (outdoor air).
        # ---------------------------------------------------------------------
        RegisterDef(
            key="temperature_sensor_1",
            address=r(213),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),
        RegisterDef(
            key="temperature_sensor_2",
            address=r(214),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),
        RegisterDef(
            key="temperature_sensor_3",
            address=r(215),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),
        RegisterDef(
            key="temperature_sensor_4",
            address=r(216),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),
        RegisterDef(
            key="temperature_sensor_5",
            address=r(217),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),
        # REG_HC_TEMP_STATE / docs 219
        # Bitfield for TEMP_IN1..5 sensor-fault states. Kept raw in phase 1.
        RegisterDef(
            key="temperature_sensor_state",
            address=r(218),
            input_type="holding",
            data_type="uint16",
        ),

        # ---------------------------------------------------------------------
        # Rotor / heat recovery
        # Systemair docs 351..352 -> Modbus offsets 350..351
        # ---------------------------------------------------------------------
        RegisterDef(
            key="rotor_state",
            address=r(350),
            input_type="holding",
            data_type="uint16",
        ),
        RegisterDef(
            key="rotor_relay_active",
            address=r(351),
            input_type="holding",
            data_type="uint16",
        ),

        # ---------------------------------------------------------------------
        # System info
        # ---------------------------------------------------------------------
        RegisterDef(
            key="system_type",
            address=r(500),
            input_type="holding",
            data_type="uint16",
        ),

        # ---------------------------------------------------------------------
        # Filter
        # ---------------------------------------------------------------------
        RegisterDef(
            key="filter_replacement_period",
            address=r(600),
            input_type="holding",
            data_type="uint16",
        ),
        RegisterDef(
            key="filter_days",
            address=r(601),
            input_type="holding",
            data_type="uint16",
        ),

        # ---------------------------------------------------------------------
        # Defrost diagnostics
        # Systemair docs 651 -> Modbus offset 650
        # 0 = no defrost
        # 1 = reduced flow defrost
        # 2 = bypass defrost
        # 3 = stop defrost
        # ---------------------------------------------------------------------
        RegisterDef(
            key="defrost_state",
            address=r(650),
            input_type="holding",
            data_type="uint16",
        ),

        # ---------------------------------------------------------------------
        # Power-board relay status
        # Systemair docs 751 -> Modbus offset 750
        #
        # Packed relay states corresponding to:
        #   Coil 12001 -> bit 0: preheater relay
        #   Coil 12002 -> bit 1: reheater relay
        #   Coil 12003 -> bit 2: common heater/preheater relay
        # ---------------------------------------------------------------------
        RegisterDef(
            key="pcu_pb_relays",
            address=r(750),
            input_type="holding",
            data_type="uint16",
        ),

        # ---------------------------------------------------------------------
        # Alarm diagnostics
        # Systemair docs 802 -> Modbus offset 801
        # Alarm relay state. Detailed alarm bitfield (offset 800) is deliberately
        # left for phase 2, where it can be decoded into binary sensors.
        # ---------------------------------------------------------------------
        RegisterDef(
            key="alarm_relay_active",
            address=r(801),
            input_type="holding",
            data_type="uint16",
        ),
    ]

    def compute_derived(self, data: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}

        lvl_raw = data.get("manual_mode_command_register")
        try:
            lvl = int(float(lvl_raw))
        except (TypeError, ValueError):
            lvl = None

        out["mode_status_text"] = {
            0: "manual_stop",
            1: "manual_low",
            2: "manual_normal",
            3: "manual_high",
        }.get(lvl, "unknown")

        out["mode_status_register"] = lvl

        # SAVE-oriented derived values: kept for compatibility for now.
        # CD4 sensor.py currently does not expose derived SAVE sensors.
        out["active_season"] = "unknown"
        out["iaq_level_text"] = "unknown"
        out["regulation_mode_text"] = "unknown"
        out["exhaust_air_flow_rate"] = None
        out["supply_air_flow_rate"] = None

        # next_filter_change: rough estimate from months/days
        months_raw = data.get("filter_replacement_period")
        days_raw = data.get("filter_days")

        try:
            months = int(float(months_raw)) if months_raw is not None else None
            days = int(float(days_raw)) if days_raw is not None else None
        except (TypeError, ValueError):
            months = None
            days = None

        if months is None or days is None:
            out["next_filter_change"] = "Ukjent"
        else:
            remaining = max((months * 30) - days, 0)
            out["next_filter_change"] = (
                f"{int(remaining / 30)} mnd"
                if remaining >= 31
                else f"{remaining} dager"
            )

        return out
