"""Model layer for Systemair devices."""
from .save import SaveModel
from .cd4 import Cd4Model

MODEL_REGISTRY = {
    SaveModel.model_id: SaveModel,
    Cd4Model.model_id: Cd4Model,  # "legacy_cd4"
}

