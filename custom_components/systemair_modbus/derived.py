"""Shared derived-value calculation for TCP and Modbus RTU coordinators."""
from __future__ import annotations


def compute_derived(model, values, *, dependencies=None):
    """Compute model-derived values without modifying the input mapping.

    Modbus RTU may pass dependency requirements to avoid reporting derived values
    from stale or missing inputs after a failed block read.
    """
    derived = model.compute_derived(values)
    if dependencies is None:
        return derived
    return {
        key: value for key, value in derived.items()
        if key not in dependencies
        or all(values.get(required) is not None for required in dependencies[key])
    }
