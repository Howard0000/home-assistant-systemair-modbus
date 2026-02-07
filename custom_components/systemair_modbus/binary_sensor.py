"""Binary sensor platform for Systemair Modbus."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import SystemairBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities: list[BinarySensorEntity] = [
        SystemairBinaryFromKey(entry, coordinator, "free_cooling_active", "free_cooling_active"),
        SystemairBinaryFromKey(entry, coordinator, "cooker_hood_active", "cooker_hood_active"),
        EcoFunctionActive(entry, coordinator),
        PressureGuardActive(entry, coordinator),
    ]

    async_add_entities(entities)


class SystemairBinaryFromKey(SystemairBaseEntity, BinarySensorEntity):
    """Binary sensor backed by a numeric key (0/1) in coordinator data."""

    def __init__(self, entry: ConfigEntry, coordinator, source_key: str, translation_key: str) -> None:
        super().__init__(entry, coordinator)
        self._source_key = source_key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{self._uid_base}_{source_key}_bin"

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get(self._source_key)
        try:
            return int(float(raw or 0)) == 1
        except (TypeError, ValueError):
            return None


class EcoFunctionActive(SystemairBaseEntity, BinarySensorEntity):
    _attr_translation_key = "eco_function_active"
    _attr_icon = "mdi:leaf"

    def __init__(self, entry: ConfigEntry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._uid_base}_eco_function_active_bin"

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get("eco_function_active")
        try:
            return int(float(raw or 0)) == 1
        except (TypeError, ValueError):
            return None


class PressureGuardActive(SystemairBaseEntity, BinarySensorEntity):
    _attr_translation_key = "pressure_guard_active"
    _attr_icon = "mdi:gauge"

    def __init__(self, entry: ConfigEntry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{self._uid_base}_pressure_guard_active_bin"

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get("pressure_guard_active")
        try:
            return int(float(raw or 0)) == 1
        except (TypeError, ValueError):
            return None
