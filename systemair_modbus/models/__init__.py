"""Model layer for Systemair devices."""
from __future__ import annotations

from .save import SaveModel

MODEL_REGISTRY = {
    SaveModel.model_id: SaveModel,
}
