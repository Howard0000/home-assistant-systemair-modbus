"""Config flow for Systemair Modbus."""
from __future__ import annotations

import logging
import asyncio

import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from .entity_id_migration import restore_legacy_save_ids
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SerialPortSelector, NumberSelector, NumberSelectorConfig, NumberSelectorMode
from homeassistant.components.modbus import async_get_temporary_unit
from modbus_connection import ModbusSerialParams

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_SLAVE,
    CONF_SCAN_INTERVAL,
    CONF_MODEL,
    CONF_UNIT_MODEL,
    CONF_GATEWAY_PROFILE,
    GATEWAY_PROFILE_GENERIC,
    GATEWAY_PROFILE_SAVE_CONNECT,
    DEFAULT_GATEWAY_PROFILE,
    DEFAULT_PORT,
    DEFAULT_SLAVE,
    DEFAULT_SCAN_INTERVAL,
    SUPPORTED_MODELS,
    UNIT_MODEL_QV_MAX,
)
from .modbus import ModbusTcpClient
from .models import MODEL_REGISTRY

_LOGGER = logging.getLogger(__name__)


async def _tcp_probe(host: str, port: int, timeout_s: float = 3.0) -> None:
    """Fast TCP reachability check (network/VLAN/firewall vs Modbus issues)."""
    _LOGGER.debug("TCP probe start: %s:%s (timeout=%ss)", host, port, timeout_s)
    conn = asyncio.open_connection(host, port)
    reader, writer = await asyncio.wait_for(conn, timeout=timeout_s)
    writer.close()
    await writer.wait_closed()
    _LOGGER.debug("TCP probe OK: %s:%s", host, port)


