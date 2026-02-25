"""Generic Modbus TCP client (async) with batching.

Defensive against pymodbus / HA wrapper signature differences.

Key points:
- Prefer keyword argument `count=` (some wrappers make it keyword-only)
- Always try to include slave/unit id FIRST (Save Connect can be strict)
- Auto-detect Save Connect quirk: FC04 (input) may be unsupported ("Illegal function")
  -> fall back to FC03 (holding) for all "input" registers, cached per client instance.

Profiles:
- generic: aggressive batching, can bridge holes, tries FC04 for input registers
- save_connect: safe mode (uint32-safe batch=2), no hole bridging, forces FC03 for "input"
               + serial request queue + pacing + retries/backoff (SAVE Connect robustness)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Awaitable
import logging
import asyncio
import inspect

from pymodbus.client import AsyncModbusTcpClient

_LOGGER = logging.getLogger(__name__)


# These mimic the old HA modbus yaml defaults Philippe shared.
DEFAULT_TIMEOUT_S = 5
DEFAULT_CONNECT_DELAY_S = 10
DEFAULT_MESSAGE_WAIT_S = 0.03  # 30 ms (after each request)

# Save Connect safe-mode extras
DEFAULT_SAVE_CONNECT_PACING_S = 0.10  # 100 ms between requests
DEFAULT_SAVE_CONNECT_RETRIES = 5
DEFAULT_SAVE_CONNECT_BACKOFF_BASE_S = 0.20  # exponential backoff base

# Profiles / gateway strategies
GATEWAY_PROFILE_GENERIC = "generic"
GATEWAY_PROFILE_SAVE_CONNECT = "save_connect"

PROFILE_CONFIG: dict[str, dict[str, Any]] = {
    GATEWAY_PROFILE_GENERIC: {
        "max_batch_size": None,           # allow large reads
        "bridge_holes": True,             # allow grouping across holes
        "force_input_as_holding": False,  # try FC04 normally

        # robustness features OFF for generic
        "use_queue": False,
        "pacing_s": 0.0,
        "retries": 3,
        "backoff_base_s": 0.0,

        # NEW: profile-controlled connect delay (avoid slowing down generic gateways)
        "connect_delay_s": 0.0,
    },
    GATEWAY_PROFILE_SAVE_CONNECT: {
        "max_batch_size": 2,              # uint32-safe, very conservative
        "bridge_holes": False,            # only strictly contiguous
        "force_input_as_holding": True,   # avoid FC04 entirely

        # robustness features ON for Save Connect
        "use_queue": True,
        "pacing_s": DEFAULT_SAVE_CONNECT_PACING_S,
        "retries": DEFAULT_SAVE_CONNECT_RETRIES,
        "backoff_base_s": DEFAULT_SAVE_CONNECT_BACKOFF_BASE_S,

        # NEW: keep conservative connect delay for save_connect safe mode
        "connect_delay_s": float(DEFAULT_CONNECT_DELAY_S),
    },
}


async def _safe_client_close(client: AsyncModbusTcpClient | None) -> None:
    """Close pymodbus client in a way that works across versions (sync or async close)."""
    if client is None:
        return
    try:
        res = client.close()
        if inspect.isawaitable(res):
            await res
    except Exception:  # noqa: BLE001
        # Best-effort close; some gateways/versions can throw during shutdown.
        pass


@dataclass
class ModbusTcpClient:
    host: str
    port: int
    slave: int
    gateway_profile: str = GATEWAY_PROFILE_GENERIC

    def __post_init__(self) -> None:
        self._client: AsyncModbusTcpClient | None = None

        profile = PROFILE_CONFIG.get(self.gateway_profile, PROFILE_CONFIG[GATEWAY_PROFILE_GENERIC])
        self._max_batch_size: int | None = profile["max_batch_size"]
        self._bridge_holes: bool = bool(profile["bridge_holes"])
        self._force_input_as_holding: bool = bool(profile["force_input_as_holding"])

        self._use_queue: bool = bool(profile.get("use_queue", False))
        self._pacing_s: float = float(profile.get("pacing_s", 0.0) or 0.0)
        self._retries: int = int(profile.get("retries", 3) or 3)
        self._backoff_base_s: float = float(profile.get("backoff_base_s", 0.0) or 0.0)

        # NEW: profile-controlled connect delay
        self._connect_delay_s: float = float(profile.get("connect_delay_s", 0.0) or 0.0)

        self._connected_once: bool = False
        self._io_lock = asyncio.Lock()

        # SAVE Connect queue/worker (only used if _use_queue)
        self._queue: asyncio.Queue[tuple[str, Callable[[], Awaitable[Any]], asyncio.Future[Any]]] | None = None
        self._worker_task: asyncio.Task | None = None
        self._stop_worker = asyncio.Event()

        _LOGGER.info(
            "Modbus client using gateway profile '%s' "
            "(max_batch_size=%s, bridge_holes=%s, force_input_as_holding=%s, "
            "use_queue=%s, pacing_s=%s, retries=%s, backoff_base_s=%s)",
            self.gateway_profile,
            self._max_batch_size,
            self._bridge_holes,
            self._force_input_as_holding,
            self._use_queue,
            self._pacing_s,
            self._retries,
            self._backoff_base_s,
        )

    # ----------------------------
    # Client lifecycle
    # ----------------------------

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
                # NEW: profile-controlled delay (generic=0, save_connect=10s)
                if self._connect_delay_s > 0:
                    await asyncio.sleep(self._connect_delay_s)

        return self._client

    async def _force_reconnect(self) -> None:
        """Close + reset client. Next call will reconnect."""
        try:
            if self._client is not None:
                await _safe_client_close(self._client)
        except Exception:  # noqa: BLE001
            pass
        self._client = None
        self._connected_once = False

    async def async_close(self) -> None:
        # stop worker first (so it doesn't keep using client)
        await self._stop_queue_worker()

        if self._client is not None:
            try:
                await _safe_client_close(self._client)
            except Exception:  # noqa: BLE001
                pass
        self._client = None
        self._connected_once = False

    # ----------------------------
    # Queue worker (SAVE Connect safe mode)
    # ----------------------------

    async def _ensure_queue_worker(self) -> None:
        if not self._use_queue:
            return
        if self._queue is None:
            self._queue = asyncio.Queue()
        if self._worker_task is None or self._worker_task.done():
            self._stop_worker.clear()
            self._worker_task = asyncio.create_task(self._queue_worker(), name="systemair_modbus_queue_worker")

    async def _stop_queue_worker(self) -> None:
        if self._worker_task is None:
            return
        self._stop_worker.set()
        try:
            self._worker_task.cancel()
        except Exception:  # noqa: BLE001
            pass
        try:
            await asyncio.wait_for(asyncio.shield(self._worker_task), timeout=1.0)
        except Exception:  # noqa: BLE001
            pass
        self._worker_task = None
        self._queue = None

    async def _queue_worker(self) -> None:
        """Single worker to serialize Modbus requests (SAVE Connect robustness)."""
        assert self._queue is not None

        while not self._stop_worker.is_set():
            try:
                op_name, op_coro_factory, fut = await self._queue.get()
            except asyncio.CancelledError:
                return

            if fut.cancelled():
                self._queue.task_done()
                continue

            try:
                result = await op_coro_factory()
                if not fut.cancelled():
                    fut.set_result(result)
            except Exception as e:  # noqa: BLE001
                if not fut.cancelled():
                    fut.set_exception(e)
            finally:
                # pacing between requests for SAVE Connect
                if self._pacing_s > 0:
                    try:
                        await asyncio.sleep(self._pacing_s)
                    except asyncio.CancelledError:
                        return
                self._queue.task_done()

    async def _enqueue(self, op_name: str, op: Callable[[], Awaitable[Any]]) -> Any:
        """Enqueue an op and wait for result. Only used in save_connect profile."""
        await self._ensure_queue_worker()
        assert self._queue is not None

        loop = asyncio.get_running_loop()
        fut: asyncio.Future[Any] = loop.create_future()
        await self._queue.put((op_name, op, fut))
        return await fut

    # ----------------------------
    # Signature-defensive pymodbus calls
    # ----------------------------

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

    # ----------------------------
    # Helpers
    # ----------------------------

    @staticmethod
    def _is_gateway_busy(rr: Any) -> bool:
        """Best-effort detection of 'device busy' / 'gateway target failed'."""
        try:
            if rr is None:
                return False
            if not hasattr(rr, "isError") or not rr.isError():
                return False
            exc_code = getattr(rr, "exception_code", None)
            # Common Modbus exception codes:
            # 06 = Slave Device Busy
            # 0B (11) = Gateway Target Device Failed to Respond
            return exc_code in (6, 11)
        except Exception:  # noqa: BLE001
            return False

    def _calc_backoff(self, attempt: int, busy: bool) -> float:
        if self._backoff_base_s <= 0:
            return 0.0
        # Exponential backoff. If "busy", be a bit nicer.
        base = self._backoff_base_s * (2**attempt)
        if busy:
            base *= 1.5
        # Cap to something reasonable
        return min(base, 5.0)

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

    # ----------------------------
    # Core IO operations
    # ----------------------------

    async def _read_once(self, fn_name: str, address: int, count: int):
        """Single read attempt."""
        client = await self._ensure_client()
        return await self._call_read(client, fn_name, address, count)

    async def _write_once(self, address: int, value: int):
        """Single write attempt."""
        client = await self._ensure_client()
        return await self._call_write(client, address, value)

    async def _robust_read(self, fn_name: str, address: int, count: int):
        """Read with retries/backoff and reconnect on failure (used mainly for SAVE Connect)."""
        last_exc: Exception | None = None
        last_rr: Any = None

        for attempt in range(max(1, self._retries)):
            try:
                rr = await self._read_once(fn_name, address, count)
                last_rr = rr
                if rr is not None and hasattr(rr, "isError") and rr.isError():
                    busy = self._is_gateway_busy(rr)
                    backoff = self._calc_backoff(attempt, busy)
                    if backoff > 0:
                        await asyncio.sleep(backoff)
                    # For some error patterns, reconnect helps
                    if attempt < (self._retries - 1):
                        await self._force_reconnect()
                        continue
                return rr
            except Exception as e:  # noqa: BLE001
                last_exc = e
                backoff = self._calc_backoff(attempt, False)
                if backoff > 0:
                    await asyncio.sleep(backoff)
                if attempt < (self._retries - 1):
                    await self._force_reconnect()
                    continue

        if last_exc is not None:
            raise last_exc
        return last_rr

    async def _robust_write(self, address: int, value: int):
        """Write with retries/backoff and reconnect on failure (used mainly for SAVE Connect)."""
        last_exc: Exception | None = None
        last_rr: Any = None

        for attempt in range(max(1, self._retries)):
            try:
                rr = await self._write_once(address, value)
                last_rr = rr
                if rr is not None and hasattr(rr, "isError") and rr.isError():
                    busy = self._is_gateway_busy(rr)
                    backoff = self._calc_backoff(attempt, busy)
                    if backoff > 0:
                        await asyncio.sleep(backoff)
                    if attempt < (self._retries - 1):
                        await self._force_reconnect()
                        continue
                return rr
            except Exception as e:  # noqa: BLE001
                last_exc = e
                backoff = self._calc_backoff(attempt, False)
                if backoff > 0:
                    await asyncio.sleep(backoff)
                if attempt < (self._retries - 1):
                    await self._force_reconnect()
                    continue

        if last_exc is not None:
            raise last_exc
        return last_rr

    async def _do_read(self, fn_name: str, address: int, count: int):
        """Read wrapper with profile-specific execution path."""
        if self._use_queue:
            # SAVE Connect: serialized + robust read in queue
            async def op():
                rr = await self._robust_read(fn_name, address, count)
                if DEFAULT_MESSAGE_WAIT_S > 0:
                    await asyncio.sleep(DEFAULT_MESSAGE_WAIT_S)
                return rr

            return await self._enqueue(f"read:{fn_name}@{address}x{count}", op)

        # Generic/EW11: preserve old behavior (direct) + io_lock + message_wait
        client = await self._ensure_client()
        async with self._io_lock:
            rr = await self._call_read(client, fn_name, address, count)
            if DEFAULT_MESSAGE_WAIT_S > 0:
                await asyncio.sleep(DEFAULT_MESSAGE_WAIT_S)
        return rr

    async def _do_write(self, address: int, value: int):
        """Write wrapper with profile-specific execution path."""
        if self._use_queue:
            # SAVE Connect: serialized + robust write in queue
            async def op():
                rr = await self._robust_write(address, value)
                if DEFAULT_MESSAGE_WAIT_S > 0:
                    await asyncio.sleep(DEFAULT_MESSAGE_WAIT_S)
                return rr

            return await self._enqueue(f"write@{address}={value}", op)

        # Generic/EW11: preserve old behavior (direct) + io_lock + message_wait
        client = await self._ensure_client()
        async with self._io_lock:
            rr = await self._call_write(client, address, value)
            if DEFAULT_MESSAGE_WAIT_S > 0:
                await asyncio.sleep(DEFAULT_MESSAGE_WAIT_S)
        return rr

    # ----------------------------
    # Public API
    # ----------------------------

    async def read_register_map(self, register_defs: list[dict[str, Any]]) -> dict[str, Any]:
        # Ensure worker exists early (SAVE Connect only)
        await self._ensure_queue_worker()

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

                # Strict contiguous by default: addr == last_end
                contiguous = last_end is not None and addr == last_end

                # Generic profile may allow bridging "holes"
                if self._bridge_holes and last_end is not None:
                    contiguous = addr <= last_end

                if contiguous:
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

                max_batch = self._max_batch_size
                if max_batch is None:
                    ranges = [(start, count)]
                else:
                    # Ensure we can still read uint32 values (2 registers).
                    max_count = max(2, int(max_batch))
                    ranges = _split_ranges(start, count, max_count)

                for r_start, r_count in ranges:
                    # Decide function code per batch.
                    if group_type == "input" and self._force_input_as_holding:
                        fn_name = "read_holding_registers"
                    elif group_type == "input":
                        fn_name = "read_input_registers"
                    else:
                        fn_name = "read_holding_registers"

                    rr = None
                    exc: Exception | None = None

                    try:
                        rr = await self._do_read(fn_name, r_start, r_count)
                    except Exception as e:  # noqa: BLE001
                        exc = e

                    failed = (exc is not None) or (rr is not None and rr.isError())

                    if failed:
                        # Auto-detect Save Connect: FC04 unsupported -> use FC03 for "input" regs
                        if fn_name == "read_input_registers" and not self._force_input_as_holding:
                            rr2 = None
                            exc2: Exception | None = None
                            try:
                                rr2 = await self._do_read("read_holding_registers", r_start, r_count)
                            except Exception as e:  # noqa: BLE001
                                exc2 = e

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
        # Ensure worker exists early (SAVE Connect only)
        await self._ensure_queue_worker()

        rr = await self._do_write(address, value)
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