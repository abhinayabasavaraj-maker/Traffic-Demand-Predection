"""
ParkPulse — Central configuration.
All magic numbers live here so sensitivity checks are easy to run.
"""
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"

RAW_CSV = DATA_RAW / "violations.csv"

# Processed outputs
VIOLATIONS_CLEAN_PARQUET = DATA_PROCESSED / "violations_clean.parquet"
JUNCTION_DAILY_PARQUET = DATA_PROCESSED / "junction_daily.parquet"
HOTSPOTS_PARQUET = DATA_PROCESSED / "hotspots.parquet"
TEMPORAL_PARQUET = DATA_PROCESSED / "temporal_patterns.parquet"
PPI_PARQUET = DATA_PROCESSED / "ppi_scores.parquet"
FORECAST_PARQUET = DATA_PROCESSED / "forecast_results.parquet"
ALLOCATION_PARQUET = DATA_PROCESSED / "allocation_results.parquet"
SQLITE_DB = DATA_PROCESSED / "parkpulse.db"
MODEL_DIR = DATA_PROCESSED / "models"

# ── Reproducibility ──────────────────────────────────────────────────────────
RANDOM_STATE = 42

# ── Cleaning ─────────────────────────────────────────────────────────────────
IST_OFFSET_HOURS = 5.5  # UTC → IST

# validation_status values treated as "validated"
VALID_STATUSES = {"approved"}

# ── Junction placeholder names — single source of truth ──────────────────────
# "No Junction" is the literal string present in 147,880 raw records (49.5% of
# all records) that had no junction attribution at entry time.
# "Unknown" is the fillna() fallback for the 5 records with a true null.
# Both are null-buckets covering violations scattered across the entire city —
# not real, actionable locations. They must be excluded from every named-
# hotspot ranking, PPI computation, and forecasting model.
# DBSCAN clustering (which keys off lat/long) is NOT affected by this filter.
JUNCTION_PLACEHOLDER_NAMES: frozenset[str] = frozenset({"No Junction", "Unknown", ""})

# ── Severity weights per violation label ────────────────────────────────────
# Ordinal scale: higher = more severe / more likely to directly block traffic
# Published in RULES.md / dashboard footnote — not a hidden constant.
SEVERITY_WEIGHTS: dict[str, float] = {
    "PARKING IN A MAIN ROAD": 1.0,
    "PARKING ON FOOTPATH": 0.9,
    "WRONG PARKING": 0.5,
    "NO PARKING": 0.5,
    "PARKING NEAR ROAD CROSSING": 0.7,
    "PARKING NEAR SIGNAL": 0.7,
    "PARKING IN A BUS STOP": 0.8,
    "PARKING NEAR SCHOOL": 0.6,
    "PARKING NEAR HOSPITAL": 0.6,
}
DEFAULT_SEVERITY_WEIGHT = 0.4  # fallback for unknown labels

# ── Economic Impact Parameters (Bangalore Traffic Congestion Costs) ─────────
ECONOMIC_TIME_VALUE_INR = 150.0  # travel time value in INR/hour
ECONOMIC_FUEL_COST_INR = 100.0   # petrol cost in INR/liter
ECONOMIC_IDLE_FUEL_CONSUMPTION = 0.6  # wasted fuel (liters/hour of congestion)
ECONOMIC_CO2_EMISSION_KG_PER_LITER = 2.3  # kg of CO2 per liter of fuel

# Delay caused in vehicle-minutes per violation label
# Parking in a main road causes the largest blockage; footpath causes less vehicle delay
VIOLATION_DELAY_VEHICLE_MINUTES: dict[str, float] = {
    "PARKING IN A MAIN ROAD": 15.0,
    "PARKING ON FOOTPATH": 3.0,
    "WRONG PARKING": 5.0,
    "NO PARKING": 5.0,
    "PARKING NEAR ROAD CROSSING": 10.0,
    "PARKING NEAR SIGNAL": 10.0,
    "PARKING IN A BUS STOP": 12.0,
    "PARKING NEAR SCHOOL": 8.0,
    "PARKING NEAR HOSPITAL": 8.0,
}
DEFAULT_DELAY_VEHICLE_MINUTES = 4.0
AFFECTED_VEHICLES_PER_VIOLATION = 120.0  # average number of vehicles delayed per violation event

