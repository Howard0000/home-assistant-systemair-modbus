"""Fan platform for Systemair Modbus."""
from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import DOMAIN
from .entity import SystemairBaseEntity


def _supports_manual_fan(model) -> bool:
    """Return True when a model exposes the common manual-fan interface."""
    return all(
        hasattr(model, attr)
        for attr in (
            "ADDR_MANUAL_SPEED_COMMAND",
            "MANUAL_SPEED_OPTIONS",
            "MANUAL_SPEED_OPTIONS_INV",
            "MANUAL_SPEED_ORDER",
        )
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    model = coordinator.model

    if not _supports_manual_fan(model):
        return

    async_add_entities(
        [SystemairManualSpeedFan(entry, coordinator, client, model)]
    )


class SystemairManualSpeedFan(SystemairBaseEntity, FanEntity):
    """Systemair manual ventilation speed as a standard HA fan entity."""

    _attr_translation_key = "ventilation_fan"
    _attr_icon = "mdi:fan"

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_manual_speed_fan"
        self._attr_suggested_object_id = "ventilation_fan"

    @property
    def _speed_order(self) -> tuple[str, ...]:
        return tuple(self._model.MANUAL_SPEED_ORDER)

    @property
    def _stop_option(self) -> str:
        return getattr(self._model, "MANUAL_SPEED_STOP_OPTION", "stop")

    def _current_speed(self) -> str | None:
        raw = self.coordinator.data.get("manual_mode_command_register")
        try:
            value = int(float(raw))
        except (TypeError, ValueError):
            return None

        inverse = self._model.MANUAL_SPEED_OPTIONS_INV
        if isinstance(inverse, dict):
            return inverse.get(value)

        return None

    def _stop_allowed(self) -> bool:
        """Return whether this unit reports support for manual fan stop."""
        raw = self.coordinator.data.get("fan_manual_stop_allowed_register")
        try:
            return int(float(raw)) == 1
        except (TypeError, ValueError):
            return False

    @property
    def supported_features(self) -> FanEntityFeature:
        features = FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON
        if self._stop_allowed() and self._stop_option in self._model.MANUAL_SPEED_OPTIONS:
            features |= FanEntityFeature.TURN_OFF
        return features

    @property
    def is_on(self) -> bool | None:
        speed = self._current_speed()
        if speed is None:
            return None
        return speed != self._stop_option

    @property
    def percentage(self) -> int | None:
        speed = self._current_speed()
        if speed is None:
            return None
        if speed == self._stop_option:
            return 0
        if speed not in self._speed_order:
            return None
        return ordered_list_item_to_percentage(self._speed_order, speed)

    @property
    def speed_count(self) -> int:
        return len(self._speed_order)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set one of the discrete manual speeds through HA's percentage API."""
        if percentage <= 0:
            await self.async_turn_off()
            return

        speed = percentage_to_ordered_list_item(self._speed_order, percentage)
        await self._write_speed(speed)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the ventilation fan on.

        If no percentage is supplied, preserve the current running speed.
        If currently stopped/unknown, use Normal as a sensible default when
        available; otherwise use the first supported running speed.
        """
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return

        current = self._current_speed()
        if current in self._speed_order:
            return

        default_speed = (
            "normal" if "normal" in self._speed_order else self._speed_order[0]
        )
        await self._write_speed(default_speed)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off only when the CD4 unit explicitly supports stop."""
        if not self._stop_allowed():
            # Do not silently map an OFF request to Low. The entity does not
            # advertise TURN_OFF when stop is unsupported.
            return

        if self._stop_option not in self._model.MANUAL_SPEED_OPTIONS:
            return

        await self._write_speed(self._stop_option)

    async def _write_speed(self, speed: str) -> None:
        value = self._model.MANUAL_SPEED_OPTIONS.get(speed)
        if value is None:
            return

        await self._client.write_register(
            self._model.ADDR_MANUAL_SPEED_COMMAND,
            value,
        )
        await self.coordinator.async_request_refresh()
