"""Sensor platform for Systemair Modbus."""
from __future__ import annotations

import re

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import SystemairBaseEntity


# Prefixes we want to strip from internal keys to make nicer names/object_ids.
# Keep order from most specific to least specific.
_STRIP_PREFIXES: tuple[str, ...] = (
    "systemair_save_",
    "save_",
    "systemair_",
)


def _strip_prefixes(key: str) -> str:
    """Strip known prefixes from a key and return the remainder."""
    s = key.strip()
    for prefix in _STRIP_PREFIXES:
        if s.startswith(prefix):
            return s[len(prefix) :]
    return s


def _pretty_reg_name(key: str) -> str:
    """Make register keys human-friendly (English fallback labels)."""
    base = _strip_prefixes(key).lower().strip("_")

    direct = {
        "outdoor_temperature": "Outdoor temperature",
        "supply_temperature": "Supply air temperature",
        "extract_temperature": "Extract air temperature",
        "room_temperature": "Room temperature",
        "free_cooling_enable": "Free cooling active",
        "eco_mode_enable": "Eco mode active",
        "heat_recovery": "Heat recovery",
        "filter_alarm": "Filter alarm",
        "filter_warning_alarm": "Filter warning",
        "calculated_moisture_extraction": "Calculated moisture extraction",
        "calculated_moisture_intake": "Calculated moisture intake",

        # Duration / timers
        "refresh_mode_duration": "Refresh mode – duration",
        "fireplace_mode_duration": "Fireplace mode – duration",
        "holiday_mode_duration": "Holiday mode – duration",
        "away_mode_duration": "Away mode – duration",
        "crowded_mode_duration": "Crowded mode – duration",

        # Free cooling (night cooling)
        "free_cooling_active": "Free cooling active",
        "free_cooling_daytime_min_temp": "Free cooling – daytime min temp",
        "free_cooling_night_high_limit": "Free cooling – night high limit",
        "free_cooling_night_low_limit": "Free cooling – night low limit",
        "free_cooling_room_cancel_temp": "Free cooling – room cancel temp",
        "free_cooling_start_time_h": "Free cooling – start (hour)",
        "free_cooling_start_time_m": "Free cooling – start (minute)",
        "free_cooling_end_time_h": "Free cooling – end (hour)",
        "free_cooling_end_time_m": "Free cooling – end (minute)",
        "free_cooling_min_speed_saf": "Free cooling – min SAF speed",
        "free_cooling_min_speed_eaf": "Free cooling – min EAF speed",

        # Filters
        "filter_replacement_alarm": "Filter replacement alarm",
        "filter_replacement_period": "Filter replacement interval",
        "filter_warning_alarm": "Filter warning",
        "filter_warning_alarm_delay_count": "Filter warning – delay",

        # Speeds (common)
        "saf_speed_rpm": "SAF fan speed (RPM)",
        "eaf_speed_rpm": "EAF fan speed (RPM)",

        # Season / operation
        "summer_winter_operation_1_0": "Summer/winter operation",
    }
    if base in direct:
        return direct[base]

    parts = [p for p in base.split("_") if p]

    fan = None
    if parts and parts[0] in ("saf", "eaf"):
        fan = "Supply air fan" if parts[0] == "saf" else "Extract air fan"
        parts = parts[1:]

    rpm = "rpm" in parts
    parts = [p for p in parts if p != "rpm"]

    trans = {
        "speed": "speed",
        "temperature": "temperature",
        "high": "high",
        "low": "low",
        "enable": "enabled",
        "enabled": "enabled",
        "status": "status",
        "alarm": "alarm",
        "pressure": "pressure",
        "humidity": "humidity",
        "timer": "timer",
        "time": "time",
        "remaining": "remaining",
    }

    words = [trans.get(p, p) for p in parts]

    if fan:
        phrase = " ".join(words).strip()
        if rpm:
            phrase = (phrase + " (RPM)").strip()
        return f"{fan} – {phrase}" if phrase else fan

    phrase = " ".join(words).strip()
    if rpm:
        phrase = (phrase + " (RPM)").strip()
    return phrase[:1].upper() + phrase[1:] if phrase else base


