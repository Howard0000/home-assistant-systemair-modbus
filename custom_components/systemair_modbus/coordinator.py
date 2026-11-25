"""Coordinator for Systemair Modbus integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .modbus import ModbusTcpClient
from .derived import compute_derived
from .model_identity import read_save_model_name
from .airflow import update_save_airflow

_LOGGER = logging.getLogger(__name__)


class SystemairCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, *, name: str, client: ModbusTcpClient, model, scan_interval_s: int) -> None:
        self.client = client
        self.model = model
        self._save_model_text: str | None = None
        self._airflow_override: str | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=scan_interval_s),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        base = await self.client.read_register_map([r.__dict__ for r in self.model.REGISTERS])
        # Optional model text is cached on success, retried after startup failures.
        if getattr(self.model, "model_id", None) == "save":
            self._save_model_text = await read_save_model_name(
                self.client, self.model, self._save_model_text
            )
            base["system_type"] = self._save_model_text
            update_save_airflow(self.model, self._save_model_text, self._airflow_override)

        derived = compute_derived(self.model, base)
        base.update(derived)
        return base
