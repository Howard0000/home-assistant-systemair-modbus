"""Opt-in, collision-safe restoration of legacy SAVE entity IDs.

Only entity_id values are updated. Existing unique_id values are never changed.
No changes to Modbus communication or model registers.
"""
from __future__ import annotations

import re
from homeassistant.helpers import entity_registry as er

# Current default device-name prefixes vary by detected SAVE model.
_CURRENT_SAVE_ID = re.compile(r"^(?P<domain>[a-z_]+)\.(?:[a-z0-9_]+_)?systemair_.+?_save_(?P<suffix>[a-z0-9_]+)$")


def plan_legacy_save_ids(hass, entry):
    """Build a complete migration plan without changing HA state.

    Refuse the entire operation if any target ID is already registered.
    This avoids taking over entities from another Systemair unit.
    """
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, entry.entry_id)
    plan = []
    for entity in entries:
        match = _CURRENT_SAVE_ID.fullmatch(entity.entity_id)
        if not match:
            # Compatibility alias missed by the first migration: the older
            # Norwegian entity ID used "oko", while the current translation
            # produces "eco". Handle this even after the bulk migration ran.
            if entity.entity_id == "number.systemair_save_eco_varmeoffset":
                target = "number.systemair_save_oko_varmeoffset"
                if registry.async_get(target) is not None:
                    raise ValueError(f"Target entity ID is already registered: {target}")
                plan.append((entity.entity_id, target))
            continue
        suffix = match.group("suffix")
        # New RTU diagnostics have no legacy counterpart.
        if suffix.startswith("modbus_rtu_"):
            continue
        target = f"{match.group('domain')}.systemair_save_{suffix}"
        if target == "number.systemair_save_eco_varmeoffset":
            target = "number.systemair_save_oko_varmeoffset"
        if target == entity.entity_id:
            continue
        if registry.async_get(target) is not None:
            raise ValueError(f"Target entity ID is already registered: {target}")
        plan.append((entity.entity_id, target))
    if not plan:
        raise ValueError("No eligible SAVE entities were found for migration")
    if len({target for _, target in plan}) != len(plan):
        raise ValueError("Multiple entities would receive the same target ID")
    return plan


def restore_legacy_save_ids(hass, entry):
    """Restore legacy IDs after a complete collision preflight.

    Intended only for a single SAVE device on installations where old IDs
    were removed. Back up Home Assistant before using this operation.
    """
    registry = er.async_get(hass)
    plan = plan_legacy_save_ids(hass, entry)
    for old_id, new_id in plan:
        registry.async_update_entity(old_id, new_entity_id=new_id)
    return len(plan)
