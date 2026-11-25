"""Resolve nominal SAVE airflow from the detected model, not the transport."""
from __future__ import annotations
import re
from .const import UNIT_MODEL_QV_MAX

def resolve_qv_max(model_text: str | None, override: str | None = None) -> int | None:
    if override and override in UNIT_MODEL_QV_MAX:
        return UNIT_MODEL_QV_MAX[override]
    if not isinstance(model_text, str):
        return None
    normalized = re.sub(r"[^A-Z0-9]", "", model_text.upper())
    matches = [(name, value) for name, value in UNIT_MODEL_QV_MAX.items()
               if value is not None and re.sub(r"[^A-Z0-9]", "", name.upper()) == normalized]
    return matches[0][1] if len(matches) == 1 else None

def update_save_airflow(model, model_text: str | None, override: str | None = None) -> None:
    if getattr(model, "model_id", None) == "save":
        model._qv_max = resolve_qv_max(model_text, override)
