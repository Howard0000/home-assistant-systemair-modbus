"""Fan platform for Systemair Modbus."""
from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import DOMAIN
from .entity import SystemairBaseEntity

ORDERED_MANUAL_SPEEDS = ["Low", "Normal", "High"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    model = coordinator.model

    if hasattr(model, "MANUAL_SPEED_OPTIONS") and hasattr(model, "ADDR_MANUAL_SPEED_COMMAND"):
        async_add_entities([SystemairManualSpeedFan(entry, coordinator, client, model)])


class SystemairManualSpeedFan(SystemairBaseEntity, FanEntity):
    """Fan entity backed by the unit's manual speed command register."""

    _attr_icon = "mdi:fan"
    _attr_name = None
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_manual_speed_fan"

    def _current_speed(self) -> str | None:
        raw = self.coordinator.data.get("manual_mode_command_register")
        try:
            value = int(float(raw))
        except (TypeError, ValueError):
            return None

        inverse = getattr(self._model, "MANUAL_SPEED_OPTIONS_INV", None)
        if isinstance(inverse, dict):
            return inverse.get(value)

        return {val: key for key, val in self._model.MANUAL_SPEED_OPTIONS.items()}.get(value)

    @property
    def is_on(self) -> bool | None:
        speed = self._current_speed()
        if speed is None:
            return None
        return speed != "Stop"

    @property
    def percentage(self) -> int | None:
        speed = self._current_speed()
        if speed is None:
            return None
        if speed == "Stop":
            return 0
        if speed not in ORDERED_MANUAL_SPEEDS:
            return None
        return ordered_list_item_to_percentage(ORDERED_MANUAL_SPEEDS, speed)

    @property
    def speed_count(self) -> int:
        return len(ORDERED_MANUAL_SPEEDS)

    async def async_turn_on(self, percentage: int | None = None, **kwargs) -> None:
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return

        speed = self._current_speed()
        if speed and speed != "Stop":
            return

        await self._write_speed("Normal")

    async def async_turn_off(self, **kwargs) -> None:
        if "Stop" in self._model.MANUAL_SPEED_OPTIONS:
            await self._write_speed("Stop")
            return

        await self._write_speed(ORDERED_MANUAL_SPEEDS[0])

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage <= 0:
            await self.async_turn_off()
            return

        speed = percentage_to_ordered_list_item(ORDERED_MANUAL_SPEEDS, percentage)
        await self._write_speed(speed)

    async def _write_speed(self, speed: str) -> None:
        await self._client.write_register(
            self._model.ADDR_MANUAL_SPEED_COMMAND,
            self._model.MANUAL_SPEED_OPTIONS[speed],
        )
        await self.coordinator.async_request_refresh()
