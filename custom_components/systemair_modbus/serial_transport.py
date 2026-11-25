"""Modbus RTU serial Modbus transport with validated FC06 writes."""
from __future__ import annotations
import asyncio
from modbus_connection import ModbusSerialParams
from homeassistant.components.modbus import async_get_unit

class SerialModbusTransport:
    """Serialize RTU reads and validated, allowlisted writes."""
    def __init__(self, hass, entry):
        data = entry.data
        params = ModbusSerialParams(
            device=data["serial_device"], baudrate=int(data["baudrate"]),
            parity=data["parity"], stopbits=int(data["stopbits"]),
            bytesize=8, framer="rtu",
        )
        self._unit = async_get_unit(hass, entry, params, int(entry.options.get("slave", data["slave"])))
        self._io_lock = asyncio.Lock()
        self._model_id = entry.data.get("model", "save")

    # Exact write targets used by the existing SAVE entity platforms.
    # No arbitrary Modbus writes are exposed by this transport.
    _WRITABLE = frozenset({
        1100, 1101, 1102, 1103, 1104, 1130, 1161,
        2000, 2503, 2504, 4100, 4101, 4102, 4103, 4104,
        4105, 4106, 4107, 4108, 4111, 4112, 7000, 7001, 7002,
    })
    # CD4 writes: manual fan-speed command (100), temperature level (206).
    _CD4_WRITABLE = frozenset({100, 206})
    _COMMAND_ADDRESSES = frozenset({1130, 1161, 7001, 7002, 100, 206})

    async def write_register(self, address: int, value: int) -> None:
        """FC06, serialized with reads; allow only known SAVE control addresses."""
        allowed = self._CD4_WRITABLE if self._model_id == "legacy_cd4" else self._WRITABLE
        if type(address) is not int or address not in allowed:
            raise ValueError(f"Modbus RTU write address not permitted: {address!r}")
        if type(value) is not int or not 0 <= value <= 65535:
            raise ValueError(f"Invalid FC06 unsigned word: {value!r}")
        if self._model_id == "legacy_cd4" and address == 100 and not 0 <= value <= 3:
            raise ValueError("CD4 fan-speed command must be 0–3")
        if self._model_id == "legacy_cd4" and address == 206 and not 0 <= value <= 29:
            raise ValueError("CD4 temperature-level command must be 0–29")
        if self._model_id == "save" and address == 2000 and not 100 <= value <= 300:
            raise ValueError("Supply-air setpoint must be 10.0–30.0 °C")
        async with self._io_lock:
            response = await self._unit.write_register(address, value)
            if response is False or (hasattr(response, "isError") and response.isError()):
                raise RuntimeError(f"Modbus RTU FC06 failed at {address}: {response!r}")
            # Command registers may change asynchronously and are not expected to echo.
            if address not in self._COMMAND_ADDRESSES:
                verify = await self._unit.read_holding_registers(address, 1)
                if (not isinstance(verify, (list, tuple)) or len(verify) != 1
                        or int(verify[0]) != value):
                    raise RuntimeError(f"Modbus RTU readback mismatch at {address}: expected {value}, got {verify!r}")

    async def write_0_1c(self, address: int, value: float) -> None:
        raw = round(value * 10)
        if abs(raw / 10 - value) > 0.001:
            raise ValueError("Temperature must use 0.1 °C increments")
        await self.write_register(address, raw)

    async def read_ascii_registers(self, address: int, count: int) -> str | None:
        """Read SAVE model text using the same decoding rules as TCP.

        Read contiguous chunks of at most 12 words; never write registers.
        """
        if not 1 <= count <= 125:
            raise ValueError("count must be between 1 and 125")
        words = []
        async with self._io_lock:
            for start in range(address, address + count, 12):
                size = min(12, address + count - start)
                part = await self._unit.read_holding_registers(start, size)
                if not isinstance(part, (list, tuple)) or len(part) != size:
                    return None
                words.extend(int(value) for value in part)
        if any(value < 0 or value > 127 for value in words):
            return None
        result = "".join(chr(value) for value in words if value != 0).strip()
        if not result or any(not char.isprintable() for char in result):
            return None
        return result

    async def read_register(self, reg):
        """One bounded read; never writes and never retries at this layer."""
        count = 2 if reg.data_type == "uint32" else 1
        async with self._io_lock:
            if reg.input_type == "input":
                words = await self._unit.read_input_registers(reg.address, count)
            else:
                words = await self._unit.read_holding_registers(reg.address, count)
        if not isinstance(words, (list, tuple)) or len(words) != count:
            raise ValueError(f"Unexpected response at {reg.address}: {words!r}")
        if reg.data_type == "uint32":
            raw = ((int(words[1]) & 0xffff) << 16) | (int(words[0]) & 0xffff)
        else:
            raw = int(words[0]) & 0xffff
            if reg.data_type == "int16" and raw >= 0x8000:
                raw -= 0x10000
        value = raw * reg.scale + reg.offset
        return round(value, reg.precision) if reg.precision is not None else value

    async def read_block(self, regs):
        """Read one contiguous, same-function block and decode each register."""
        if not regs:
            return {}
        start = regs[0].address
        count = sum(2 if r.data_type == "uint32" else 1 for r in regs)
        async with self._io_lock:
            if regs[0].input_type == "input":
                words = await self._unit.read_input_registers(start, count)
            else:
                words = await self._unit.read_holding_registers(start, count)
        if not isinstance(words, (list, tuple)) or len(words) != count:
            raise ValueError(f"Unexpected Modbus RTU block response at {start}: {words!r}")
        result = {}
        index = 0
        for reg in regs:
            width = 2 if reg.data_type == "uint32" else 1
            if reg.data_type == "uint32":
                raw = ((int(words[index + 1]) & 0xffff) << 16) | (int(words[index]) & 0xffff)
            else:
                raw = int(words[index]) & 0xffff
                if reg.data_type == "int16" and raw >= 0x8000:
                    raw -= 0x10000
            value = raw * reg.scale + reg.offset
            result[reg.key] = round(value, reg.precision) if reg.precision is not None else value
            index += width
        return result
