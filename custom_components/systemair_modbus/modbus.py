"""Generic Modbus TCP client (async) with batching.

Defensive against pymodbus / HA wrapper signature differences.

Key points:
- Prefer keyword argument `count=` (some wrappers make it keyword-only)
- Always try to include slave/unit id FIRST (Save Connect can be strict)
- Auto-detect Save Connect quirk: FC04 (input) may be unsupported ("Illegal function")
  -> fall back to FC03 (holding) for all "input" registers, cached per client instance.

Fixes vs previous file:
- Once FC04->FC03 fallback is detected, we immediately use FC03 for the *rest of the same poll cycle*.
  (Previously we still called FC04 for remaining input batches, causing "read_input_registers" spam
  and sometimes leaving entities unpopulated at startup.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import logging
import asyncio

from pymodbus.client import AsyncModbusTcpClient

_LOGGER = logging.getLogger(__name__)


# These mimic the old HA modbus yaml defaults Philippe shared.
DEFAULT_TIMEOUT_S = 5
DEFAULT_CONNECT_DELAY_S = 10
DEFAULT_MESSAGE_WAIT_S = 0.03  # 30 ms

# Limit maximum number of registers per Modbus request (count).
# NOTE: Must be >= 2 to support uint32 (2-register) values.
# Set to None to disable (current behaviour).
DEFAULT_MAX_BATCH_SIZE: int | None = 2


@dataclass
class ModbusTcpClient:
    host: str
    port: int
    slave: int

    def __post_init__(self) -> None:
        self._client: AsyncModbusTcpClient | None = None
        # Some gateways (e.g. Systemair Save Connect 1.0) expose many "IR" registers
        # only via FC03 (holding), while others (e.g. EW11) support FC04 (input).
        self._force_input_as_holding: bool = False
        self._connected_once: bool = False
        self._io_lock = asyncio.Lock()

    async def _ensure_client(self) -> AsyncModbusTcpClient:
        if self._client is None:
            # AsyncModbusTcpClient accepts timeout in recent pymodbus.
            # If your HA/pymodbus build does not accept it, it will raise TypeError
            # and we fall back to constructor without timeout.
            try:
                self._client = AsyncModbusTcpClient(self.host, port=self.port, timeout=DEFAULT_TIMEOUT_S)
            except TypeError:
                self._client = AsyncModbusTcpClient(self.host, port=self.port)

        if not self._client.connected:
            await self._client.connect()
            # "delay" from old yaml: some gateways need a short pause after connect.
            if not self._connected_once:
                self._connected_once = True
                if DEFAULT_CONNECT_DELAY_S > 0:
                    await asyncio.sleep(DEFAULT_CONNECT_DELAY_S)

        return self._client

    async def async_close(self) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:  # noqa: BLE001
                pass
        self._client = None
        self._connected_once = False

    async def _call_read(
        self,
        client: AsyncModbusTcpClient,
        fn_name: str,
        address: int,
        count: int,
    ):
        """Call a pymodbus read method in a signature-defensive way.

        IMPORTANT: try to pass slave/unit FIRST (many Modbus servers are strict).
        """
        fn = getattr(client, fn_name)

        # 1) Preferred: keyword-only count supported + explicit slave/unit id
        for kw in ("slave", "unit", "device_id", "unit_id"):
            try:
                return await fn(address, count=count, **{kw: self.slave})
            except TypeError:
                pass

        # 2) Next: keyword-only count supported (no slave/unit)
        try:
            return await fn(address, count=count)
        except TypeError:
            pass

        # 3) Try positional (address, count) with explicit slave/unit id via keywords (count positional)
        for kw in ("slave", "unit", "device_id", "unit_id"):
            try:
                return await fn(address, count, **{kw: self.slave})
            except TypeError:
                pass

        # 4) Some environments accept positional (address, count)
        try:
            return await fn(address, count)
        except TypeError:
            pass

        # 5) Last resort: positional including slave (rare)
        return await fn(address, count, self.slave)

    async def _call_write(self, client: AsyncModbusTcpClient, address: int, value: int):
        """Call a pymodbus write_register method in a signature-defensive way."""
        fn = client.write_register

        # 1) Preferred: explicit slave/unit id
        for kw in ("slave", "unit", "device_id", "unit_id"):
            try:
                return await fn(address, value, **{kw: self.slave})
            except TypeError:
                pass

        # 2) Simple (address, value)
        try:
            return await fn(address, value)
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

        async def read_group(group: list[dict[str, Any]], group_type: str) -> None:
            """Read one group (holding/input) in contiguous batches.

            group_type: "holding" | "input" (the *logical* type from the register map).
            """
            if not group:
                return

            # Build contiguous-ish batches
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


            def _split_ranges(start: int, count: int, max_count: int) -> list[tuple[int, int]]:
                out: list[tuple[int, int]] = []
                s = start
                remaining = count
                while remaining > 0:
                    c = min(max_count, remaining)
                    out.append((s, c))
                    s += c
                    remaining -= c
                return out

            for b in batches:
                start = min(int(d["address"]) for d in b)
                end = max(int(d["address"]) + self._reg_len(d.get("data_type", "int16")) for d in b)
                count = end - start

                max_batch = DEFAULT_MAX_BATCH_SIZE
                if max_batch is None:
                    ranges = [(start, count)]
                else:
                    # Ensure we can still read uint32 values (2 registers).
                    max_count = max(2, int(max_batch))
                    ranges = _split_ranges(start, count, max_count)

                for r_start, r_count in ranges:
                    # IMPORTANT: decide function code per batch, based on current fallback flag.
                    if group_type == "input" and self._force_input_as_holding:
                        fn_name = "read_holding_registers"
                    elif group_type == "input":
                        fn_name = "read_input_registers"
                    else:
                        fn_name = "read_holding_registers"

                    rr = None
                    exc: Exception | None = None

                    async with self._io_lock:
                        try:
                            rr = await self._call_read(client, fn_name, r_start, r_count)
                        except Exception as e:  # noqa: BLE001
                            exc = e

                        # "message_wait_milliseconds" equivalent
                        if DEFAULT_MESSAGE_WAIT_S > 0:
                            await asyncio.sleep(DEFAULT_MESSAGE_WAIT_S)

                    failed = (exc is not None) or (rr is not None and rr.isError())

                    if failed:
                        # Auto-detect Save Connect: FC04 unsupported -> use FC03 for "input" regs
                        if fn_name == "read_input_registers" and not self._force_input_as_holding:
                            rr2 = None
                            exc2: Exception | None = None

                            async with self._io_lock:
                                try:
                                    rr2 = await self._call_read(client, "read_holding_registers", r_start, r_count)
                                except Exception as e:  # noqa: BLE001
                                    exc2 = e

                                if DEFAULT_MESSAGE_WAIT_S > 0:
                                    await asyncio.sleep(DEFAULT_MESSAGE_WAIT_S)

                            if rr2 is not None and not rr2.isError():
                                self._force_input_as_holding = True
                                _LOGGER.info(
                                    "Gateway does not support FC04 for input registers; "
                                    "falling back to FC03 (holding) for all input registers."
                                )
                                rr = rr2
                            else:
                                _LOGGER.debug("Modbus read error %s @%s len=%s", fn_name, r_start, r_count)
                                if exc is not None:
                                    _LOGGER.debug("Read exception (%s): %s", fn_name, exc)
                                if exc2 is not None:
                                    _LOGGER.debug("Fallback exception (read_holding_registers): %s", exc2)
                                continue
                        else:
                            _LOGGER.debug("Modbus read error %s @%s len=%s", fn_name, r_start, r_count)
                            if exc is not None:
                                _LOGGER.debug("Read exception (%s): %s", fn_name, exc)
                            continue

                    regs = list(rr.registers)

                    for d in b:
                        key = d.get("key")
                        addr = int(d["address"])
                        reg_len = self._reg_len(d.get("data_type", "int16"))

                        # Only decode values fully covered by this sub-range
                        if addr < r_start or (addr + reg_len) > (r_start + r_count):
                            continue

                        idx = addr - r_start

                        dt = d.get("data_type", "int16")
                        raw = self._decode_registers(regs, idx, dt)
                        if raw is None:
                            continue

                        scale = float(d.get("scale", 1.0) or 1.0)
                        offset = float(d.get("offset", 0.0) or 0.0)
                        val: Any = raw * scale + offset

                        precision = d.get("precision")
                        if precision is not None:
                            try:
                                val = round(float(val), int(precision))
                            except Exception:  # noqa: BLE001
                                pass

                        if key:
                            results[key] = val

        # Read holding registers first
        await read_group(holding, "holding")
        # Then logical input registers (which may be read via FC03 on Save Connect)
        await read_group(inputs, "input")

        return results

    async def write_register(self, address: int, value: int) -> None:
        client = await self._ensure_client()

        async with self._io_lock:
            rr = await self._call_write(client, address, value)
            if DEFAULT_MESSAGE_WAIT_S > 0:
                await asyncio.sleep(DEFAULT_MESSAGE_WAIT_S)

        if rr is None or rr.isError():
            raise RuntimeError(f"Modbus write failed @ {address} = {value}")
    async def write_0_1c(self, address: int, temp_c: float) -> None:
        """Write a temperature value in 0.1°C units (e.g. 21.5°C -> 215).

        Some SAVE registers use 0.1°C scaling.
        """
        raw = int(round(float(temp_c) * 10.0))
        # Defensive clamp (some devices don't accept negative setpoints)
        if raw < 0:
            raw = 0
        await self.write_register(address, raw)
