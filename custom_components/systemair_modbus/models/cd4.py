"""Systemair CD4 / D24810 legacy model (minimal register map + derived values).

This model is intentionally small to avoid invalid register reads on older panels.

All addresses in this file are Modbus client offsets (PDF address - 1).
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
    unit: str | None = None



class Cd4Model:
    model_id = "legacy_cd4"
    model_name = "Systemair CD4 (legacy)"
    manufacturer = "Systemair"
    ...


    def __init__(self, *, qv_max: int | None = None) -> None:
        # Not used for now, but keep same signature as SaveModel
        self._qv_max = qv_max

    # ---- Key legacy registers (based on D24810 manual + what we simulate) ----
    ADDR_FAN_SPEED_LEVEL = 100

    ADDR_SYSTEM_TYPE = 500
    ADDR_SYSTEM_PROG_V_HIGH = 501
    ADDR_SYSTEM_PROG_V_MID = 502
    ADDR_SYSTEM_PROG_V_LOW = 503

    ADDR_FILTER_MONTHS = 600
    ADDR_FILTER_DAYS = 601

    # Optional (used by some legacy setups / our simulator)
    ADDR_SF_RPM = 110
    ADDR_EF_RPM = 111
    ADDR_MANUAL_FAN_STOP_ALLOWED = 113

    # NOTE: We DO NOT define the SAVE Touch feature registers here
    # (mode command, free cooling, eco mode, etc.). We will gate those platforms next.

    REGISTERS: list[RegisterDef] = [
        RegisterDef(key="fan_speed_level", address=ADDR_FAN_SPEED_LEVEL, input_type="holding", data_type="uint16"),

        RegisterDef(key="system_type", address=ADDR_SYSTEM_TYPE, input_type="holding", data_type="uint16"),
        RegisterDef(key="system_prog_v_high", address=ADDR_SYSTEM_PROG_V_HIGH, input_type="holding", data_type="uint16"),
        RegisterDef(key="system_prog_v_mid", address=ADDR_SYSTEM_PROG_V_MID, input_type="holding", data_type="uint16"),
        RegisterDef(key="system_prog_v_low", address=ADDR_SYSTEM_PROG_V_LOW, input_type="holding", data_type="uint16"),

        RegisterDef(key="filter_months", address=ADDR_FILTER_MONTHS, input_type="holding", data_type="uint16", unit="months"),
        RegisterDef(key="filter_days", address=ADDR_FILTER_DAYS, input_type="holding", data_type="uint16", unit="days"),

        RegisterDef(key="sf_rpm", address=ADDR_SF_RPM, input_type="holding", data_type="uint16", unit="rpm"),
        RegisterDef(key="ef_rpm", address=ADDR_EF_RPM, input_type="holding", data_type="uint16", unit="rpm"),
        RegisterDef(key="manual_fan_stop_allowed", address=ADDR_MANUAL_FAN_STOP_ALLOWED, input_type="holding", data_type="uint16"),
    ]

    def compute_derived(self, data: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}

        lvl_raw = data.get("fan_speed_level")
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

        # These are SAVE Touch oriented derived sensors; for legacy we return unknown/None
        out["active_season"] = "unknown"
        out["iaq_level_text"] = "unknown"
        out["regulation_mode_text"] = "unknown"
        out["exhaust_air_flow_rate"] = None
        out["supply_air_flow_rate"] = None

        # next_filter_change: rough estimate from months/days (legacy registers)
        months_raw = data.get("filter_months")
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
            if remaining >= 31:
                out["next_filter_change"] = f"{int(remaining / 30)} mnd"
            else:
                out["next_filter_change"] = f"{remaining} dager"

        return out
