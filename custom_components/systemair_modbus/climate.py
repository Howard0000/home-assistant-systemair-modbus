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

    CD4 temperature model:
      - REG_HC_TEMP_LVL (PDF 207 / offset 206) is the R/W level command.
      - Level 0 is manual summer mode.
      - Levels 1..11 represent 12..22 °C in 1 °C steps.
      - REG_HC_TEMP_SP (PDF 208 / offset 207) is read back as the actual
        temperature setpoint in °C by the CD4 model.
    """

    _attr_translation_key = "cd4_climate"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
    )
    _attr_entity_category = EntityCategory.CONFIG
    # CD4 REG_HC_TEMP_LVL = 0 is the physical panel's temperature OFF /
    # Systemair "Manual summer mode". This is NOT the same as stopping the
    # ventilation fans. Fan stop remains separately capability-gated by
    # REG_FAN_ALLOW_MANUAL_FAN_STOP.
    _attr_hvac_modes = [HVACMode.FAN_ONLY, HVACMode.OFF]

    # Both maps below are verified on real VSR500/CD4 hardware:
    #   heater configured:     level 1..11 = 12..22 °C
    #   no heater configured:  level 1..5  = 15..19 °C
    # REG_HC_HEATER_TYPE is used as the profile selector. If it is unavailable,
    # use the heater-capable 12..22 °C profile as a conservative fallback.
    _attr_target_temperature_step = 1.0

    def __init__(self, entry: ConfigEntry, coordinator, client, model) -> None:
        super().__init__(entry, coordinator)
        self._client = client
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_cd4_climate"

        # Keep the last valid target available while REG_HC_TEMP_LVL is 0
        # (Manual summer / temperature regulation off), so Home Assistant can
        # return directly to a valid setpoint for the active CD4 profile.
        self._last_target_temperature = 20.0

        # Fan-mode OFF is separate from temperature OFF and is only exposed
        # when the controller explicitly allows manual fan stop.
        self._attr_fan_modes = ["low", "medium", "high"]
        if self._stop_allowed():
            self._attr_fan_modes.append("off")

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

    def _heater_configured(self) -> bool:
        """Return True when CD4 reports a configured heater.

        REG_HC_HEATER_TYPE:
          0 = no heater
          1 = water heater
          2 = electrical heater
          3 = other

        If the value is unavailable, assume the heater-capable 12..22 °C
        profile as a conservative fallback.
        """
        raw = self._get_int("heater_type")
        if raw is None:
            return True
        return raw != 0

    @property
    def min_temp(self) -> float:
        return 12.0 if self._heater_configured() else 15.0

    @property
    def max_temp(self) -> float:
        return 22.0 if self._heater_configured() else 19.0

    def _temperature_to_level(self, temperature: float) -> int | None:
        """Map a user temperature to REG_HC_TEMP_LVL."""
        rounded = round(temperature)
        if abs(temperature - rounded) > 0.01:
            return None

        value = int(rounded)
        if self._heater_configured():
            if 12 <= value <= 22:
                return value - 11
            return None

        if 15 <= value <= 19:
            return value - 14
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        # Temperature command 0 is Systemair Manual summer / panel "OFF".
        # The ventilation fan may still be running; this only reports the
        # state of the temperature-regulation part of this Climate entity.
        temperature_level = self._get_int("temperature_level_command_register")
        if temperature_level == 0:
            return HVACMode.OFF
        return HVACMode.FAN_ONLY

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            # Temperature regulation OFF / Manual summer mode.
            # Deliberately do NOT touch the manual fan-speed register here.
            await self._client.write_register(
                self._model.ADDR_TEMPERATURE_LEVEL_COMMAND,
                0,
            )
        elif hvac_mode == HVACMode.FAN_ONLY:
            # Leaving Manual summer mode requires a valid 1..11 temperature
            # command. Restore the last valid target known by this entity.
            target = min(
                max(float(self._last_target_temperature), self.min_temp),
                self.max_temp,
            )
            level = self._temperature_to_level(target)
            if level is None:
                return
            self._last_target_temperature = float(round(target))
            await self._client.write_register(
                self._model.ADDR_TEMPERATURE_LEVEL_COMMAND,
                level,
            )
        else:
            return

        await self.coordinator.async_request_refresh()

    @property
    def hvac_action(self) -> HVACAction:
        """Report the temperature-regulation activity of the CD4 climate."""
        # REG_HC_TEMP_LVL = 0 means the temperature function itself is off,
        # even though the ventilation fans can continue to run.
        temperature_level = self._get_int("temperature_level_command_register")
        if temperature_level == 0:
            return HVACAction.OFF

        relays = self._get_int("pcu_pb_relays")
        if relays is not None and (relays & (1 << 1)):
            return HVACAction.HEATING

        # Temperature regulation is enabled, but no reheating is currently
        # requested. Airflow may of course continue.
        return HVACAction.FAN

    @property
    def current_temperature(self) -> float | None:
        # TEMP_IN1 = SS = supply-air temperature, documented by Systemair.
        return self._get_float("temperature_sensor_1")

    @property
    def target_temperature(self) -> float | None:
        level = self._get_int("temperature_level_command_register")
        setpoint = self._get_float("temperature_setpoint")

        # When temperature regulation is active, remember the valid target
        # reported by the controller.
        if (
            level is not None
            and 1 <= level <= (11 if self._heater_configured() else 5)
            and setpoint is not None
            and self.min_temp <= setpoint <= self.max_temp
        ):
            self._last_target_temperature = setpoint
            return setpoint

        # REG_HC_TEMP_LVL = 0 is CD4 manual summer mode. The controller then
        # reports REG_HC_TEMP_SP = 0, but returning None here makes Home
        # Assistant hide the temperature control. Keep showing the last valid
        # target instead, so selecting a valid temperature can leave manual summer mode.
        if level == 0:
            return self._last_target_temperature

        # During startup/temporary communication gaps, keep the last known
        # target rather than removing the temperature control from the UI.
        return self._last_target_temperature

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

        selected_level = self._temperature_to_level(requested)
        if selected_level is None:
            return

        rounded = round(requested)
        self._last_target_temperature = float(rounded)

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