def _suggested_object_id(key: str) -> str:
    """Generate a short, stable object_id (used for entity_id on first create)."""
    s = _strip_prefixes(key).lower()
    s = re.sub(r"[^a-z0-9_]+", "_", s).strip("_")
    if not s:
        s = "value"
    return f"save_{s}"


def _base_key(key: str) -> str:
    """Normalize a register key to its logical base (no device/model prefixes)."""
    return _strip_prefixes(key).lower().strip("_")


ENABLED_RAW_KEYS: set[str] = {
    # Temperatures
    "outdoor_temperature",
    "supply_temperature",
    "extract_temperature",
    "room_temperature",
    "supply_air_setpoint",
    # Fan speeds (RPM)
    "saf_speed_rpm",
    "eaf_speed_rpm",
    # Moisture (calculated)
    "calculated_moisture_extraction",
    "calculated_moisture_intake",
    "relative_moisture_extraction",
    # Heat recovery
    "heat_recovery",
}


# CD4 raw registers that have proper translated Home Assistant names in 1B.
CD4_TRANSLATED_SENSOR_KEYS: set[str] = {
    "saf_speed_low_rpm",
    "eaf_speed_low_rpm",
    "saf_speed_normal",
    "eaf_speed_normal",
    "saf_speed_high",
    "eaf_speed_high",
    "saf_speed_rpm",
    "eaf_speed_rpm",
    "saf_pwm",
    "eaf_pwm",
    "fan_speed_level_cd",
    "temperature_sensor_1",
    "temperature_sensor_2",
    "temperature_sensor_3",
    "temperature_sensor_4",
    "temperature_sensor_5",
    "temperature_sensor_state",
    "rotor_state",
    "defrost_state",
    "system_type",
    "filter_replacement_period",
    "filter_days",
    "manual_mode_command_register",
}


# These registers remain in Cd4Model.REGISTERS so the coordinator reads them,
# but they are represented by binary_sensor entities instead of duplicate
# numeric sensor entities.
CD4_BINARY_SENSOR_SOURCE_KEYS: set[str] = {
    "fan_manual_stop_allowed_register",
    "rotor_relay_active",
    "alarm_relay_active",
}

# CD4 temperature-control registers are read by the coordinator for the
# temperature control entity, but are not useful as separate raw sensors.
CD4_INTERNAL_SENSOR_KEYS: set[str] = {
    "temperature_level_command_register",
    "temperature_setpoint_level",
    "temperature_level_1",
    "temperature_level_2",
    "temperature_level_3",
    "temperature_level_4",
    "temperature_level_5",
    "pcu_pb_relays",
}


# Language-neutral enum state keys. Translation is handled by en/nb JSON.
CD4_ENUM_VALUE_MAPS: dict[str, dict[int, str]] = {
    "fan_speed_level_cd": {
        0: "stop",
        1: "low",
        2: "normal",
        3: "high",
    },
    "defrost_state": {
        0: "inactive",
        1: "reduced_flow",
        2: "bypass",
        3: "stop",
    },
}


