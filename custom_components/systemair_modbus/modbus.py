"""Generic Modbus TCP client (async) with batching.

Defensive against pymodbus / HA wrapper signature differences.

In some environments (e.g. ModbusClientMixin), `count` is keyword-only:
  read_holding_registers(address, *, count=...)
So we must prefer keyword calls: count=count.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import logging

from pymodbus.client import AsyncModbusTcpClient

_LOGGER = logging.getLogger(__name__)


@dataclass
class ModbusTcpClient:
    host: str
    port: int
    slave: int

    def __post_init__(self) -> None:
        self._client: AsyncModbusTcpClient | None = None
        # Auto-detect/cache: some gateways (e.g. Save Connect) expose "input registers"
        # only via FC03 (holding), while others (e.g. EW11) support FC04 (input).
        self._force_input_as_holding: bool = False

    async def _ensure_client(self) -> AsyncModbusTcpClient:
        if self._client is None:
            self._client = AsyncModbusTcpClient(self.host, port=self.port)
        if not self._client.connected:
            await self._client.connect()
        return self._client

    async def async_close(self) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:  # noqa: BLE001
                pass
        self._client = None

    async def _call_read(self, client: AsyncModbusTcpClient, fn_name: str, address: int, count: int):
        fn = getattr(client, fn_name)

        # 1) Preferred: keyword-only count supported
        try:
            return await fn(address, count=count)
        except TypeError:
            pass

        # 2) Try common slave keyword names (still with count=)
        try:
            return await fn(address, count=count, slave=self.slave)
        except TypeError:
            pass
        try:
            return await fn(address, count=count, unit=self.slave)
        except TypeError:
            pass
        try:
            return await fn(address, count=count, device_id=self.slave)
        except TypeError:
            pass

        # 3) Some environments accept positional (address, count)
        try:
            return await fn(address, count)
        except TypeError:
            pass

        # 4) Last resort: positional including slave (rare)
        return await fn(address, count, self.slave)

    async def _call_write(self, client: AsyncModbusTcpClient, address: int, value: int):
        fn = client.write_register

        # 1) Preferred: simple (address, value)
        try:
            return await fn(address, value)
        except TypeError:
            pass

        # 2) Try common slave keyword names
        try:
            return await fn(address, value, slave=self.slave)
        except TypeError:
            pass
        try:
            return await fn(address, value, unit=self.slave)
        except TypeError:
            pass
        try:
            return await fn(address, value, device_id=self.slave)
        except TypeError:
            pass

        # 3) Last resort: positional including slave
        return await fn(address, value, self.slave)

    @staticmethod
    def _decode_registers(registers: list[int], idx: int, data_type: str) -> int | None:
        try:
            if data_type == "int16":
                val = registers[idx] & 0xFFFF
                if val >= 0x8000:
                    val -= 0x10000
                return val
            if data_type == "uint16":
                return registers[idx] & 0xFFFF
            if data_type == "uint32":
                # Systemair uses L/H register pairs: addr=low word, addr+1=high word
                lo = registers[idx] & 0xFFFF
                hi = registers[idx + 1] & 0xFFFF
                return (hi << 16) | lo
        except Exception:  # noqa: BLE001
            return None
        return None

    @staticmethod
    def _reg_len(data_type: str) -> int:
        return 2 if data_type == "uint32" else 1

    async def read_register_map(self, register_defs: list[dict[str, Any]]) -> dict[str, Any]:
        client = await self._ensure_client()
        results: dict[str, Any] = {}

        defs_sorted = sorted(register_defs, key=lambda d: int(d["address"]))

        holding = [d for d in defs_sorted if (d.get("input_type") or "holding") == "holding"]
        inputs = [d for d in defs_sorted if (d.get("input_type") or "holding") == "input"]

        async def read_group(group: list[dict[str, Any]], fn_name: str) -> None:
            if not group:
                return

            batches: list[list[dict[str, Any]]] = []
            batch: list[dict[str, Any]] = []
            last_end: int | None = None

            for d in group:
                addr = int(d["address"])
                length = self._reg_len(d.get("data_type", "int16"))

                if not batch:
                    batch = [d]
                    last_end = addr + length
                    continue

                if last_end is not None and addr <= last_end + 1:
                    batch.append(d)
                    last_end = max(last_end, addr + length)
                else:
                    batches.append(batch)
                    batch = [d]
                    last_end = addr + length

            if batch:
                batches.append(batch)

            for b in batches:
                start = min(int(d["address"]) for d in b)
                end = max(int(d["address"]) + self._reg_len(d.get("data_type", "int16")) for d in b)
                count = end - start

                # --- robust read with FC04 -> FC03 fallback (handles isError() + exceptions) ---
                rr = None
                exc_fc04: Exception | None = None

                try:
                    rr = await self._call_read(client, fn_name, start, count)
                except Exception as e:  # noqa: BLE001
                    exc_fc04 = e

                fc_failed = (exc_fc04 is not None) or (rr is not None and rr.isError())

                if fc_failed:
                    # Auto-detect + cache:
                    # If FC04 fails (exception or error response) but FC03 works for same batch,
                    # treat gateway as exposing "input registers" via holding registers.
                    if fn_name == "read_input_registers" and not self._force_input_as_holding:
                        rr2 = None
                        try:
                            rr2 = await self._call_read(client, "read_holding_registers", start, count)
                        except Exception:  # noqa: BLE001
                            rr2 = None

                        if rr2 is not None and not rr2.isError():
                            self._force_input_as_holding = True
                            _LOGGER.info(
                                "Gateway does not return input registers via FC04; "
                                "falling back to FC03 (holding) for all input registers."
                            )
                            rr = rr2  # decode from holding response
                        else:
                            _LOGGER.debug("Modbus read error %s @%s len=%s", fn_name, start, count)
                            continue
                    else:
                        _LOGGER.debug("Modbus read error %s @%s len=%s", fn_name, start, count)
                        continue

                # At this point rr is expected to be a successful response
                regs = list(rr.registers)

                for d in b:
                    key = d["key"]
                    addr = int(d["address"])
                    idx = addr - start

                    data_type = d.get("data_type", "int16")
                    raw = self._decode_registers(regs, idx, data_type)
                    if raw is None:
                        continue

                    scale = float(d.get("scale", 1))
                    offset = float(d.get("offset", 0))
                    precision = d.get("precision")

                    value = (raw * scale) + offset
                    if isinstance(precision, int):
                        value = round(value, precision)

                    results[key] = value

        await read_group(holding, "read_holding_registers")

        # Input registers: use FC04 unless we have detected a gateway that requires FC03.
        if inputs:
            if self._force_input_as_holding:
                await read_group(inputs, "read_holding_registers")
            else:
                await read_group(inputs, "read_input_registers")

        return results

    async def write_register(self, address: int, value: int) -> None:
        client = await self._ensure_client()
        rr = await self._call_write(client, address, int(value))
        if rr.isError():
            raise RuntimeError(f"Modbus write failed @ {address} = {value}")

    async def write_0_1c(self, address: int, temp_c: float) -> None:
        raw = int(round(float(temp_c) * 10))
        if raw < 0:
            raw = 0
        await self.write_register(address, raw)
