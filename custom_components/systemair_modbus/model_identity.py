"""Transport-independent SAVE model identification with retry on failure."""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


async def read_save_model_name(client, model, cached: str | None = None) -> str | None:
    """Return cached model name, or retry a failed/empty FC03 model read.

    A successful read is cached by the caller; failures do not poison the cache.
    Never changes normal polling register definitions.
    """
    if cached and cached.strip():
        return cached
    try:
        name = await client.read_ascii_registers(
            model.ADDR_SYSTEM_MODEL_TEXT,
            model.SYSTEM_MODEL_TEXT_REGISTER_COUNT,
        )
    except Exception as exc:  # Serial may not be ready at startup.
        _LOGGER.debug("SAVE model identification unavailable; will retry: %s", exc)
        return None
    return name.strip() if isinstance(name, str) and name.strip() else None
