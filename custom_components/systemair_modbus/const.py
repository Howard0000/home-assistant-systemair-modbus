"""Constants for Systemair Modbus integration."""
from __future__ import annotations

DOMAIN = "systemair_modbus"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_SLAVE = "slave"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MODEL = "model"

DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
DEFAULT_SCAN_INTERVAL = 10  # seconds

PLATFORMS: list[str] = ["sensor", "binary_sensor", "switch", "select", "number", "climate", "button"]

# Modell-IDer må matche models/*.py
MODEL_SAVE = "save"
SUPPORTED_MODELS = [MODEL_SAVE]
CONF_UNIT_MODEL = "unit_model"

# Nominal max air flow (qv max) per unit model (m³/h). Used for *estimated* air flow rate derived sensors.
# Source: Systemair datasheets / ErP tables (Ps ref 50 Pa).
# NOTE: Actual air flow depends on installation and duct pressure; this is only an estimate.
UNIT_MODEL_QV_MAX: dict[str, int | None] = {
    "Generic (legacy x3)": None,
    # VSR series
    "VSR 150/B": 169,
    "VSR 200/B": 284,
    "VSR 300": 368,
    "VSR 400": 615,
    "VSR 500": 609,
    "VSR 700": 870,
    # VTR series
    "VTR 100/B": 150,
    "VTR 150/B": 268,  # typical (variants exist)
    "VTR 250/B": 307,
    "VTR 275/B": 316,
    "VTR 300": 368,
    "VTR 350/B": 504,
    "VTR 500": 572,
    "VTR 700": 951,
}
