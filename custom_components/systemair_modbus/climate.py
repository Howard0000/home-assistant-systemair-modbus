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

    async_add_entities([SystemairVTRClimate(entry, coordinator, client, model)])


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
