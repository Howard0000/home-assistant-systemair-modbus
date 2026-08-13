"""Climate platform for Systemair Modbus (SAVE)."""
from __future__ import annotations

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode, HVACAction
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import SystemairBaseEntity


# Climate preset labels are not auto-translated by HA.
# Use English labels here to avoid Norwegian text in English UI.
PRESET_TO_COMMAND_MODE = {
    "Auto": 1,
    "Manual": 2,
    "Party": 3,
    "Boost": 4,
    "Fireplace": 5,
    "Away": 6,
    "Holiday": 7,
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    model = coordinator.model

    if getattr(model, "model_id", None) == "legacy_cd4":
        async_add_entities([SystemairCd4Climate(entry, coordinator, client, model)])
        return

    async_add_entities([SystemairVTRClimate(entry, coordinator, client, model)])


class SystemairCd4Climate(SystemairBaseEntity, ClimateEntity):
    """CD4 supply-air temperature control.

    Systemair documents five discrete supply-air temperature levels.
    The actual level temperatures are read from the controller, so the same
    entity works for units with an active re-heater and units without one.
    """

    _attr_translation_key = "cd4_climate"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
    )
    _attr_entity_category = EntityCategory.CONFIG
    _attr_hvac_modes = [HVACMode.FAN_ONLY]

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_cd4_climate"

        # Only expose "Off" when the CD4 controller explicitly allows
        # manual fan stop.
        self._attr_fan_modes = ["low", "medium", "high"]
        if self._stop_allowed():
            self._attr_fan_modes.append("off")

        self._update_temperature_limits()

    def _get_float(self, key: str) -> float | None:
        raw = self.coordinator.data.get(key)
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    def _get_int(self, key: str) -> int | None:
        raw = self.coordinator.data.get(key)
        if raw is None:
            return None
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return None

    def _stop_allowed(self) -> bool:
        raw = self.coordinator.data.get("fan_manual_stop_allowed_register")
        try:
            return int(float(raw)) == 1
        except (TypeError, ValueError):
            return False

    def _temperature_levels(self) -> dict[int, float]:
        levels: dict[int, float] = {}
        for level in range(1, 6):
            value = self._get_float(f"temperature_level_{level}")
            if value is not None:
                levels[level] = value
        return levels

    def _update_temperature_limits(self) -> None:
        levels = self._temperature_levels()
        if not levels:
            # Documented re-heater defaults; only used before first valid poll.
            self._attr_min_temp = 12.0
            self._attr_max_temp = 22.0
            self._attr_target_temperature_step = 2.5
            return

        ordered = [levels[level] for level in sorted(levels)]
        self._attr_min_temp = min(ordered)
        self._attr_max_temp = max(ordered)

        diffs = [
            round(ordered[i + 1] - ordered[i], 3)
            for i in range(len(ordered) - 1)
        ]
        if diffs and all(abs(diff - diffs[0]) < 0.001 for diff in diffs):
            self._attr_target_temperature_step = diffs[0]
        else:
            # The write method still validates against the exact five values.
            self._attr_target_temperature_step = 0.5

    @property
    def hvac_mode(self) -> HVACMode:
        # CD4 temperature regulation is constant supply-air control.
        # Fan speed is intentionally handled by the separate fan entity.
        return HVACMode.FAN_ONLY

    @property
    def hvac_action(self) -> HVACAction:
        """Report actual CD4 heating activity from the power-board relay."""
        relays = self._get_int("pcu_pb_relays")
        if relays is not None and (relays & (1 << 1)):
            return HVACAction.HEATING

        fan_level = self._get_int("manual_mode_command_register")
        if fan_level == 0:
            return HVACAction.OFF

        return HVACAction.FAN

    @property
    def current_temperature(self) -> float | None:
        # TEMP_IN1 = SS = supply-air temperature, documented by Systemair.
        return self._get_float("temperature_sensor_1")

    @property
    def target_temperature(self) -> float | None:
        self._update_temperature_limits()

        active_level = self._get_int("temperature_setpoint_level")
        if active_level is None or active_level == 0:
            # Level 0 is Manual Summer mode and has no temperature target.
            return None

        return self._temperature_levels().get(active_level)

    @property
    def fan_mode(self) -> str | None:
        raw = self.coordinator.data.get("manual_mode_command_register")
        try:
            level = int(float(raw))
        except (TypeError, ValueError):
            return None

        return {
            0: "off",
            1: "low",
            2: "medium",
            3: "high",
        }.get(level)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        level = {
            "off": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
        }.get(fan_mode)

        if level is None:
            return

        # Never translate an unsupported OFF request into another speed.
        # If this CD4 unit does not support manual stop, "off" is not exposed
        # in fan_modes and an unexpected external request is simply ignored.
        if level == 0 and not self._stop_allowed():
            return

        await self._client.write_register(
            self._model.ADDR_MANUAL_SPEED_COMMAND,
            level,
        )
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs) -> None:
        value = kwargs.get("temperature")
        if value is None:
            return

        try:
            requested = float(value)
        except (TypeError, ValueError):
            return

        levels = self._temperature_levels()
        if not levels:
            return

        # Climate UI should already offer the correct step, but never send an
        # unsupported value to the CD4 controller. Pick only an exact level.
        selected_level = None
        for level, temperature in levels.items():
            if abs(requested - temperature) < 0.01:
                selected_level = level
                break

        if selected_level is None:
            return

        await self._client.write_register(
            self._model.ADDR_TEMPERATURE_LEVEL_COMMAND,
            selected_level,
        )
        await self.coordinator.async_request_refresh()


