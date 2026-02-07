"""Switch platform for Systemair Modbus."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
            EcoModeSwitch(entry, coordinator, client, model),
            FreeCoolingSwitch(entry, coordinator, client, model),
        ]
    )


class EcoModeSwitch(SystemairBaseEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "eco_mode"
    _attr_icon = "mdi:leaf"

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_eco_mode_switch"

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get("eco_mode")
        try:
            return int(float(raw or 0)) == 1
        except (TypeError, ValueError):
            return None

    async def async_turn_on(self, **kwargs):
        await self._client.write_register(self._model.ADDR_ECO_MODE, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._client.write_register(self._model.ADDR_ECO_MODE, 0)
        await self.coordinator.async_request_refresh()


class FreeCoolingSwitch(SystemairBaseEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "free_cooling"
    _attr_icon = "mdi:snowflake"

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_free_cooling_switch"

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get("free_cooling_enable")
        try:
            return int(float(raw or 0)) == 1
        except (TypeError, ValueError):
            return None

    async def async_turn_on(self, **kwargs):
        await self._client.write_register(self._model.ADDR_FREE_COOLING_ENABLE, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._client.write_register(self._model.ADDR_FREE_COOLING_ENABLE, 0)
        await self.coordinator.async_request_refresh()
