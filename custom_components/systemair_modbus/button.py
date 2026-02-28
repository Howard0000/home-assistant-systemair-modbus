"""Button platform for Systemair Modbus.

Provides one-tap actions as entities so they are part of the integration (HACS-friendly).
"""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import SystemairBaseEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    model = coordinator.model

    entities: list[ButtonEntity] = [
        # Modes
        SetModeButton(entry, coordinator, client, model, translation_key="set_auto", mode_label="Auto"),
        SetModeButton(entry, coordinator, client, model, translation_key="set_away", mode_label="Away"),
        SetModeButton(entry, coordinator, client, model, translation_key="set_holiday", mode_label="Holiday"),
        SetModeButton(entry, coordinator, client, model, translation_key="set_party", mode_label="Party"),
        SetModeButton(entry, coordinator, client, model, translation_key="set_boost", mode_label="Boost"),
        # Manual speeds (forces Manual first)
        SetManualSpeedButton(entry, coordinator, client, model, translation_key="fan_low", speed_label="Low"),
        SetManualSpeedButton(entry, coordinator, client, model, translation_key="fan_normal", speed_label="Normal"),
        SetManualSpeedButton(entry, coordinator, client, model, translation_key="fan_high", speed_label="High"),
        StopButton(entry, coordinator, client, model),

        # Filter
        FilterReplacedButton(entry, coordinator, client, model),
    ]

    async_add_entities(entities)


class _BaseActionButton(SystemairBaseEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model


class SetModeButton(_BaseActionButton):
    _attr_icon = "mdi:fan"

    def __init__(self, entry: ConfigEntry, coordinator, client, model, translation_key: str, mode_label: str) -> None:
        super().__init__(entry, coordinator, client, model)
        self._mode_label = mode_label
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_btn_{translation_key}"

    async def async_press(self) -> None:
        if self._mode_label not in self._model.COMMAND_MODE_OPTIONS:
            raise HomeAssistantError(f"Unsupported mode: {self._mode_label}")

        value = self._model.COMMAND_MODE_OPTIONS[self._mode_label]
        await self._client.write_register(self._model.ADDR_MODE_COMMAND, value)
        await self.coordinator.async_request_refresh()


class SetManualSpeedButton(_BaseActionButton):
    _attr_icon = "mdi:fan-speed-1"

    def __init__(self, entry: ConfigEntry, coordinator, client, model, translation_key: str, speed_label: str) -> None:
        super().__init__(entry, coordinator, client, model)
        self._speed_label = speed_label
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_btn_{translation_key}"

    async def async_press(self) -> None:
        # Force Manual mode first
        manual_value = self._model.COMMAND_MODE_OPTIONS.get("Manual")
        if manual_value is None:
            raise HomeAssistantError("Model does not support Manual mode command")

        await self._client.write_register(self._model.ADDR_MODE_COMMAND, manual_value)

        # Then set manual speed
        if self._speed_label not in self._model.MANUAL_SPEED_OPTIONS:
            raise HomeAssistantError(f"Unsupported manual speed: {self._speed_label}")

        speed_value = self._model.MANUAL_SPEED_OPTIONS[self._speed_label]
        await self._client.write_register(self._model.ADDR_MANUAL_SPEED_COMMAND, speed_value)
        await self.coordinator.async_request_refresh()


class StopButton(_BaseActionButton):
    _attr_translation_key = "fan_stop"
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator, client, model)
        self._attr_unique_id = f"{entry.entry_id}_btn_fan_stop"

    async def async_press(self) -> None:
        # Some units only allow STOP if a specific register says it's allowed.
        allowed_raw = self.coordinator.data.get("fan_manual_stop_allowed_register")
        allowed = False
        try:
            allowed = int(float(allowed_raw or 0)) == 1
        except (TypeError, ValueError):
            allowed = False

        manual_value = self._model.COMMAND_MODE_OPTIONS.get("Manual")
        if manual_value is None:
            raise HomeAssistantError("Model does not support Manual mode command")

        await self._client.write_register(self._model.ADDR_MODE_COMMAND, manual_value)

        if allowed:
            await self._client.write_register(
                self._model.ADDR_MANUAL_SPEED_COMMAND,
                self._model.MANUAL_SPEED_OPTIONS["Stop"],
            )
        else:
            # Soft-stop fallback: Low speed
            _LOGGER.warning(
                "STOP not allowed (fan_manual_stop_allowed_register != 1). Falling back to Low speed."
            )
            await self._client.write_register(
                self._model.ADDR_MANUAL_SPEED_COMMAND,
                self._model.MANUAL_SPEED_OPTIONS["Low"],
            )

        await self.coordinator.async_request_refresh()


class FilterReplacedButton(_BaseActionButton):
    """Reset filter timer (as if user pressed 'Filter replaced' on the unit).

    This resets the internal counter used to calculate remaining filter time.
    Addresses are 0-based (PDF - 1), same as the rest of the integration.

    - filter replacement counter: 7001/7002 (low/high 16-bit) => uint32 seconds/counter
    """
    _attr_translation_key = "filter_replaced"
    _attr_icon = "mdi:air-filter"

    _ADDR_FILTER_REPLACEMENT_TIME_L = 7001
    _ADDR_FILTER_REPLACEMENT_TIME_H = 7002

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator, client, model)
        self._attr_unique_id = f"{entry.entry_id}_btn_filter_replaced"

    async def async_press(self) -> None:
        try:
            # Reset counter to 0 (low/high)
            await self._client.write_register(self._ADDR_FILTER_REPLACEMENT_TIME_L, 0)
            await self._client.write_register(self._ADDR_FILTER_REPLACEMENT_TIME_H, 0)
        except Exception as err:
            _LOGGER.warning("Filter replaced failed: %s", err)
            raise HomeAssistantError(f"Filter replaced failed: {err}") from err

        await self.coordinator.async_request_refresh()