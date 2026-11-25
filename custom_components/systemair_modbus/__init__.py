"""Systemair Modbus integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import logging

_LOGGER = logging.getLogger(__name__)

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_HOST,
    CONF_PORT,
    CONF_SLAVE,
    CONF_SCAN_INTERVAL,
    CONF_MODEL,
    CONF_UNIT_MODEL,
    # NEW:
    CONF_GATEWAY_PROFILE,
    DEFAULT_GATEWAY_PROFILE,
    DEFAULT_SLAVE,
    DEFAULT_SCAN_INTERVAL,
    UNIT_MODEL_QV_MAX,
)
from .coordinator import SystemairCoordinator
from .modbus import ModbusTcpClient
from .models import MODEL_REGISTRY

# Platforms supported by the legacy CD4 model.
PLATFORMS_LEGACY_CD4 = ["sensor", "select", "binary_sensor", "fan", "climate"]


def _update_detected_device_name(hass: HomeAssistant, entry: ConfigEntry, coordinator) -> None:
    """Update auto-managed device names when model data becomes available."""
    from homeassistant.helpers import device_registry as dr

    model_text = (coordinator.data or {}).get("system_type")
    if not model_text:
        return
    registry = dr.async_get(hass)
    # Supported entry-scoped registry lookup. Do not access registry.devices
    # or the deprecated DeviceEntry.config_entries property.
    device = next(
        (candidate for candidate in dr.async_entries_for_config_entry(registry, entry.entry_id)
         if (DOMAIN, entry.entry_id) in candidate.identifiers),
        None,
    )
    if device is None or device.name_by_user:
        return
    old_names = {"Systemair SAVE", "Systemair SAVE AUX-2", "Systemair SAVE AUX-2 (read-only test)", "Systemair CD4 AUX-2", "Systemair CD4 (legacy)"}
    if device.name not in old_names and not (device.name or "").startswith("Systemair "):
        return
    desired = coordinator.model.device_model_name(model_text)
    if desired != device.name:
        registry.async_update_device(device.id, name=desired)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if entry.data.get("connection_type") == "aux2":
        from .serial_transport import SerialModbusTransport
        from .serial_coordinator import SerialModbusCoordinator
        # Existing AUX-2 entries without a model key remain SAVE by default.
        model_id = entry.data.get(CONF_MODEL, "save")
        if model_id not in ("save", "legacy_cd4"):
            raise ValueError(f"Unsupported AUX-2 model: {model_id!r}")
        model = MODEL_REGISTRY[model_id]()
        client = SerialModbusTransport(hass, entry)
        coordinator = SerialModbusCoordinator(
            hass, client, model,
            scan_interval_s=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        coordinator._airflow_override = entry.options.get(CONF_UNIT_MODEL)
        # Preserve the existing entry and entity unique IDs.
        await coordinator.async_config_entry_first_refresh()
        platforms = PLATFORMS_LEGACY_CD4 if model_id == "legacy_cd4" else list(PLATFORMS)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
            "client": client, "coordinator": coordinator, "platforms": platforms,
            "transport": "aux2",
        }
        await hass.config_entries.async_forward_entry_setups(entry, platforms)
        _update_detected_device_name(hass, entry, coordinator)
        entry.async_on_unload(coordinator.async_add_listener(
            lambda: _update_detected_device_name(hass, entry, coordinator)
        ))
        return True

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    model_id = entry.data[CONF_MODEL]
    # New installations detect model automatically. Existing explicit selections
    # are retained as an override until changed in Options.
    unit_model = entry.options.get(CONF_UNIT_MODEL, entry.data.get(CONF_UNIT_MODEL))

    # Options override (tannhjul)
    slave = entry.options.get(CONF_SLAVE, entry.data.get(CONF_SLAVE, DEFAULT_SLAVE))
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    gateway_profile = entry.options.get(
        CONF_GATEWAY_PROFILE,
        entry.data.get(CONF_GATEWAY_PROFILE, DEFAULT_GATEWAY_PROFILE),
    )

    qv_max = UNIT_MODEL_QV_MAX.get(unit_model) if unit_model else None

    model_cls = MODEL_REGISTRY[model_id]
    model = model_cls(qv_max=qv_max)

    client = ModbusTcpClient(
        host=host,
        port=port,
        slave=int(slave),
        gateway_profile=gateway_profile,  # NEW
    )
    coordinator = SystemairCoordinator(
        hass,
        name=entry.title,
        client=client,
        model=model,
        scan_interval_s=int(scan_interval),
    )

    coordinator._airflow_override = unit_model if unit_model in UNIT_MODEL_QV_MAX and UNIT_MODEL_QV_MAX[unit_model] is not None else None
    await coordinator.async_config_entry_first_refresh()

    # Velg plattformer basert på modell
    platforms = PLATFORMS_LEGACY_CD4 if model_id == "legacy_cd4" else list(PLATFORMS)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "platforms": platforms,
    }

    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    _update_detected_device_name(hass, entry, coordinator)
    entry.async_on_unload(coordinator.async_add_listener(
        lambda: _update_detected_device_name(hass, entry, coordinator)
    ))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    platforms = data.get("platforms", PLATFORMS)

    _LOGGER.debug("Unloading Systemair entry %s; platforms=%s", entry.entry_id, platforms)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)
    if not unload_ok:
        _LOGGER.error(
            "Systemair entry %s: platform unload returned False for %s; "
            "Home Assistant may require a restart. See preceding platform errors.",
            entry.entry_id, platforms,
        )

    if unload_ok:
        await entry.async_unload(hass)
        data = hass.data[DOMAIN].pop(entry.entry_id, {})
        client: ModbusTcpClient | None = data.get("client")
        if client and entry.data.get("connection_type") != "aux2":
            await client.async_close()
        _LOGGER.debug("Systemair entry %s unloaded successfully", entry.entry_id)

    return unload_ok