DERIVED = [
    {"key": "mode_status_text", "icon": "mdi:fan"},
    {"key": "active_season", "icon": "mdi:weather-sunny-snowflake"},
    {"key": "next_filter_change", "icon": "mdi:air-filter"},
    {"key": "iaq_level_text", "icon": "mdi:air-filter"},
    {"key": "regulation_mode_text", "icon": "mdi:tune-vertical"},
    {"key": "exhaust_air_flow_rate", "icon": "mdi:weather-windy", "unit": "m³/h"},
    {"key": "supply_air_flow_rate", "icon": "mdi:weather-windy", "unit": "m³/h"},
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    model = coordinator.model
    is_cd4 = getattr(model, "model_id", None) == "legacy_cd4"

    entities: list[SensorEntity] = []

    # Raw register-backed sensors (from model.REGISTERS).
    for reg in model.REGISTERS:
        # CD4: do not create duplicate numeric sensors for values represented
        # as binary_sensor entities in phase 1B.
        if is_cd4 and _base_key(reg.key) in CD4_BINARY_SENSOR_SOURCE_KEYS:
            continue
        if is_cd4 and _base_key(reg.key) in CD4_INTERNAL_SENSOR_KEYS:
            continue

        entities.append(SystemairRegisterSensor(coordinator, entry, reg))

    if is_cd4:
        # CD4 phase 1B:
        # Do not expose SAVE-style "mode_status_text" as a separate Mode sensor.
        # REG_FAN_SPEED_LEVEL only represents Stop/Low/Normal/High, while
        # fan_speed_level_cd already exposes the actual active fan level.
        async_add_entities(entities)
        return

    # Derived sensors (SAVE-oriented)
    for d in DERIVED:
        entities.append(
            SystemairDerivedSensor(
                coordinator,
                entry,
                d["key"],
                d.get("icon"),
                d.get("unit"),
            )
        )

    entities.append(SystemairCalculatedExhaustTemperature(coordinator, entry))
    async_add_entities(entities)


class SystemairRegisterSensor(SystemairBaseEntity, SensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry, reg) -> None:
        super().__init__(entry, coordinator)
        self._key = reg.key
        self._base_key = _base_key(reg.key)
        self._is_cd4 = (
            getattr(self.coordinator.model, "model_id", None) == "legacy_cd4"
        )

        self._attr_unique_id = f"{entry.entry_id}_reg_{reg.key}"
        self._attr_suggested_object_id = _suggested_object_id(reg.key)

        translated_keys = set(ENABLED_RAW_KEYS)
        if self._is_cd4:
            translated_keys |= CD4_TRANSLATED_SENSOR_KEYS

        if self._base_key in translated_keys:
            self._attr_translation_key = self._base_key
        else:
            self._attr_name = _pretty_reg_name(reg.key)

        enabled_keys = getattr(
            self.coordinator.model,
            "DEFAULT_ENABLED_RAW_KEYS",
            ENABLED_RAW_KEYS,
        )

        if self._base_key not in enabled_keys:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_entity_registry_enabled_default = False

        if reg.unit:
            self._attr_native_unit_of_measurement = reg.unit
        if reg.device_class:
            self._attr_device_class = reg.device_class
        if reg.state_class:
            self._attr_state_class = reg.state_class

        enum_map = CD4_ENUM_VALUE_MAPS.get(self._base_key) if self._is_cd4 else None
        if enum_map is not None:
            self._enum_map = enum_map
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = list(enum_map.values()) + ["unknown"]
            # Enum sensors cannot have numeric measurement metadata.
            self._attr_native_unit_of_measurement = None
            self._attr_state_class = None
        else:
            self._enum_map = None

    @property
    def native_value(self):
        raw = self.coordinator.data.get(self._key)

        if self._enum_map is None:
            return raw

        try:
            value = int(float(raw))
        except (TypeError, ValueError):
            return "unknown"

        return self._enum_map.get(value, "unknown")


class SystemairDerivedSensor(SystemairBaseEntity, SensorEntity):
    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        key: str,
        icon: str | None,
        unit: str | None = None,
    ) -> None:
        super().__init__(entry, coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_derived_{key}"
        self._attr_suggested_object_id = _suggested_object_id(key)
        self._attr_translation_key = key
        if icon:
            self._attr_icon = icon
        if unit:
            self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)


class SystemairCalculatedExhaustTemperature(SystemairBaseEntity, SensorEntity):
    """Calculated exhaust/avkast air temperature (estimated).

    This is NOT a real Modbus value. It is estimated from:
      - outdoor_temperature
      - extract_temperature
      - heat_recovery (%)
    """

    _attr_translation_key = "calculated_exhaust_temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = None
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calculated_exhaust_temperature"
        self._attr_suggested_object_id = "save_calculated_exhaust_temperature"

    @property
    def native_value(self):
        data = self.coordinator.data

        try:
            outdoor = float(data.get("outdoor_temperature"))
            extract = float(data.get("extract_temperature"))
            recovery = float(data.get("heat_recovery"))

            value = extract - ((extract - outdoor) * (recovery / 100.0))
            return round(value, 1)
        except (TypeError, ValueError):
            return None
