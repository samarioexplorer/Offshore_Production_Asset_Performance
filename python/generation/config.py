"""Project 2 configuration for the Orion Deepwater synthetic dataset."""

from pathlib import Path

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REFERENCE_DATA_DIR = DATA_DIR / "reference"

# ---------------------------------------------------------------------------
# Field definition
# ---------------------------------------------------------------------------

FIELD_ID = "FIELD-001"
FIELD_NAME = "Orion Deepwater Field"
BASIN = "Orion Deepwater Basin"
DEVELOPMENT_TYPE = "Subsea-FPSO"
WATER_DEPTH_FT = 6800
OPERATOR_TYPE = "Offshore Operator"
FPSO_NAME = "FPSO Orion"

FIRST_PRODUCTION_DATE = "2023-01-18"

# ---------------------------------------------------------------------------
# Population
# ---------------------------------------------------------------------------

PRODUCER_COUNT = 24
INJECTOR_COUNT = 6
MANIFOLD_COUNT = 4

# ---------------------------------------------------------------------------
# Analysis period
# ---------------------------------------------------------------------------

START_DATE = "2023-01-01"
END_DATE = "2026-12-31"

# ---------------------------------------------------------------------------
# Economics
# ---------------------------------------------------------------------------

OIL_PRICE_LOW_USD_BBL = 60.0
OIL_PRICE_BASE_USD_BBL = 75.0
OIL_PRICE_HIGH_USD_BBL = 90.0

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

RANDOM_SEED = 20260927

# ---------------------------------------------------------------------------
# Engineering ranges
# ---------------------------------------------------------------------------

PRODUCER_INITIAL_OIL_RATE_MIN_BOPD = 8000
PRODUCER_INITIAL_OIL_RATE_MAX_BOPD = 18500

PRODUCER_DECLINE_MIN_PCT = 0.04
PRODUCER_DECLINE_MAX_PCT = 0.16

INITIAL_WATER_CUT_MIN_PCT = 0.05
INITIAL_WATER_CUT_MAX_PCT = 0.25

WATER_DEPTH_MIN_FT = 6200
WATER_DEPTH_MAX_FT = 7200

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

MIN_PRODUCER_COUNT = 24
EXPECTED_MANIFOLD_COUNT = 4
EXPECTED_SCENARIO_COUNT = 3

'@ | Set-Content -Encoding UTF8 python\generation\config.py'