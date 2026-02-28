"""Systemair SAVE model (register map + derived values).

All addresses in this file are Modbus client offsets (PDF address - 1)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RegisterDef:
    key: str
    address: int
    input_type: str = "holding"  # "holding" | "input"
    data_type: str = "int16"     # "int16" | "uint16" | "uint32"
    scale: float = 1.0
    offset: float = 0.0
    precision: int | None = None
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None


class SaveModel:
    model_id = "save"
    model_name = "Systemair SAVE"
    manufacturer = "Systemair"

    def __init__(self, *, qv_max: int | None = None) -> None:
        """Create a model instance.

        qv_max is the nominal maximum air flow (m³/h) for the selected unit model.
        If not provided, we fall back to the legacy factor (fan % * 3).
        """
        self._qv_max = qv_max

    @property
    def flow_factor(self) -> float:
        """m³/h per % (estimated)."""
        return (self._qv_max / 100.0) if self._qv_max else 3.0

    ADDR_MODE_STATUS = 1160
    ADDR_MODE_COMMAND = 1161
    ADDR_MANUAL_SPEED_COMMAND = 1130

    ADDR_ECO_MODE = 2504
    ADDR_HOLIDAY_DURATION_DAYS = 1100
    ADDR_AWAY_DURATION_HOURS = 1101
    ADDR_REFRESH_DURATION_MINUTES = 1103
    ADDR_CROWDED_DURATION_HOURS = 1104

    ADDR_ECO_HEAT_OFFSET_0_1C = 2503
    ADDR_SUPPLY_AIR_SETPOINT_0_1C = 2000

    ADDR_FREE_COOLING_ENABLE = 4100
    ADDR_FREE_COOLING_DAY_MIN_0_1C = 4101
    ADDR_FREE_COOLING_NIGHT_HIGH_0_1C = 4102
    ADDR_FREE_COOLING_NIGHT_LOW_0_1C = 4103
    ADDR_FREE_COOLING_ROOM_CANCEL_0_1C = 4104
    ADDR_FREE_COOLING_START_H = 4105
    ADDR_FREE_COOLING_START_M = 4106
    ADDR_FREE_COOLING_END_H = 4107
    ADDR_FREE_COOLING_END_M = 4108
    ADDR_FREE_COOLING_MIN_SAF = 4111
    ADDR_FREE_COOLING_MIN_EAF = 4112
    ADDR_FILTER_REPLACEMENT_PERIOD = 7000

    # NOTE: Keep all user-facing labels in English in code.
    # The HA frontend can translate *states* (for derived sensors) via translations,
    # but things like climate preset labels are not auto-translated.
    COMMAND_MODE_OPTIONS: dict[str, int] = {
        "Auto": 1,
        "Manual": 2,
        "Party": 3,
        "Boost": 4,
        "Fireplace": 5,
        "Away": 6,
        "Holiday": 7,
    }

    STATUS_MODE_TO_LABEL: dict[int, str] = {
        0: "Auto",
        1: "Manual",
        2: "Party",
        3: "Boost",
        4: "Fireplace",
        5: "Away",
        6: "Holiday",
        7: "Cooker Hood",
        8: "Vacuum cleaner",
        9: "CDI1",
        10: "CDI2",
        11: "CDI3",
        12: "Pressure guard",
    }

    # Language-neutral keys for derived sensors (translated in UI)
    STATUS_MODE_TO_KEY: dict[int, str] = {
        0: "auto",
        1: "manual",
        2: "party",
        3: "boost",
        4: "fireplace",
        5: "away",
        6: "holiday",
        7: "cooker_hood",
        8: "vacuum_cleaner",
        9: "cdi1",
        10: "cdi2",
        11: "cdi3",
        12: "pressure_guard",
    }

    MANUAL_SPEED_OPTIONS: dict[str, int] = {
        "Stop": 0,
        "Low": 2,
        "Normal": 3,
        "High": 4,
    }
    MANUAL_SPEED_OPTIONS_INV: dict[int, str] = {v: k for k, v in MANUAL_SPEED_OPTIONS.items()}

    # Free cooling minimum fan speed uses the same discrete speed steps as manual speed.
    FREE_COOLING_MIN_SPEED_OPTIONS: dict[str, int] = MANUAL_SPEED_OPTIONS
    FREE_COOLING_MIN_SPEED_OPTIONS_INV: dict[int, str] = {v: k for k, v in FREE_COOLING_MIN_SPEED_OPTIONS.items()}

    # Backwards-compatible aliases (older code used these names).
    MODE_COMMAND_OPTIONS = COMMAND_MODE_OPTIONS
    MODE_STATUS_TO_LABEL = STATUS_MODE_TO_LABEL

    REGISTERS: list[RegisterDef] = [
        # --- Modes and time settings ---
        RegisterDef(key='summer_winter_operation_1_0', address=1038, input_type='input', data_type='uint16'),
        RegisterDef(key='holiday_mode_duration', address=1100, input_type='holding', data_type='uint16', unit='days'),
        RegisterDef(key='away_mode_duration', address=1101, input_type='holding', data_type='uint16', unit='h'),
        RegisterDef(key='fireplace_mode_duration', address=1102, input_type='holding', data_type='uint16', unit='min'),
        RegisterDef(key='refresh_mode_duration', address=1103, input_type='holding', data_type='uint16', unit='min'),
        RegisterDef(key='crowded_mode_duration', address=1104, input_type='holding', data_type='uint16', unit='h'),
        RegisterDef(key='countdown_mode_time', address=1110, input_type='input', data_type='uint32', unit='s'),

        # --- System status ---
        RegisterDef(key='iaq_level', address=1122, input_type='input', data_type='uint16'),
        RegisterDef(key='manual_mode_command_register', address=1130, input_type='holding', data_type='uint16'),
        RegisterDef(key='mode_status_register', address=1160, input_type='input', data_type='uint16'),
        RegisterDef(key='mode_command_register', address=1161, input_type='holding', data_type='uint16'),

        # --- CDI speeds (IR = input) ---
        RegisterDef(key='saf_speed_holiday', address=1220, input_type='input', data_type='uint16', unit='rpm'),
        RegisterDef(key='eaf_speed_holiday', address=1221, input_type='input', data_type='uint16', unit='rpm'),
        RegisterDef(key='saf_speed_cooker_hood', address=1222, input_type='input', data_type='uint16', unit='rpm'),
        RegisterDef(key='eaf_speed_cooker_hood', address=1223, input_type='input', data_type='uint16', unit='rpm'),
        RegisterDef(key='saf_speed_vacuumcleaner', address=1224, input_type='input', data_type='uint16', unit='rpm'),
        RegisterDef(key='eaf_speed_vacuumcleaner', address=1225, input_type='input', data_type='uint16', unit='rpm'),

        # --- Outdoor compensation ---
        RegisterDef(key='fan_speed_comp_winter', address=1251, input_type='holding', data_type='uint16', unit='%'),
        RegisterDef(key='fan_speed_comp_checked', address=1252, input_type='holding', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='fan_speed_comp_winter_max_temp', address=1253, input_type='holding', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='fan_speed_comp_read', address=1254, input_type='input', data_type='uint16', unit='%'),
        RegisterDef(key='fan_speed_comp_winter_start_temp', address=1255, input_type='holding', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='fan_speed_comp_summer_start_temp', address=1256, input_type='holding', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='fan_speed_comp_max_temp', address=1257, input_type='holding', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='fan_speed_comp_summer', address=1258, input_type='holding', data_type='uint16', unit='%'),

        # --- Fan level status ---
        RegisterDef(key='saf_speed_low', address=1302, input_type='input', data_type='uint16', unit='rpm'),
        RegisterDef(key='eaf_speed_low', address=1303, input_type='input', data_type='uint16', unit='rpm'),

        # --- System status / permissions ---
        RegisterDef(key='fan_manual_stop_allowed_register', address=1352, input_type='holding', data_type='uint16'),

        # --- Fan limits (RPM) ---
        RegisterDef(key='saf_speed_minimum_rpm', address=1410, input_type='holding', data_type='uint16', unit='rpm'),
        RegisterDef(key='eaf_speed_minimum_rpm', address=1411, input_type='holding', data_type='uint16', unit='rpm'),
        RegisterDef(key='saf_speed_low_rpm', address=1412, input_type='holding', data_type='uint16', unit='rpm'),
        RegisterDef(key='eaf_speed_low_rpm', address=1413, input_type='holding', data_type='uint16', unit='rpm'),
        RegisterDef(key='saf_speed_normal', address=1414, input_type='holding', data_type='uint16', unit='rpm'),
        RegisterDef(key='eaf_speed_normal', address=1415, input_type='holding', data_type='uint16', unit='rpm'),
        RegisterDef(key='saf_speed_high', address=1416, input_type='holding', data_type='uint16', unit='rpm'),
        RegisterDef(key='eaf_speed_high', address=1417, input_type='holding', data_type='uint16', unit='rpm'),
        RegisterDef(key='saf_speed_maximum', address=1418, input_type='holding', data_type='uint16', unit='rpm'),
        RegisterDef(key='eaf_speed_maximum', address=1419, input_type='holding', data_type='uint16', unit='rpm'),

        # --- Temperature settings ---
        RegisterDef(key='supply_air_setpoint', address=2000, input_type='holding', data_type='uint16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='exhaust_air_sp', address=2012, input_type='holding', data_type='uint16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='exhaust_air_min_sp', address=2020, input_type='holding', data_type='uint16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='exhaust_air_max_sp', address=2021, input_type='holding', data_type='uint16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='supply_air_room_exhaust_reg', address=2030, input_type='holding', data_type='uint16'),

        # --- Heating and humidity ---
        RegisterDef(key='triac_after_manual_override', address=2148, input_type='input', data_type='uint16', unit='%'),
        RegisterDef(key='moisture_extraction_sp', address=2202, input_type='holding', data_type='uint16', unit='%', device_class='humidity'),
        RegisterDef(key='calculated_moisture_extraction', address=2210, input_type='holding', data_type='uint16', unit='%', device_class='humidity'),
        RegisterDef(key='calculated_moisture_intake', address=2211, input_type='holding', data_type='uint16', unit='%', device_class='humidity'),

        # --- Eco ---
        RegisterDef(key='eco_heat_offset', address=2503, input_type='holding', data_type='uint16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='eco_mode', address=2504, input_type='holding', data_type='uint16'),
        RegisterDef(key='eco_function_active', address=2505, input_type='input', data_type='uint16'),

        # --- Free Cooling ---
        RegisterDef(key='free_cooling_enable', address=4100, input_type='holding', data_type='uint16'),
        RegisterDef(key='free_cooling_daytime_min_temp', address=4101, input_type='holding', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='free_cooling_night_high_limit', address=4102, input_type='holding', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='free_cooling_night_low_limit', address=4103, input_type='holding', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='free_cooling_room_cancel_temp', address=4104, input_type='holding', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='free_cooling_start_time_h', address=4105, input_type='holding', data_type='uint16'),
        RegisterDef(key='free_cooling_start_time_m', address=4106, input_type='holding', data_type='uint16'),
        RegisterDef(key='free_cooling_end_time_h', address=4107, input_type='holding', data_type='uint16'),
        RegisterDef(key='free_cooling_end_time_m', address=4108, input_type='holding', data_type='uint16'),
        RegisterDef(key='free_cooling_active', address=4110, input_type='input', data_type='uint16'),
        RegisterDef(key='free_cooling_min_speed_saf', address=4111, input_type='holding', data_type='uint16'),
        RegisterDef(key='free_cooling_min_speed_eaf', address=4112, input_type='holding', data_type='uint16'),

        # --- Filter ---
        RegisterDef(key='filter_replacement_period', address=7000, input_type='holding', data_type='uint16', unit='months'),
        # Remaining filter time: 32-bit (low=7004, high=7005) per PDF (-1 offset applied)
        RegisterDef(key='time_to_filter_replacement', address=7004, input_type='input', data_type='uint32', unit='s'),
        # Timestamp of last filter replacement: 32-bit (low=7001, high=7002) per PDF (-1 offset applied)
        RegisterDef(key='filter_replacement_time', address=7001, input_type='input', data_type='uint32', unit='s'),

        # --- Sensors ---
        RegisterDef(key='digital_ui_1', address=12020, input_type='input', data_type='uint16'),
        RegisterDef(key='outdoor_temperature', address=12101, input_type='input', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='supply_temperature', address=12102, input_type='input', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='efficiency_temperature', address=12106, input_type='input', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='overheat_temperature', address=12107, input_type='input', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),
        RegisterDef(key='relative_moisture_extraction', address=12135, input_type='input', data_type='uint16', unit='%', device_class='humidity'),
        RegisterDef(key='saf_speed_rpm', address=12400, input_type='input', data_type='uint16', unit='rpm'),
        RegisterDef(key='eaf_speed_rpm', address=12401, input_type='input', data_type='uint16', unit='rpm'),
        RegisterDef(key='extract_temperature', address=12543, input_type='input', data_type='int16', scale=0.1, precision=1, unit='°C', device_class='temperature'),

        # --- Outputs and alarms ---
        RegisterDef(key='supply_air_fan_pwr_fact', address=14000, input_type='input', data_type='uint16', unit='%'),
        RegisterDef(key='extractor_fan_pwr_fact', address=14001, input_type='input', data_type='uint16', unit='%'),
        RegisterDef(key='heat_recovery', address=14102, input_type='input', data_type='uint16', unit='%'),
        RegisterDef(key='triac_control_signal', address=14380, input_type='input', data_type='uint16'),
        RegisterDef(key='filter_alarm', address=15141, input_type='input', data_type='uint16'),
        RegisterDef(key='supply_air_temp_low_alarm', address=15176, input_type='input', data_type='uint16'),
        RegisterDef(key='filter_warning_alarm', address=15543, input_type='input', data_type='uint16'),
        RegisterDef(key='filter_warning_alarm_delay_counter', address=15548, input_type='input', data_type='uint16'),
        RegisterDef(key='a_alarm', address=15900, input_type='input', data_type='uint16'),
        RegisterDef(key='b_alarm', address=15901, input_type='input', data_type='uint16'),
        RegisterDef(key='c_alarm', address=15902, input_type='input', data_type='uint16'),
    ]


    def compute_derived(self, data: dict[str, Any]) -> dict[str, Any]:
        """Compute derived values from raw register data.

        Notes:
        - Keep user-facing text OUT of the model.
        - For UI, prefer language-neutral keys + numeric values.
        """

        def _to_int(value: Any, default: int = 0) -> int:
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return default

        out: dict[str, Any] = {}

        # ------------------------------------------------------------
        # Filter status / remaining time
        # ------------------------------------------------------------
        seconds = _to_int(data.get("time_to_filter_replacement"), 0)
        alarm = _to_int(data.get("filter_alarm"), 0)
        warning = _to_int(data.get("filter_warning_alarm"), 0)

        # ALWAYS define these to avoid UnboundLocalError
        days = 0
        months = 0
        if seconds > 0:
            days = seconds // 86400
            months = days // 30

        out["filter_time_remaining_s"] = seconds
        out["filter_time_remaining_days"] = int(days)
        out["filter_time_remaining_months"] = int(months)

        if alarm == 1:
            out["next_filter_change_status"] = "replace_filter"
        elif warning == 1:
            out["next_filter_change_status"] = "warning"
        elif seconds <= 0:
            out["next_filter_change_status"] = "unknown"
        else:
            out["next_filter_change_status"] = "ok"

        if seconds <= 0:
            out["next_filter_change_bucket"] = "unknown"
        else:
            if days > 548:
                out["next_filter_change_bucket"] = "more_than_18_months"
            elif days >= 31:
                out["next_filter_change_bucket"] = "months"
            else:
                out["next_filter_change_bucket"] = "days"

        # Backwards-compatible legacy text for existing sensor "next_filter_change".
        # Keep in English to avoid hardcoded Norwegian in code.
        if alarm == 1:
            out["next_filter_change"] = "Replace filter!"
        elif warning == 1:
            out["next_filter_change"] = "Filter warning"
        elif seconds <= 0:
            out["next_filter_change"] = "Unknown"
        else:
            if days > 548:
                out["next_filter_change"] = "More than 18 months"
            elif days >= 31:
                out["next_filter_change"] = f"{months} months"
            else:
                out["next_filter_change"] = f"{days} days"

        # ------------------------------------------------------------
        # Season
        # ------------------------------------------------------------
        season = _to_int(data.get("summer_winter_operation_1_0"), -1)
        out["active_season"] = "summer" if season == 0 else "winter" if season == 1 else "unknown"

        # ------------------------------------------------------------
        # IAQ level text
        # ------------------------------------------------------------
        v = _to_int(data.get("iaq_level"), -1)
        out["iaq_level_text"] = {0: "economy", 1: "good", 2: "improve"}.get(v, "unknown")

        # ------------------------------------------------------------
        # Regulation mode text
        # ------------------------------------------------------------
        reg_mode = _to_int(data.get("supply_air_room_exhaust_reg"), -1)
        if reg_mode == 0:
            out["regulation_mode_text"] = "supply_air"
        elif reg_mode == 1:
            out["regulation_mode_text"] = "room"
        elif reg_mode == 2:
            out["regulation_mode_text"] = "exhaust"
        else:
            out["regulation_mode_text"] = "unknown"

        # ------------------------------------------------------------
        # Mode status text (language-neutral keys)
        # ------------------------------------------------------------
        mode = _to_int(data.get("mode_status_register"), -1)
        man = _to_int(data.get("manual_mode_command_register"), -1)

        if mode == 0:
            out["mode_status_text"] = "auto_demand_control"
        elif mode == 1:
            out["mode_status_text"] = {
                0: "manual_stop",
                2: "manual_low",
                3: "manual_normal",
                4: "manual_high",
            }.get(man, "manual_unknown")
        else:
            out["mode_status_text"] = SaveModel.STATUS_MODE_TO_KEY.get(mode, "unknown")

        # ------------------------------------------------------------
        # Estimated flow rates (m³/h)
        # ------------------------------------------------------------
        p_e = _to_int(data.get("extractor_fan_pwr_fact"), 0)
        p_s = _to_int(data.get("supply_air_fan_pwr_fact"), 0)

        out["exhaust_air_flow_rate"] = round(p_e * self.flow_factor)
        out["supply_air_flow_rate"] = round(p_s * self.flow_factor)

        return out