# ── Emerging Hotspot Detection ──────────────────────────────────────────────
EMERGING_SHORT_WINDOW_DAYS = 14
EMERGING_LONG_WINDOW_DAYS = 30
EMERGING_THRESHOLD_RATIO = 1.35   # 35% growth in short vs long term to flag as emerging
EMERGING_MIN_DAILY_VIOLATIONS = 0.5  # must have at least 0.5 violations/day to be flagged

# ── What-If Simulator Parameters ────────────────────────────────────────────
DETERRENCE_RATE_PER_UNIT = 0.25   # 25% reduction in violations per assigned patrol unit
SPILLOVER_RATE = 0.10             # 10% of deterred violations spill over to neighbors

# ── DBSCAN ───────────────────────────────────────────────────────────────────
# eps in degrees (~0.0015° ≈ 165 m in Bangalore)
DBSCAN_EPS = 0.0015
DBSCAN_MIN_SAMPLES = 20

# ── PPI weights ──────────────────────────────────────────────────────────────
# w1: frequency, w2: severity, w3: repeat-offender ratio, w4: persistence
PPI_WEIGHTS = {"frequency": 0.4, "severity": 0.3, "repeat": 0.2, "persistence": 0.1}
PPI_SENSITIVITY_DELTA = 0.10  # ±10% perturbation for sensitivity check

# Trailing window for PPI computation (days)
PPI_WINDOW_DAYS = 90

# Quantile thresholds for tiers (computed on data, stored here after first run)
# Critical = top 10%, High = next 20%, Medium = next 30%, Low = bottom 40%
PPI_TIER_QUANTILES = {"Critical": 0.90, "High": 0.70, "Medium": 0.40}

# ── Forecasting ───────────────────────────────────────────────────────────────
# Minimum number of historical days required to forecast a hotspot
MIN_HISTORY_DAYS = 30

# Train/validate/test split (IST dates, inclusive)
TRAIN_END = "2024-02-29"
VALIDATE_START = "2024-03-01"
VALIDATE_END = "2024-03-31"
TEST_START = "2024-04-01"
TEST_END = "2024-04-08"  # partial month as per PRD

LAG_DAYS = [1, 7]
ROLLING_WINDOWS = [7, 14]

LGBM_PARAMS = {
    "n_estimators": 500,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "random_state": RANDOM_STATE,
    "n_jobs": -1,
    "verbose": -1,
}

XGB_PARAMS = {
    "n_estimators": 500,
    "learning_rate": 0.05,
    "max_depth": 6,
    "random_state": RANDOM_STATE,
    "n_jobs": -1,
    "verbosity": 0,
}

# ── Patrol Allocation ─────────────────────────────────────────────────────────
MAX_UNITS_PER_HOTSPOT = 5
MIN_UNITS_CRITICAL = 1  # minimum coverage guarantee for Critical-tier hotspots
PRECOMPUTE_UNIT_COUNTS = [5, 10, 15, 20, 25]

# ── Dashboard ────────────────────────────────────────────────────────────────
TOP_N_HOTSPOTS = 15      # shown in ranked list / forecast
TOP_N_OVERVIEW = 5       # top-5 Critical list on landing screen
MAP_CENTER = [12.97, 77.59]   # approximate Bangalore centre
MAP_ZOOM = 12

TIER_COLORS = {
    "Critical": "#d32f2f",
    "High": "#f57c00",
    "Medium": "#fbc02d",
    "Low": "#388e3c",
}
TIER_ICONS = {
    "Critical": "🔴",
    "High": "🟠",
    "Medium": "🟡",
    "Low": "🟢",
}
