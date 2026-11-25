"""Full-map Modbus RTU coordinator for SAVE and legacy CD4.

Read all eligible registers every refresh. No rotating cursor, no overlapping
sweeps. Adjacent addresses of the same function code are read in blocks.
"""
from __future__ import annotations

import logging
import time
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .derived import compute_derived
from .model_identity import read_save_model_name
from .airflow import update_save_airflow

_LOGGER = logging.getLogger(__name__)
POLL_SECONDS = 30  # Default RTU interval; can be overridden by entry options.
MAX_BLOCK_WORDS = 12
DEPENDENCIES = {
    "filter_time_remaining_s": ("time_to_filter_replacement",),
    "filter_time_remaining_days": ("time_to_filter_replacement",),
    "filter_time_remaining_months": ("time_to_filter_replacement",),
    "next_filter_change_status": ("time_to_filter_replacement", "filter_alarm", "filter_warning_alarm"),
    "next_filter_change_bucket": ("time_to_filter_replacement",),
    "next_filter_change": ("time_to_filter_replacement", "filter_alarm", "filter_warning_alarm"),
    "active_season": ("summer_winter_operation_1_0",),
    "iaq_level_text": ("iaq_level",),
    "regulation_mode_text": ("supply_air_room_exhaust_reg",),
    "mode_status_text": ("mode_status_register", "manual_mode_command_register"),
    "exhaust_air_flow_rate": ("extractor_fan_pwr_fact",),
    "supply_air_flow_rate": ("supply_air_fan_pwr_fact",),
}


def _is_serial_port_unavailable(exc: Exception) -> bool:
    """Only classify transport-open failures, not Modbus register exceptions."""
    message = str(exc).lower()
    return "could not open serial port" in message or "cannot open serial port" in message


def _width(reg):
    return 2 if reg.data_type == "uint32" else 1


def _build_blocks(registers):
    """Only join exactly adjacent addresses; never read unlisted gap registers."""
    ordered = sorted(registers, key=lambda r: (r.input_type, r.address))
    blocks = []
    for reg in ordered:
        if blocks:
            prev = blocks[-1]
            last = prev[-1]
            size = reg.address + _width(reg) - prev[0].address
            if (reg.input_type == last.input_type
                    and reg.address == last.address + _width(last)
                    and size <= MAX_BLOCK_WORDS):
                prev.append(reg)
                continue
        blocks.append([reg])
    return tuple(tuple(b) for b in blocks)


class SerialModbusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client, model, scan_interval_s=POLL_SECONDS):
        self.client = client
        self.model = model
        self._values = {}
        self._airflow_override = None
        self._failed = set()
        self._cycles = 0
        self._startup_serial_failure_logged = False
        self._registers = tuple(model.REGISTERS)
        self._blocks = _build_blocks(self._registers)
        super().__init__(hass, _LOGGER, name=f"Systemair Modbus RTU {model.model_id} full",
                         update_interval=timedelta(seconds=max(10, int(scan_interval_s))))

    def _report_serial_unavailable(self, exc: Exception) -> None:
        """Startup race is informational once; later failures remain warnings."""
        if self._cycles == 0 and not self._startup_serial_failure_logged:
            self._startup_serial_failure_logged = True
            _LOGGER.info("Modbus RTU serial port not ready during initial read; next scheduled update will retry: %s", exc)
        else:
            _LOGGER.warning("Modbus RTU serial port unavailable; aborting sweep: %s", exc)

    async def _async_update_data(self):
        if not self._registers:
            raise UpdateFailed("No eligible model registers")
        started = time.monotonic()
        # SAVE identifies itself using an ASCII holding-register range.
        # CD4 has a normal numeric system_type register in its model map.
        if self.model.model_id == "save":
            model_name = await read_save_model_name(
                self.client, self.model, self._values.get("system_type")
            )
            if model_name:
                self._values["system_type"] = model_name
            update_save_airflow(self.model, self._values.get("system_type"), self._airflow_override)
        failures = set()
        requests = 0
        for block in self._blocks:
            try:
                requests += 1
                values = await self.client.read_block(block)
                for key, value in values.items():
                    self._values[key] = value
            except Exception as exc:
                if _is_serial_port_unavailable(exc):
                    # A disconnected serial port cannot be repaired by 98 single reads.
                    self._report_serial_unavailable(exc)
                    raise UpdateFailed("Modbus RTU serial port unavailable") from exc
                # A failed block must not hide healthy registers in that block.
                _LOGGER.warning("Modbus RTU block read failed at %s (%s): %s; trying singles",
                                block[0].address, block[0].input_type, exc)
                for reg in block:
                    try:
                        requests += 1
                        self._values[reg.key] = await self.client.read_register(reg)
                    except Exception as individual_exc:
                        if _is_serial_port_unavailable(individual_exc):
                            self._report_serial_unavailable(individual_exc)
                            raise UpdateFailed("Modbus RTU serial port unavailable") from individual_exc
                        self._values.pop(reg.key, None)
                        failures.add(reg.key)
                        _LOGGER.warning("Modbus RTU register %s addr=%s failed: %s",
                                        reg.key, reg.address, individual_exc)
        self._failed = failures
        self._cycles += 1
        result = dict(self._values)
        result.update(compute_derived(self.model, result, dependencies=DEPENDENCIES))
        result.update({
            "serial_registers_total": len(self._registers),
            "serial_registers_attempted": len(self._registers),
            "serial_registers_ok": sum(r.key in self._values for r in self._registers),
            "serial_registers_failed": len(failures),
            "serial_sweep_percent": 100,
            "serial_sweep_seconds": round(time.monotonic() - started, 2),
            "serial_requests_per_sweep": requests,
        })
        return result
