"""Coordinator for Systemair Modbus integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .modbus import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)


class SystemairCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, *, name: str, client: ModbusTcpClient, model, scan_interval_s: int) -> None:
        self.client = client
        self.model = model

        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=scan_interval_s),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        base = await self.client.read_register_map([r.__dict__ for r in self.model.REGISTERS])
        derived = self.model.compute_derived(base)
        base.update(derived)
        return base