async def _async_validate_connection(
    *,
    host: str,
    port: int,
    slave: int,
    model_id: str,
    gateway_profile: str,
) -> None:
    """Validate that we can reach the device and read at least one register."""
    model_cls = MODEL_REGISTRY[model_id]
    # Use a single, stable holding register to keep config flow fast.
    test_reg = model_cls.REGISTERS[0].__dict__

    client = ModbusTcpClient(host=host, port=port, slave=slave, gateway_profile=gateway_profile)

    # Use a short validation timeout, but allow more room for SAVE Connect safe mode
    timeout_s = 10
    if gateway_profile == GATEWAY_PROFILE_SAVE_CONNECT:
        timeout_s = 25

    try:
        async with async_timeout.timeout(timeout_s):
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
        return await self.async_step_connection(user_input)

    async def async_step_connection(self, user_input=None) -> FlowResult:
        """Choose transport without changing existing TCP setup."""
        if user_input is not None:
            if user_input["connection_type"] == "tcp":
                return await self.async_step_tcp()
            return await self.async_step_aux2()

        return self.async_show_form(
            step_id="connection",
            data_schema=vol.Schema({
                vol.Required("connection_type", default="tcp"): vol.In({"tcp": "Modbus TCP/IP (nettverk)", "aux2": "Modbus RTU (seriell)"}),
            }),
        )

    async def async_step_aux2(self, user_input=None) -> FlowResult:
        """Collect serial Modbus settings and validate before creating an entry."""
        if user_input is not None:
            settings = dict(user_input)
            settings[CONF_SLAVE] = int(settings[CONF_SLAVE])
            try:
                await self._validate_serial_settings(settings)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Modbus RTU setup validation failed: %s: %s", type(err).__name__, err)
                return self.async_show_form(
                    step_id="aux2", data_schema=self._serial_schema(),
                    errors={"base": "cannot_connect"},
                )
            await self.async_set_unique_id(
                f"aux2:{settings['serial_device']}:{int(settings['slave'])}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="Modbus RTU (seriell)",
                data={"connection_type": "aux2", **settings},
            )

        return self.async_show_form(step_id="aux2", data_schema=self._serial_schema())

    @staticmethod
    def _serial_schema():
        return vol.Schema({
            vol.Required(CONF_MODEL, default="save"): vol.In({
                "save": "Systemair SAVE",
                "legacy_cd4": "Systemair CD4 (legacy)",
            }),
            vol.Required("serial_device"): SerialPortSelector(),
            vol.Required("baudrate", default=115200): vol.In([1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]),
            vol.Required("parity", default="E"): vol.In({"N": "None", "E": "Even", "O": "Odd"}),
            vol.Required("stopbits", default=1): vol.In([1, 2]),
            vol.Required("slave", default=1): NumberSelector(NumberSelectorConfig(min=1, max=247, step=1, mode=NumberSelectorMode.BOX)),
        })

    async def _validate_serial_settings(self, settings) -> None:
        """Verify a model-specific holding register before creating an RTU entry."""
        params = ModbusSerialParams(
            device=settings["serial_device"],
            baudrate=int(settings["baudrate"]),
            parity=settings["parity"],
            stopbits=int(settings["stopbits"]),
            bytesize=8, framer="rtu",
        )
        probe_address = 8020 if settings[CONF_MODEL] == "save" else 500
        _LOGGER.debug("Modbus RTU setup probe: model=%s FC03 address=%s", settings[CONF_MODEL], probe_address)
        async with async_timeout.timeout(8):
            async with async_get_temporary_unit(
                self.hass, params, int(settings["slave"])
            ) as unit:
                result = await unit.read_holding_registers(probe_address, 1)
        if not isinstance(result, (list, tuple)) or len(result) != 1:
            raise ValueError(f"Unexpected response: {result!r}")

    async def async_step_tcp(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            model_id = user_input[CONF_MODEL]
            host = str(user_input[CONF_HOST]).strip()
            port = int(user_input[CONF_PORT])
            slave = int(user_input[CONF_SLAVE])
            scan_interval = int(user_input[CONF_SCAN_INTERVAL])
            unit_model = None
            gateway_profile = user_input[CONF_GATEWAY_PROFILE]

            # Unique ID to avoid duplicates
            await self.async_set_unique_id(f"{model_id}:{host.lower()}:{port}:{slave}")
            self._abort_if_unique_id_configured()

            try:
                # First: is TCP even reachable from HA?
                await _tcp_probe(host, port, timeout_s=3.0)

                # Then: can we do at least one Modbus read using the selected profile?
                await _async_validate_connection(
                    host=host,
                    port=port,
                    slave=slave,
                    model_id=model_id,
                    gateway_profile=gateway_profile,
                )
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Cannot connect to Systemair Modbus device: %s", err, exc_info=True)
                errors["base"] = "cannot_connect"
            else:
                model_name = MODEL_REGISTRY[model_id].model_name
                return self.async_create_entry(
                    title="Modbus TCP/IP",
                    data={
                        CONF_MODEL: model_id,
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_SLAVE: slave,
                        CONF_SCAN_INTERVAL: scan_interval,
                        CONF_UNIT_MODEL: unit_model,
                    },
                    # Store profile in options so it can be changed without re-adding the integration
                    options={
                        CONF_GATEWAY_PROFILE: gateway_profile,
                    },
                )

        model_options = {mid: MODEL_REGISTRY[mid].model_name for mid in SUPPORTED_MODELS}

        gateway_profile_options = {GATEWAY_PROFILE_GENERIC: "Standard kommunikasjon", GATEWAY_PROFILE_SAVE_CONNECT: "Forsiktig kommunikasjon (begrenset belastning)"}

        schema = vol.Schema(
            {
                vol.Required(CONF_MODEL, default=SUPPORTED_MODELS[0]): vol.In(model_options),
                vol.Required(CONF_GATEWAY_PROFILE, default=DEFAULT_GATEWAY_PROFILE): vol.In(gateway_profile_options),
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
                vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): NumberSelector(NumberSelectorConfig(min=1, max=247, step=1, mode=NumberSelectorMode.BOX)),
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.Coerce(int),
            }
        )

        return self.async_show_form(step_id="tcp", data_schema=schema, errors=errors)

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
            # Explicit one-time action, never persisted as a setting.
            migrate = bool(user_input.pop("restore_legacy_save_ids", False))
            if migrate:
                if self._config_entry.data.get(CONF_MODEL, "save") != "save":
                    return self.async_show_form(
                        step_id="init", data_schema=self._options_schema(),
                        errors={"base": "migration_not_save"},
                    )
                try:
                    count = restore_legacy_save_ids(self.hass, self._config_entry)
                except ValueError as err:
                    _LOGGER.warning("Legacy SAVE entity migration blocked: %s", err)
                    return self.async_show_form(
                        step_id="init", data_schema=self._options_schema(),
                        errors={"base": "migration_conflict"},
                    )
                _LOGGER.warning("Restored %d legacy SAVE entity IDs for %s", count, self._config_entry.entry_id)
            user_input[CONF_SLAVE] = int(user_input[CONF_SLAVE])
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=self._options_schema())

    def _options_schema(self):
        current_scan = self._config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        current_slave = self._config_entry.options.get(
            CONF_SLAVE,
            self._config_entry.data.get(CONF_SLAVE, DEFAULT_SLAVE),
        )
        current_profile = self._config_entry.options.get(
            CONF_GATEWAY_PROFILE,
            self._config_entry.data.get(CONF_GATEWAY_PROFILE, DEFAULT_GATEWAY_PROFILE),
        )

        gateway_profile_options = {GATEWAY_PROFILE_GENERIC: "Standard kommunikasjon", GATEWAY_PROFILE_SAVE_CONNECT: "Forsiktig kommunikasjon (begrenset belastning)"}

        is_rtu = self._config_entry.data.get("connection_type") == "aux2"
        fields = {
            vol.Optional("restore_legacy_save_ids", default=False): bool,
        }
        if not is_rtu:
            fields[vol.Required(CONF_GATEWAY_PROFILE, default=current_profile)] = vol.In(gateway_profile_options)
        fields[vol.Required(CONF_SCAN_INTERVAL, default=current_scan)] = vol.Coerce(int)
        fields[vol.Required(CONF_SLAVE, default=current_slave)] = NumberSelector(NumberSelectorConfig(min=1, max=247, step=1, mode=NumberSelectorMode.BOX))
        return vol.Schema(fields)
