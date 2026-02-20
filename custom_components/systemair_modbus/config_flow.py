"""Config flow for Systemair Modbus."""
from __future__ import annotations

import logging

import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_SLAVE,
    CONF_SCAN_INTERVAL,
    CONF_MODEL,
    CONF_UNIT_MODEL,
    DEFAULT_PORT,
    DEFAULT_SLAVE,
    DEFAULT_SCAN_INTERVAL,
    SUPPORTED_MODELS,
    UNIT_MODEL_QV_MAX,
)
from .modbus import ModbusTcpClient
from .models import MODEL_REGISTRY

_LOGGER = logging.getLogger(__name__)


async def _async_validate_connection(*, host: str, port: int, slave: int, model_id: str) -> None:
    """Validate that we can reach the device and read at least one register."""
    model_cls = MODEL_REGISTRY[model_id]
    # Use a single, stable holding register to keep config flow fast.
    test_reg = model_cls.REGISTERS[0].__dict__

    client = ModbusTcpClient(host=host, port=port, slave=slave)
    try:
        async with async_timeout.timeout(10):
            result = await client.read_register_map([test_reg])
        # Some gateways can respond but still return empty/invalid data;
        # treat that as a failed connect for UX.
        if not result:
            raise ConnectionError("Empty modbus response")
    finally:
        await client.async_close()


class SystemairModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            model_id = user_input[CONF_MODEL]
            host = str(user_input[CONF_HOST]).strip()
            port = int(user_input[CONF_PORT])
            slave = int(user_input[CONF_SLAVE])
            scan_interval = int(user_input[CONF_SCAN_INTERVAL])
            unit_model = user_input[CONF_UNIT_MODEL]

            # Unique ID to avoid duplicates
            await self.async_set_unique_id(f"{model_id}:{host.lower()}:{port}:{slave}")
            self._abort_if_unique_id_configured()

            try:
                await _async_validate_connection(host=host, port=port, slave=slave, model_id=model_id)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Cannot connect to Systemair Modbus device: %s", err, exc_info=True)
                errors["base"] = "cannot_connect"
            else:
                model_name = MODEL_REGISTRY[model_id].model_name
                return self.async_create_entry(
                    title=model_name,
                    data={
                        CONF_MODEL: model_id,
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_SLAVE: slave,
                        CONF_SCAN_INTERVAL: scan_interval,
                        CONF_UNIT_MODEL: unit_model,
                    },
                )

        model_options = {mid: MODEL_REGISTRY[mid].model_name for mid in SUPPORTED_MODELS}

        schema = vol.Schema(
            {
                vol.Required(CONF_MODEL, default=SUPPORTED_MODELS[0]): vol.In(model_options),
                vol.Required(CONF_UNIT_MODEL, default="Generic (legacy x3)"): vol.In(list(UNIT_MODEL_QV_MAX.keys())),
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
                vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): vol.Coerce(int),
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.Coerce(int),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        # IMPORTANT: pass config_entry so OptionsFlow can read both data + options safely
        return SystemairOptionsFlow(config_entry)


class SystemairOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_scan = self._config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        current_slave = self._config_entry.options.get(
            CONF_SLAVE,
            self._config_entry.data.get(CONF_SLAVE, DEFAULT_SLAVE),
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current_scan): vol.Coerce(int),
                vol.Required(CONF_SLAVE, default=current_slave): vol.All(
                    vol.Coerce(int),
                    vol.In([1, 2]),
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
