"""Systemair CD4 / D24810 legacy model (minimal register map + derived values).

This model is intentionally small to avoid invalid register reads on older panels.

Addresses are Modbus client register offsets (0-based).
"""

from __future__ import annotations

from typing import Any

from .save import RegisterDef


def r(pdf_addr: int) -> int:
    """Convert PDF 1-based register address to Modbus 0-based client offset."""
    return pdf_addr


class Cd4Model:
    model_id = "legacy_cd4"
    model_name = "Systemair CD4 (legacy)"
    manufacturer = "Systemair"

    # --- Minimal select-støtte (CD4) ---
    # CD4 bruker samme register for status/kommando for manuell hastighet
    ADDR_MANUAL_SPEED_COMMAND = r(100)

    MANUAL_SPEED_OPTIONS: dict[str, int] = {
        "Stop": 0,
        "Low": 1,
        "Normal": 2,
        "High": 3,
    }
    MANUAL_SPEED_OPTIONS_INV: dict[int, str] = {v: k for k, v in MANUAL_SPEED_OPTIONS.items()}

    # What raw registers should be ENABLED by default (shown under Sensorer)
    DEFAULT_ENABLED_RAW_KEYS = {
        "manual_mode_command_register",
        "saf_speed_rpm",
        "eaf_speed_rpm",
        "saf_speed_low_rpm",
        "eaf_speed_low_rpm",
        "saf_speed_normal",
        "eaf_speed_normal",
        "saf_speed_high",
        "eaf_speed_high",
        "flow_units",
        "saf_pwm",
        "eaf_pwm",
        "fan_speed_level_cd",
        "filter_replacement_period",
        "filter_days",
        "system_type",
        "fan_manual_stop_allowed_register",
        "heater_type",
        "frost_protection_level_setpoint",
        "temperature_setpoint",
        "temperature_regulation_setpoint",
        "supply_temperature",
        "extract_temperature",
        "exhaust_air_preheater_temperature",
        "overheating_frost_protection_temperature",
        "outdoor_temperature",
        "temperature_sensor_state",
        "alarms_all_detailed",
    }

    def __init__(self, *, qv_max: int | None = None) -> None:
        self._qv_max = qv_max

    REGISTERS: list[RegisterDef] = [
        # --- Fan ---
        RegisterDef(key="manual_mode_command_register", address=r(100), input_type="holding", data_type="uint16"),
        RegisterDef(key="saf_speed_low_rpm", address=r(101), input_type="holding", data_type="uint16", unit="rpm"),
        RegisterDef(key="eaf_speed_low_rpm", address=r(102), input_type="holding", data_type="uint16", unit="rpm"),
        RegisterDef(key="saf_speed_normal", address=r(103), input_type="holding", data_type="uint16", unit="rpm"),
        RegisterDef(key="eaf_speed_normal", address=r(104), input_type="holding", data_type="uint16", unit="rpm"),
        RegisterDef(key="saf_speed_high", address=r(105), input_type="holding", data_type="uint16", unit="rpm"),
        RegisterDef(key="eaf_speed_high", address=r(106), input_type="holding", data_type="uint16", unit="rpm"),
        RegisterDef(key="flow_units", address=r(107), input_type="holding", data_type="uint16"),
        RegisterDef(key="saf_pwm", address=r(108), input_type="holding", data_type="uint16", unit="%", state_class="measurement"),
        RegisterDef(key="eaf_pwm", address=r(109), input_type="holding", data_type="uint16", unit="%", state_class="measurement"),
        RegisterDef(key="saf_speed_rpm", address=r(110), input_type="holding", data_type="uint16", unit="rpm", state_class="measurement"),
        RegisterDef(key="eaf_speed_rpm", address=r(111), input_type="holding", data_type="uint16", unit="rpm", state_class="measurement"),
        RegisterDef(key="fan_speed_level_cd", address=r(112), input_type="holding", data_type="uint16"),
        RegisterDef(key="fan_manual_stop_allowed_register", address=r(113), input_type="holding", data_type="uint16"),

        # --- Heating and temperature settings ---
        RegisterDef(key="heater_type", address=r(200), input_type="holding", data_type="uint16"),
        RegisterDef(key="frost_protection_level_setpoint", address=r(205), input_type="holding", data_type="uint16"),
        RegisterDef(key="temperature_setpoint", address=r(207), input_type="holding", data_type="uint16"),
        RegisterDef(
            key="temperature_regulation_setpoint",
            address=r(221),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),

        # --- Temperatures ---
        RegisterDef(
            key="supply_temperature",
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
            key="extract_temperature",
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
            key="exhaust_air_preheater_temperature",
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
            key="overheating_frost_protection_temperature",
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
            key="outdoor_temperature",
            address=r(217),
            input_type="holding",
            data_type="int16",
            scale=0.1,
            precision=1,
            unit="°C",
            device_class="temperature",
            state_class="measurement",
        ),
        RegisterDef(key="temperature_sensor_state", address=r(218), input_type="holding", data_type="uint16"),

        # --- System info ---
        RegisterDef(key="system_type", address=r(500), input_type="holding", data_type="uint16"),

        # --- Filter ---
        RegisterDef(key="filter_replacement_period", address=r(600), input_type="holding", data_type="uint16", unit="months"),
        RegisterDef(key="filter_days", address=r(601), input_type="holding", data_type="uint16", unit="days"),

        # --- Alarms ---
        RegisterDef(key="alarms_all_detailed", address=r(802), input_type="holding", data_type="uint16"),
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

        # SAVE-oriented derived values: keep placeholders for now
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
            out["next_filter_change"] = f"{int(remaining/30)} mnd" if remaining >= 31 else f"{remaining} dager"

        return out