class SystemairVTRClimate(SystemairBaseEntity, ClimateEntity):
    """Main control entity (setpoint + mode)."""

    _attr_translation_key = "climate"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model

        self._attr_unique_id = f"{entry.entry_id}_climate"

        self._attr_min_temp = 10.0
        self._attr_max_temp = 30.0
        self._attr_target_temperature_step = 0.5

        self._attr_preset_modes = list(PRESET_TO_COMMAND_MODE.keys())
        self._attr_hvac_modes = [HVACMode.AUTO, HVACMode.FAN_ONLY]
        if self._stop_allowed():
            self._attr_hvac_modes.append(HVACMode.OFF)

    def _get_int(self, key: str, default: int = 0) -> int:
        raw = self.coordinator.data.get(key)
        try:
            return int(float(raw if raw is not None else default))
        except (TypeError, ValueError):
            return default

    def _get_float(self, key: str, default: float | None = None) -> float | None:
        raw = self.coordinator.data.get(key)
        if raw is None:
            return default
        try:
            return float(raw)
        except (TypeError, ValueError):
            return default

    def _stop_allowed(self) -> bool:
        # key from old unique_id: save_fan_manual_stop_allowed_reg
        # Internal key becomes fan_manual_stop_allowed_reg
        allowed = self._get_int("fan_manual_stop_allowed_reg", 1)
        return allowed == 1

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation."""
        # Check the triac register for heating activity
        triac_val = self._get_int("triac_after_manual_override", 0)
        if triac_val > 0:
            return HVACAction.HEATING
        
        # If not heating, check if it's off or just circulating air
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        return HVACAction.FAN

    @property
    def hvac_mode(self) -> HVACMode:
        man = self._get_int("manual_mode_command_register", 3)
        if man == 0 and self._stop_allowed():
            return HVACMode.OFF

        mode = self._get_int("mode_status_register", 0)
        if mode == 0:
            return HVACMode.AUTO
        return HVACMode.FAN_ONLY

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            if not self._stop_allowed():
                return
            await self._client.write_register(self._model.ADDR_MANUAL_SPEED_COMMAND, 0)
        elif hvac_mode == HVACMode.AUTO:
            await self._client.write_register(self._model.ADDR_MODE_COMMAND, PRESET_TO_COMMAND_MODE["Auto"])
        elif hvac_mode == HVACMode.FAN_ONLY:
            # Keep current mode, but ensure manual speed not 0
            man = self._get_int("manual_mode_command_register", 3)
            if man == 0:
                await self._client.write_register(self._model.ADDR_MANUAL_SPEED_COMMAND, 3)

        await self.coordinator.async_request_refresh()

    @property
    def preset_mode(self) -> str | None:
        mode = self._get_int("mode_status_register", 0)
        return self._model.STATUS_MODE_TO_LABEL.get(mode)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode not in PRESET_TO_COMMAND_MODE:
            return
        await self._client.write_register(self._model.ADDR_MODE_COMMAND, PRESET_TO_COMMAND_MODE[preset_mode])
        await self.coordinator.async_request_refresh()

    @property
    def target_temperature(self) -> float:
        return float(self.coordinator.data.get("supply_air_setpoint") or 20.0)

    @property
    def current_temperature(self) -> float:
        supply = self._get_float("supply_temperature", None)
        if supply is not None:
            return supply
        exhaust = self._get_float("exhaust_temperature", 20.0)
        return exhaust if exhaust is not None else 20.0

    async def async_set_temperature(self, **kwargs) -> None:
        if (val := kwargs.get("temperature")) is None:
            return
        await self._client.write_0_1c(self._model.ADDR_SUPPLY_AIR_SETPOINT_0_1C, float(val))
        await self.coordinator.async_request_refresh()
