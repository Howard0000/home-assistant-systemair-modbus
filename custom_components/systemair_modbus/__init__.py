"""Systemair Modbus integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    model_id = entry.data[CONF_MODEL]
    unit_model = entry.data.get(CONF_UNIT_MODEL)

    # Options override (tannhjul)
    slave = entry.options.get(CONF_SLAVE, entry.data.get(CONF_SLAVE, DEFAULT_SLAVE))
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

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

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, {})
        client: ModbusTcpClient | None = data.get("client")
        if client:
            await client.async_close()

    return unload_ok
