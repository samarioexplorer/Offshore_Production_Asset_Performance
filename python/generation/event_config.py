from pathlib import Path

# ---------------------------------------------------------------------------
# Project 2 - Offshore Production & Asset Performance
# Phase 4C - Downtime & Intervention Event Engine
# Event generation configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

# ---------------------------------------------------------------------------
# Downtime generation
# ---------------------------------------------------------------------------

DOWNTIME_EVENT_MIN = 600
DOWNTIME_EVENT_MAX = 900

DOWNTIME_DURATION_MIN_HR = 2.0
DOWNTIME_DURATION_MAX_HR = 48.0

LOW_SEVERITY_MAX_HR = 8.0
MEDIUM_SEVERITY_MAX_HR = 24.0

PRODUCTION_IMPACT_PROBABILITY = 0.90

DOWNTIME_TYPES = [
    "Equipment Failure",
    "Well Integrity",
    "Subsea Constraint",
    "Process Constraint",
    "Operational Event",
]

# ---------------------------------------------------------------------------
# Intervention generation
# ---------------------------------------------------------------------------

INTERVENTION_EVENT_MIN = 35
INTERVENTION_EVENT_MAX = 55

INTERVENTION_DURATION_MIN_DAYS = 1
INTERVENTION_DURATION_MAX_DAYS = 14

INTERVENTION_COST_MIN_USD = 250_000
INTERVENTION_COST_MAX_USD = 3_500_000

INTERVENTION_RECOVERY_MIN_PCT = 0.65
INTERVENTION_RECOVERY_MAX_PCT = 1.05

INTERVENTION_TYPES = [
    "Well Intervention",
    "Scale Removal",
    "Water Shutoff",
    "Artificial Lift Optimization",
    "Well Integrity Repair",
    "Production Optimization",
]

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

EVENT_RANDOM_SEED = 20260928

# ---------------------------------------------------------------------------
# QA expectations
# ---------------------------------------------------------------------------

EXPECTED_PRODUCER_COUNT = 24
EXPECTED_FAILURE_CAUSE_COUNT = 16
EXPECTED_INTERVENTION_TYPE_COUNT = 6
