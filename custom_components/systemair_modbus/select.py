"""Select platform for Systemair Modbus."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import SystemairBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    model = coordinator.model

    async_add_entities(
        [
            ModeSelect(entry, coordinator, client, model),
            ManualSpeedSelect(entry, coordinator, client, model),
            FreeCoolingMinSafSelect(entry, coordinator, client, model),
            FreeCoolingMinEafSelect(entry, coordinator, client, model),
        ]
    )


class ModeSelect(SystemairBaseEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "mode_command"
    _attr_icon = "mdi:fan"

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_mode_select"
        self._attr_options = list(model.COMMAND_MODE_OPTIONS.keys())

    @property
    def current_option(self) -> str | None:
        # Display based on status register (not command)
        raw = self.coordinator.data.get("mode_status_register")
        try:
            v = int(float(raw))
        except (TypeError, ValueError):
            return None
        return self._model.STATUS_MODE_TO_LABEL.get(v)

    async def async_select_option(self, option: str) -> None:
        if option not in self._model.COMMAND_MODE_OPTIONS:
            raise HomeAssistantError("Invalid option")

        await self._client.write_register(self._model.ADDR_MODE_COMMAND, self._model.COMMAND_MODE_OPTIONS[option])
        await self.coordinator.async_request_refresh()


class ManualSpeedSelect(SystemairBaseEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "manual_speed"
    _attr_icon = "mdi:fan-speed-1"

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_manual_speed_select"
        self._attr_options = list(model.MANUAL_SPEED_OPTIONS.keys())

    @property
    def current_option(self) -> str | None:
        raw = self.coordinator.data.get("manual_mode_command_register")
        try:
            v = int(float(raw))
        except (TypeError, ValueError):
            return None
        inv = {val: key for key, val in self._model.MANUAL_SPEED_OPTIONS.items()}
        return inv.get(v)

    async def async_select_option(self, option: str) -> None:
        if option not in self._model.MANUAL_SPEED_OPTIONS:
            raise HomeAssistantError("Invalid option")

        await self._client.write_register(self._model.ADDR_MANUAL_SPEED_COMMAND, self._model.MANUAL_SPEED_OPTIONS[option])
        await self.coordinator.async_request_refresh()


class FreeCoolingMinSafSelect(SystemairBaseEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "free_cooling_min_saf"
    _attr_icon = "mdi:fan"

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_fc_min_saf_select"
        self._attr_options = list(model.FREE_COOLING_MIN_SPEED_OPTIONS.keys())

    @property
    def current_option(self) -> str | None:
        raw = self.coordinator.data.get("free_cooling_min_speed_saf")
        try:
            v = int(float(raw))
        except (TypeError, ValueError):
            return None
        inv = {val: key for key, val in self._model.FREE_COOLING_MIN_SPEED_OPTIONS.items()}
        return inv.get(v)

    async def async_select_option(self, option: str) -> None:
        if option not in self._model.FREE_COOLING_MIN_SPEED_OPTIONS:
            raise HomeAssistantError("Invalid option")
        await self._client.write_register(self._model.ADDR_FREE_COOLING_MIN_SAF, self._model.FREE_COOLING_MIN_SPEED_OPTIONS[option])
        await self.coordinator.async_request_refresh()


class FreeCoolingMinEafSelect(SystemairBaseEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "free_cooling_min_eaf"
    _attr_icon = "mdi:fan"

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_fc_min_eaf_select"
        self._attr_options = list(model.FREE_COOLING_MIN_SPEED_OPTIONS.keys())

    @property
    def current_option(self) -> str | None:
        raw = self.coordinator.data.get("free_cooling_min_speed_eaf")
        try:
            v = int(float(raw))
        except (TypeError, ValueError):
            return None
        inv = {val: key for key, val in self._model.FREE_COOLING_MIN_SPEED_OPTIONS.items()}
        return inv.get(v)

    async def async_select_option(self, option: str) -> None:
        if option not in self._model.FREE_COOLING_MIN_SPEED_OPTIONS:
            raise HomeAssistantError("Invalid option")
        await self._client.write_register(self._model.ADDR_FREE_COOLING_MIN_EAF, self._model.FREE_COOLING_MIN_SPEED_OPTIONS[option])
        await self.coordinator.async_request_refresh()
