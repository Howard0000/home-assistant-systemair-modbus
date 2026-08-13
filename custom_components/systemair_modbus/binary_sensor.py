"""Binary sensor platform for Systemair Modbus."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import SystemairBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    model = coordinator.model

    if getattr(model, "model_id", None) == "legacy_cd4":
        async_add_entities(
            [
                BoolFromRegister(
                    entry,
                    coordinator,
                    source_key="rotor_relay_active",
                    translation_key="cd4_rotor_active",
                    icon="mdi:rotate-3d-variant",
                ),
                BoolFromRegister(
                    entry,
                    coordinator,
                    source_key="alarm_relay_active",
                    translation_key="cd4_alarm_relay_active",
                    icon="mdi:alert-circle",
                    device_class=BinarySensorDeviceClass.PROBLEM,
                ),
                BoolFromRegister(
                    entry,
                    coordinator,
                    source_key="fan_manual_stop_allowed_register",
                    translation_key="cd4_manual_fan_stop_allowed",
                    icon="mdi:fan-off",
                    entity_category=EntityCategory.DIAGNOSTIC,
                    enabled_default=False,
                ),
                BitFromRegister(
                    entry,
                    coordinator,
                    source_key="pcu_pb_relays",
                    bit=0,
                    translation_key="cd4_preheater_active",
                    icon="mdi:radiator",
                    entity_category=EntityCategory.DIAGNOSTIC,
                    enabled_default=False,
                ),
                BitFromRegister(
                    entry,
                    coordinator,
                    source_key="pcu_pb_relays",
                    bit=1,
                    translation_key="cd4_reheater_active",
                    icon="mdi:radiator",
                ),
                BitFromRegister(
                    entry,
                    coordinator,
                    source_key="pcu_pb_relays",
                    bit=2,
                    translation_key="cd4_heater_relay_active",
                    icon="mdi:heating-coil",
                    entity_category=EntityCategory.DIAGNOSTIC,
                    enabled_default=False,
                ),
            ]
        )
        return

    # SAVE
    async_add_entities(
        [
            BoolFromRegister(entry, coordinator, "a_alarm", "a_alarm", "mdi:alert-circle"),
            BoolFromRegister(entry, coordinator, "b_alarm", "b_alarm", "mdi:alert-circle"),
            BoolFromRegister(entry, coordinator, "c_alarm", "c_alarm", "mdi:alert-circle"),
            BoolFromRegister(
                entry,
                coordinator,
                "filter_alarm",
                "filter_alarm",
                "mdi:air-filter",
            ),
            BoolFromRegister(
                entry,
                coordinator,
                "filter_warning_alarm",
                "filter_warning_alarm",
                "mdi:air-filter",
            ),
            FreeCoolingActive(entry, coordinator),
            CookerHoodActive(entry, coordinator),
            EcoFunctionActive(entry, coordinator),
            PressureGuardActive(entry, coordinator),
        ]
    )


class BoolFromRegister(SystemairBaseEntity, BinarySensorEntity):
    def __init__(
        self,
        entry: ConfigEntry,
        coordinator,
        source_key: str,
        translation_key: str,
        icon: str,
        device_class: BinarySensorDeviceClass | None = None,
        entity_category: EntityCategory | None = None,
        enabled_default: bool = True,
    ) -> None:
        super().__init__(entry, coordinator)
        self._source_key = source_key
        self._attr_unique_id = f"{entry.entry_id}_{source_key}_bin"
        self._attr_translation_key = translation_key
        self._attr_icon = icon
        if device_class is not None:
            self._attr_device_class = device_class
        if entity_category is not None:
            self._attr_entity_category = entity_category
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get(self._source_key)
        if raw is None:
            return None
        try:
            return int(float(raw)) == 1
        except (TypeError, ValueError):
            return None


class BitFromRegister(SystemairBaseEntity, BinarySensorEntity):
    """Binary sensor decoded from a packed CD4 register bit."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator,
        source_key: str,
        bit: int,
        translation_key: str,
        icon: str,
        device_class: BinarySensorDeviceClass | None = None,
        entity_category: EntityCategory | None = None,
        enabled_default: bool = True,
    ) -> None:
        super().__init__(entry, coordinator)
        self._source_key = source_key
        self._bit = bit
        self._attr_unique_id = f"{entry.entry_id}_{source_key}_bit_{bit}"
        self._attr_translation_key = translation_key
        self._attr_icon = icon
        if device_class is not None:
            self._attr_device_class = device_class
        if entity_category is not None:
            self._attr_entity_category = entity_category
        self._attr_entity_registry_enabled_default = enabled_default

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get(self._source_key)
        if raw is None:
            return None
        try:
            value = int(float(raw))
        except (TypeError, ValueError):
            return None
        return bool(value & (1 << self._bit))


class FreeCoolingActive(SystemairBaseEntity, BinarySensorEntity):
    def __init__(self, entry: ConfigEntry, coordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_free_cooling_active_bin"
        self._attr_translation_key = "free_cooling_active"
        self._attr_icon = "mdi:snowflake"

    @property
    def is_on(self) -> bool | None:
        raw = self.coordinator.data.get("free_cooling_active")
        if raw is None:
            return None
        try:
            return int(float(raw)) == 1
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
        if raw is None:
            return None
        try:
            return int(float(raw)) > 0
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
        val = self.coordinator.data.get("mode_status_text")
        if val is not None:
            return str(val) == "pressure_guard"

        raw = self.coordinator.data.get("mode_status_register")
        try:
            return int(float(raw or 0)) == 12
        except (TypeError, ValueError):
            return None
