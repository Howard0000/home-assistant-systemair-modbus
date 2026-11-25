from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class SystemairBaseEntity(CoordinatorEntity):
    """Base entity for Systemair Modbus."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, coordinator) -> None:
        super().__init__(coordinator)
        self._entry = entry

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Systemair",
            name=coordinator.model.device_model_name(
                (coordinator.data or {}).get("system_type")
            ),
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Expose the detected CD4 or SAVE system type as device model."""
        info = dict(self._attr_device_info)
        model = self.coordinator.model
        if getattr(model, "model_id", None) in ("legacy_cd4", "save"):
            data = self.coordinator.data or {}
            info["model"] = model.device_model_name(data.get("system_type"))
        return DeviceInfo(**info)
