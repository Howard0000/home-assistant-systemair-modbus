"""Sensor platform for Systemair Modbus."""
from __future__ import annotations

import re

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
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

    # Direct mappings for the most-used/most-visible values
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

    # Fan-friendly formatting
    if fan:
        phrase = " ".join(words).strip()
        if rpm:
            phrase = (phrase + " (RPM)").strip()
        return f"{fan} – {phrase}" if phrase else fan

    # Generic fallback
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
    # Always prefix with save_ for a consistent namespace in entity_id
    return f"save_{s}"


def _base_key(key: str) -> str:
    """Normalize a register key to its logical base (no device/model prefixes)."""
    return _strip_prefixes(key).lower().strip("_")


# Raw register sensors: keep only the most useful enabled by default.
# Everything else is still available, but hidden by default to reduce noise in the UI.

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

DERIVED = [
    {"key": "mode_status_text", "icon": "mdi:fan"},
    {"key": "active_season", "icon": "mdi:weather-sunny-snowflake"},
    {"key": "next_filter_change", "icon": "mdi:air-filter"},
    {"key": "iaq_level_text", "icon": "mdi:air-filter"},
    {"key": "regulation_mode_text", "icon": "mdi:tune-vertical"},
    {"key": "exhaust_air_flow_rate", "icon": "mdi:weather-windy", "unit": "m³/h"},
    {"key": "supply_air_flow_rate", "icon": "mdi:weather-windy", "unit": "m³/h"},
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    model = coordinator.model

    entities: list[SensorEntity] = []

    # Raw register-backed sensors (1:1 from the known working register map)
    for reg in model.REGISTERS:
        entities.append(SystemairRegisterSensor(coordinator, entry, reg))

    # Derived sensors
    for d in DERIVED:
        entities.append(SystemairDerivedSensor(coordinator, entry, d["key"], d.get("icon"), d.get("unit")))

    # Calculated (estimated) exhaust/avkast temperature (NOT a real Modbus sensor)
    entities.append(SystemairCalculatedExhaustTemperature(coordinator, entry))

    async_add_entities(entities)


class SystemairRegisterSensor(SystemairBaseEntity, SensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry, reg) -> None:
        super().__init__(entry, coordinator)
        self._key = reg.key

        # Deterministic unique_id (OK that history breaks right now)
        self._attr_unique_id = f"{entry.entry_id}_reg_{reg.key}"
        self._attr_suggested_object_id = _suggested_object_id(reg.key)

        base_key = _base_key(reg.key)
        if base_key in ENABLED_RAW_KEYS:
            self._attr_translation_key = base_key
        else:
            self._attr_name = _pretty_reg_name(reg.key)

        # Hide most raw registers by default (they are still available in the entity registry).
        if base_key not in ENABLED_RAW_KEYS:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_entity_registry_enabled_default = False

        if reg.unit:
            self._attr_native_unit_of_measurement = reg.unit
        if reg.device_class:
            self._attr_device_class = reg.device_class
        if reg.state_class:
            self._attr_state_class = reg.state_class

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)


class SystemairDerivedSensor(SystemairBaseEntity, SensorEntity):
    def __init__(self, coordinator, entry: ConfigEntry, key: str, icon: str | None, unit: str | None = None) -> None:
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
        self._attr_suggested_object_id = _suggested_object_id("calculated_exhaust_temperature")

    @property
    def native_value(self):
        t_out = self.coordinator.data.get("outdoor_temperature")
        t_ext = self.coordinator.data.get("extract_temperature")
        hr_pct = self.coordinator.data.get("heat_recovery")  # 0..100 (pådrag/aktivitet)

        try:
            if t_out is None or t_ext is None or hr_pct is None:
                return None

            t_out = float(t_out)
            t_ext = float(t_ext)

            # Skaler "pådrag" til estimert reell virkningsgrad (maks 82 %)
            eta = 0.82 * (float(hr_pct) / 100.0)

            # clamp 0..0.82
            eta = max(0.0, min(0.82, eta))

            # T_exhaust ≈ T_extract - eta * (T_extract - T_outdoor)
            t_exhaust = t_ext - eta * (t_ext - t_out)
            return round(t_exhaust, 1)

        except (TypeError, ValueError):
            return None