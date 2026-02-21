"""Generic Modbus TCP client (async) with batching.

Defensive against pymodbus / HA wrapper signature differences.

Key points:
- Prefer keyword argument `count=` (some wrappers make it keyword-only)
- Always try to include slave/unit id FIRST (Save Connect can be strict)
- Auto-detect Save Connect quirk: FC04 (input) may be unsupported ("Illegal function")
  -> fall back to FC03 (holding) for all "input" registers, cached per client instance.

v3.1 robustness (Modbus layer only):
- 1 fast retry on read when rr.isError() or exceptions
- Max batch size + automatic splitting of large spans
- Small delay between batch calls ("be nice to gateway")
- Write-lock + cooldown: avoid polling collisions around writes (mode changes etc.)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import asyncio
import logging
import time

from pymodbus.client import AsyncModbusTcpClient

_LOGGER = logging.getLogger(__name__)

# --- Robustness knobs (v3.1) ---
MAX_BATCH_REGISTERS = 70          # 60–80 is typically a good range
INTER_BATCH_DELAY_S = 0.08        # 50–100 ms
READ_RETRY_COUNT = 1              # "1 quick retry"
READ_RETRY_DELAY_S = 0.15         # short, but enough for weak gateways
WRITE_COOLDOWN_S = 1.2            # 1–2s after write before next poll read


@dataclass
class ModbusTcpClient:
    host: str
    port: int
    slave: int

    def __post_init__(self) -> None:
        self._client: AsyncModbusTcpClient | None = None

        # Save Connect quirk: input registers (FC04) unsupported -> use holding (FC03) instead
        self._force_input_as_holding: bool = False
        self._logged_fc04_fallback: bool = False

        # v3.1: coordinate I/O to avoid read/write collisions
        self._io_lock = asyncio.Lock()
        self._last_write_monotonic: float = 0.0

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

    async def _maybe_wait_write_cooldown(self) -> None:
        """After writes, give weak gateways a short quiet period before polling."""
        if WRITE_COOLDOWN_S <= 0:
            return
        since = time.monotonic() - self._last_write_monotonic
        if since < WRITE_COOLDOWN_S:
            await asyncio.sleep(WRITE_COOLDOWN_S - since)

    async def _call_read(
        self,
        client: AsyncModbusTcpClient,
        fn_name: str,
        address: int,
        count: int,
    ):
        """Call a pymodbus read method in a signature-defensive way."""
        fn = getattr(client, fn_name)

        for kw in ("slave", "unit", "device_id"):
            try:
                return await fn(address, count=count, **{kw: self.slave})
            except TypeError:
                pass

        try:
            return await fn(address, count=count)
        except TypeError:
            pass

        for kw in ("slave", "unit", "device_id"):
            try:
                return await fn(address, count, **{kw: self.slave})
            except TypeError:
                pass

        try:
            return await fn(address, count)
        except TypeError:
            pass

        return await fn(address, count, self.slave)

    async def _call_write(self, client: AsyncModbusTcpClient, address: int, value: int):
        """Call a pymodbus write_register method in a signature-defensive way."""
        fn = client.write_register

        for kw in ("slave", "unit", "device_id"):
            try:
                return await fn(address, value, **{kw: self.slave})
            except TypeError:
                pass

        try:
            return await fn(address, value)
        except TypeError:
            pass

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
                lo = registers[idx] & 0xFFFF
                hi = registers[idx + 1] & 0xFFFF
                return (hi << 16) | lo
        except Exception:  # noqa: BLE001
            return None
        return None

    @staticmethod
    def _reg_len(data_type: str) -> int:
        return 2 if data_type == "uint32" else 1

    @staticmethod
    def _chunk_span(start: int, count: int, max_len: int) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        addr = start
        remaining = count
        while remaining > 0:
            qty = min(remaining, max_len)
            out.append((addr, qty))
            addr += qty
            remaining -= qty
        return out

    @staticmethod
    def _is_illegal_function(rr: Any) -> bool:
        # Pymodbus typically uses exception code 0x01 for illegal function
        # but we keep this permissive to handle wrapper differences.
        try:
            s = str(rr)
            return ("IllegalFunction" in s) or ("illegal function" in s.lower())
        except Exception:  # noqa: BLE001
            return False

    async def _read_with_retry(
        self,
        client: AsyncModbusTcpClient,
        fn_name: str,
        address: int,
        count: int,
    ):
        rr = None
        exc: Exception | None = None

        try:
            rr = await self._call_read(client, fn_name, address, count)
        except Exception as e:  # noqa: BLE001
            exc = e

        if exc is None and rr is not None and not rr.isError():
            return rr, None

        for _ in range(READ_RETRY_COUNT):
            await asyncio.sleep(READ_RETRY_DELAY_S)
            rr2 = None
            exc2: Exception | None = None
            try:
                rr2 = await self._call_read(client, fn_name, address, count)
            except Exception as e:  # noqa: BLE001
                exc2 = e

            if exc2 is None and rr2 is not None and not rr2.isError():
                return rr2, None

            rr = rr2 or rr
            exc = exc2 or exc

        return rr, exc

    async def read_register_map(self, register_defs: list[dict[str, Any]]) -> dict[str, Any]:
        client = await self._ensure_client()
        results: dict[str, Any] = {}

        defs_sorted = sorted(register_defs, key=lambda d: int(d["address"]))
        holding = [d for d in defs_sorted if (d.get("input_type") or "holding") == "holding"]
        inputs = [d for d in defs_sorted if (d.get("input_type") or "holding") == "input"]

        async def read_group(group: list[dict[str, Any]], requested_fn_name: str) -> None:
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

            # v3.1: cooldown + serialize I/O
            await self._maybe_wait_write_cooldown()
            async with self._io_lock:
                first_call = True

                for b in batches:
                    start = min(int(d["address"]) for d in b)
                    end = max(int(d["address"]) + self._reg_len(d.get("data_type", "int16")) for d in b)
                    count = end - start

                    chunks = self._chunk_span(start, count, MAX_BATCH_REGISTERS)

                    for chunk_start, chunk_count in chunks:
                        if not first_call and INTER_BATCH_DELAY_S > 0:
                            await asyncio.sleep(INTER_BATCH_DELAY_S)
                        first_call = False

                        # ✅ BUGFIX: if we already decided FC04 is unsupported,
                        # switch to FC03 immediately for the rest of this round.
                        fn_name = requested_fn_name
                        if fn_name == "read_input_registers" and self._force_input_as_holding:
                            fn_name = "read_holding_registers"

                        rr, exc = await self._read_with_retry(client, fn_name, chunk_start, chunk_count)
                        failed = (exc is not None) or (rr is not None and rr.isError())

                        if failed:
                            # Try FC04 -> FC03 fallback only if we were actually using FC04 here
                            if fn_name == "read_input_registers" and not self._force_input_as_holding:
                                rr2, exc2 = await self._read_with_retry(
                                    client, "read_holding_registers", chunk_start, chunk_count
                                )

                                if rr2 is not None and exc2 is None and not rr2.isError():
                                    self._force_input_as_holding = True
                                    if not self._logged_fc04_fallback:
                                        self._logged_fc04_fallback = True
                                        _LOGGER.info(
                                            "Gateway does not support FC04 for input registers; "
                                            "falling back to FC03 (holding) for all input registers."
                                        )
                                    rr = rr2
                                    exc = None
                                    failed = False
                                else:
                                    _LOGGER.debug(
                                        "Modbus read error %s @%s len=%s (fallback failed)",
                                        fn_name,
                                        chunk_start,
                                        chunk_count,
                                    )
                                    continue
                            else:
                                _LOGGER.debug(
                                    "Modbus read error %s @%s len=%s",
                                    fn_name,
                                    chunk_start,
                                    chunk_count,
                                )
                                continue

                        regs = list(rr.registers)

                        for d in b:
                            addr = int(d["address"])
                            length = self._reg_len(d.get("data_type", "int16"))

                            if addr < chunk_start or (addr + length) > (chunk_start + chunk_count):
                                continue

                            key = d["key"]
                            idx = addr - chunk_start

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
        if inputs:
            # Note: requested_fn is FC04, but bugfix will switch to FC03 within same round once detected.
            await read_group(inputs, "read_input_registers")

        return results

    async def write_register(self, address: int, value: int) -> None:
        client = await self._ensure_client()

        async with self._io_lock:
            rr = await self._call_write(client, address, int(value))
            self._last_write_monotonic = time.monotonic()

        if rr.isError():
            raise RuntimeError(f"Modbus write failed @ {address} = {value}")

    async def write_0_1c(self, address: int, temp_c: float) -> None:
        raw = int(round(float(temp_c) * 10))
        if raw < 0:
            raw = 0
        await self.write_register(address, raw)
