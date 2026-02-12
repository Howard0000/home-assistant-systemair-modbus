"""Number platform for Systemair Modbus."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
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
            # Varigheter / offset
            IntNumber(entry, coordinator, client, "holiday_mode_duration", model.ADDR_HOLIDAY_DURATION_DAYS, 0, 365, 1, unit="days"),
            IntNumber(entry, coordinator, client, "away_mode_duration", model.ADDR_AWAY_DURATION_HOURS, 0, 720, 1, unit="h"),
            IntNumber(entry, coordinator, client, "crowded_mode_duration", model.ADDR_CROWDED_DURATION_HOURS, 0, 72, 1, unit="h"),
            IntNumber(entry, coordinator, client, "refresh_mode_duration", model.ADDR_REFRESH_DURATION_MINUTES, 0, 120, 1, unit="min"),
            Temp01CNumber(entry, coordinator, client, "eco_heat_offset", model.ADDR_ECO_HEAT_OFFSET_0_1C, -10.0, 10.0, 0.5, unit="°C"),

            # Free cooling
            Temp01CNumber(entry, coordinator, client, "free_cooling_daytime_min_temp", model.ADDR_FREE_COOLING_DAY_MIN_0_1C, 5.0, 30.0, 0.5, unit="°C"),
            Temp01CNumber(entry, coordinator, client, "free_cooling_night_high_limit", model.ADDR_FREE_COOLING_NIGHT_HIGH_0_1C, 5.0, 30.0, 0.5, unit="°C"),
            Temp01CNumber(entry, coordinator, client, "free_cooling_night_low_limit", model.ADDR_FREE_COOLING_NIGHT_LOW_0_1C, 5.0, 30.0, 0.5, unit="°C"),
            Temp01CNumber(entry, coordinator, client, "free_cooling_room_cancel_temp", model.ADDR_FREE_COOLING_ROOM_CANCEL_0_1C, 5.0, 30.0, 0.5, unit="°C"),

            IntNumber(entry, coordinator, client, "free_cooling_start_time_h", model.ADDR_FREE_COOLING_START_H, 0, 23, 1, unit="h"),
            IntNumber(entry, coordinator, client, "free_cooling_start_time_m", model.ADDR_FREE_COOLING_START_M, 0, 59, 1, unit="min"),
            IntNumber(entry, coordinator, client, "free_cooling_end_time_h", model.ADDR_FREE_COOLING_END_H, 0, 23, 1, unit="h"),
            IntNumber(entry, coordinator, client, "free_cooling_end_time_m", model.ADDR_FREE_COOLING_END_M, 0, 59, 1, unit="min"),
        ]
    )


class _BaseNumber(SystemairBaseEntity, NumberEntity):
    def __init__(self, entry: ConfigEntry, coordinator, client, key: str, address: int, unit: str | None) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._key = key
        self._address = address

        self._attr_unique_id = f"{entry.entry_id}_{key}_number"
        self._attr_translation_key = key
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_mode = NumberMode.BOX
        if unit:
            self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        # Values are read from the coordinator register map
        return self.coordinator.data.get(self._key)


class IntNumber(_BaseNumber):
    def __init__(self, entry, coordinator, client, key: str, address: int, min_v: int, max_v: int, step: int, unit: str | None):
        super().__init__(entry, coordinator, client, key, address, unit)
        self._attr_native_min_value = float(min_v)
        self._attr_native_max_value = float(max_v)
        self._attr_native_step = float(step)

    async def async_set_native_value(self, value: float) -> None:
        await self._client.write_register(self._address, int(round(value)))
        await self.coordinator.async_request_refresh()


class Temp01CNumber(_BaseNumber):
    def __init__(self, entry, coordinator, client, key: str, address: int, min_v: float, max_v: float, step: float, unit: str | None):
        super().__init__(entry, coordinator, client, key, address, unit)
        self._attr_native_min_value = float(min_v)
        self._attr_native_max_value = float(max_v)
        self._attr_native_step = float(step)

    async def async_set_native_value(self, value: float) -> None:
        await self._client.write_0_1c(self._address, float(value))
        await self.coordinator.async_request_refresh()