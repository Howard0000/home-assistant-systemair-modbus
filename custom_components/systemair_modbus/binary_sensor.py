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

    async_add_entities(
        [
            # User-facing alarm indicators (on/off)
            BoolFromRegister(entry, coordinator, "a_alarm", "mdi:alert-circle"),
            BoolFromRegister(entry, coordinator, "b_alarm", "mdi:alert-circle"),
            BoolFromRegister(entry, coordinator, "c_alarm", "mdi:alert-circle"),
            BoolFromRegister(entry, coordinator, "filter_alarm", "mdi:air-filter"),
            BoolFromRegister(entry, coordinator, "filter_warning_alarm", "mdi:air-filter"),
            FreeCoolingActive(entry, coordinator),
            CookerHoodActive(entry, coordinator),
            EcoFunctionActive(entry, coordinator),
            PressureGuardActive(entry, coordinator),
        ]
    )


class BoolFromRegister(SystemairBaseEntity, BinarySensorEntity):
    def __init__(self, entry: ConfigEntry, coordinator, source_key: str, icon: str) -> None:
        super().__init__(entry, coordinator)
        self._source_key = source_key
        self._attr_unique_id = f"{entry.entry_id}_{source_key}_bin"
        self._attr_translation_key = source_key
        self._attr_icon = icon

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get(self._source_key)
        try:
            return int(float(raw or 0)) == 1
        except (TypeError, ValueError):
            return None


class FreeCoolingActive(SystemairBaseEntity, BinarySensorEntity):
    def __init__(self, entry: ConfigEntry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_free_cooling_active_bin"
        self._attr_translation_key = "free_cooling_active"
        self._attr_icon = "mdi:snowflake"

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get("free_cooling_active")
        try:
            return int(float(raw or 0)) == 1
        except (TypeError, ValueError):
            return None


class CookerHoodActive(SystemairBaseEntity, BinarySensorEntity):
    def __init__(self, entry: ConfigEntry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_cooker_hood_active_bin"
        self._attr_translation_key = "cooker_hood_active"
        self._attr_icon = "mdi:fan"

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        try:
            hood_switch = int(float(data.get("extractor_hood_pressure_switch_off_on") or 0))
            mode_status = int(float(data.get("mode_status_register") or 0))
            return hood_switch == 1 or mode_status == 7
        except (TypeError, ValueError):
            return None
class EcoFunctionActive(SystemairBaseEntity, BinarySensorEntity):
    """Eco function active flag from register (0/1)."""

    def __init__(self, entry: ConfigEntry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_eco_function_active_bin"
        self._attr_translation_key = "eco_function_active"
        self._attr_icon = "mdi:leaf"

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get("eco_function_active")
        try:
            # Some units may report >0 when active.
            return int(float(raw or 0)) > 0
        except (TypeError, ValueError):
            return None


class PressureGuardActive(SystemairBaseEntity, BinarySensorEntity):
    """Pressure guard active when unit enters protection mode."""

    def __init__(self, entry: ConfigEntry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_pressure_guard_active_bin"
        self._attr_translation_key = "pressure_guard_active"
        self._attr_icon = "mdi:gauge"

    @property
    def is_on(self) -> bool | None:
        # Prefer derived mode_status_text if available.
        val = self.coordinator.data.get("mode_status_text")
        if val is not None:
            return str(val) == "pressure_guard"
        # Fallback to raw mode status register.
        raw = self.coordinator.data.get("mode_status_register")
        try:
            return int(float(raw or 0)) == 12
        except (TypeError, ValueError):
            return None
