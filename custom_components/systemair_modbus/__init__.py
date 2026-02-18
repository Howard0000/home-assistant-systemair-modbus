from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import SystemairCoordinator
from .modbus import ModbusTcpClient
from .models import MODEL_REGISTRY
from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SLAVE,
    CONF_SCAN_INTERVAL,
    CONF_MODEL,
    CONF_UNIT_MODEL,
    DEFAULT_SCAN_INTERVAL,
    UNIT_MODEL_QV_MAX,
)

PLATFORMS_LEGACY_CD4 = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    slave = entry.data[CONF_SLAVE]
    model_id = entry.data[CONF_MODEL]
    unit_model = entry.data.get(CONF_UNIT_MODEL)
    qv_max = UNIT_MODEL_QV_MAX.get(unit_model) if unit_model else None

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

    model_cls = MODEL_REGISTRY[model_id]
    model = model_cls(qv_max=qv_max)

    client = ModbusTcpClient(host=host, port=port, slave=slave)
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
        # lagre hvilke plattformer vi faktisk lastet (brukes ved unload)
        "platforms": PLATFORMS_LEGACY_CD4 if model_id == "legacy_cd4" else list(PLATFORMS),
    }

    platforms = hass.data[DOMAIN][entry.entry_id]["platforms"]
    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Bruk samme plattformer som ble lastet
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    platforms = data.get("platforms", PLATFORMS)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms)

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, {})
        client: ModbusTcpClient | None = data.get("client")
        if client:
            await client.async_close()

    return unload_ok
