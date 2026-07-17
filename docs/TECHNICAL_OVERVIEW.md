# ParkPulse — Technical Overview
**Flipkart GRID · Problem Statement 1 · Prototype Phase**

---

## Problem

> How can AI-driven parking intelligence detect illegal parking hotspots and quantify their impact on traffic flow to enable targeted enforcement?

---

## Approach

Four pipeline stages, each producing a verifiable, inspectable artifact:

```
Raw CSV (298,450 rows)
    │
    ▼
[1] Clean & Normalise        →  violations_clean.parquet
    │
    ▼
[2] Aggregate + Cluster      →  junction_daily.parquet
                                hotspots.parquet (DBSCAN)
                                temporal_patterns.parquet
    │
    ▼
[3] Score + Forecast         →  ppi_scores.parquet
                                forecast_results.parquet
    │
    ▼
[4] Allocate                 →  allocation_results.parquet
    │
    ▼
[5] Dashboard                →  Streamlit (4 screens)
```

---

## Data Findings (discovered during profiling, not assumed)

| Finding | Detail |
|---|---|
| Timezone mismatch | Timestamps stored as UTC. Peak enforcement shifts to **10:00 IST** after conversion — consistent with morning enforcement sweeps, not offense-occurrence time. Every temporal chart is labelled accordingly. |
| Unattributable records | **147,880 records (49.5%)** carry the literal string `"No Junction"` — violations with no junction attribution at entry time. Kept in the clean table, fed to DBSCAN (lat/lon), excluded from named-hotspot ranking. |
| Validation quality | **28.9%** of non-null `validation_status` values are `rejected` or `duplicate`. All PPI/forecast/allocation computations use `approved` records only. |
| Repeat offenders | 84.6% of vehicles appear exactly once. Repeat-offender analysis is real but a secondary signal, not the headline. |

---

## Module Details

### Module 1 — Cleaning (`src/pipeline/clean.py`)
- Parses `violation_type` JSON-array strings → `violation_labels` list
- Converts UTC timestamps to IST (`+05:30`)
- Builds `is_validated` flag from `validation_status == 'approved'`
- Derives `severity_weight` per record from a documented per-label table
- Normalises `junction_name` (trim, title-case)
- Drops 100%-null columns (`description`, `closed_datetime`, `action_taken_timestamp`)
- **Checkpoint**: output row count must equal 298,450 — no rows dropped, only filtered at query time

### Module 2 — Aggregation + Hotspot Detection (`src/pipeline/aggregate.py`, `hotspots.py`)
- Builds `junction_daily`: validated violations per junction per day, with repeat-vehicle counts
- DBSCAN on `(latitude, longitude)`: `eps=0.0015°` (~165m), `min_samples=20`
- Result: **236 geographic clusters**, 3.8% noise
- Cluster labels: dominant junction name (placeholders excluded) → police station → coordinate fallback
- Temporal aggregates: hour-of-day, day-of-week, month — all in IST

### Module 3a — Parking Pressure Index (`src/models/ppi.py`)

```
PPI = 0.4 × norm(violation_frequency)
    + 0.3 × norm(severity_weight)
    + 0.2 × norm(repeat_offender_ratio)
    + 0.1 × norm(persistence)
```

- `norm()` = min-max across all real junctions in the trailing 90-day window
- Placeholder junction names excluded before normalisation (prevents bucket contamination)
- Tier thresholds: quantile-based (Critical = top 10%, High = next 20%, Medium = next 30%, Low = bottom 40%)
- ±10% weight sensitivity check: top-15 ranking overlap **14–15/15** across all perturbations → **STABLE**
- Assertions: `"No Junction"` and `"Unknown"` cannot appear in output (enforced at runtime)

### Module 3b — Forecasting (`src/models/forecast.py`)
- Target: next-day validated violation count per junction
- Features: lag-1, lag-7, rolling 7/14-day mean + std, day-of-week, month, is_weekend, is_holiday, junction_id
- Models: LightGBM (primary), XGBoost (cross-check)
- Baselines: yesterday's count, 7-day rolling average
- Split: Train Nov 2023–Feb 2024 · Validate Mar 2024 · Test Apr 2024 (partial month, 0 validated rows after filter)
- Eligible junctions: top-15 by volume with ≥30 days of history

**Validation set results (Mar 2024, 15 junctions, 162 rows):**

| Metric | Value |
|---|---|
| MAE | 11.40 violations/day |
| RMSE | 15.62 |
| WAPE | 94.6% |
| vs 7-day rolling baseline MAE | 12.33 → **model wins** |
| vs yesterday's count MAE | 11.06 → near-tie (0.34 gap) |

High WAPE is expected: low-volume junctions amplify percentage error even when absolute error is small. Stated explicitly, not hidden.

### Module 4 — Patrol Allocation (`src/models/allocation.py`)

MILP formulation (PuLP open-source solver):

```
Maximise:  Σ x_i · forecasted_violations_i · ppi_weight_i
Subject to:
  Σ x_i ≤ available_units
  x_i ≤ 5   ∀ i          (prevents collapsing all units onto one hotspot)
  x_i ≥ 1   ∀ Critical i (if budget allows)
  x_i ∈ ℤ≥0
```

- Precomputed for unit counts 5, 10, 15, 20, 25 (instant lookup)
- Live solve available for any other value (typically <1 second at this scale)
- No RL — no outcome-feedback data exists to train a policy

---

## Severity Weight Table

| Violation Label | Weight | Rationale |
|---|---|---|
| PARKING IN A MAIN ROAD | 1.0 | Directly blocks major traffic artery |
| PARKING ON FOOTPATH | 0.9 | Blocks pedestrian path, safety risk |
| PARKING IN A BUS STOP | 0.8 | Blocks bus stop, delays public transit |
| PARKING NEAR ROAD CROSSING | 0.7 | Increases collision risk at junctions |
| PARKING NEAR SIGNAL | 0.7 | Impedes signal-controlled flow |
| PARKING NEAR SCHOOL | 0.6 | Safety risk near school zones |
| PARKING NEAR HOSPITAL | 0.6 | Emergency-vehicle access concern |
| WRONG PARKING | 0.5 | Generic illegal parking |
| NO PARKING | 0.5 | No-parking zone violation |

---

## Known Limitations

1. **PPI is a priority proxy** — not a measured traffic-flow metric. No speed/volume data exists in this dataset.
2. **`created_datetime` = enforcement-action time** — morning-sweep pattern reflects when officers record tags, not when vehicles parked.
3. **Forecast scope limited** — only top-15 junctions by volume with ≥30 days history. Long-tail excluded explicitly.
4. **28.9% rejected/duplicate** — validated-only view shrinks effective sample for low-volume junctions.
5. **Historical system** — no real-time feed; live enforcement triggering requires a traffic-flow API (Phase 2).

---

## Future Work

| Item | Prerequisite |
|---|---|
| Replace PPI proxy with measured traffic impact | Live speed/volume API integration |
| Auto-validate violations (reduce 28.9% rejection) | Image data + OCR/CV layer |
| RL patrol policy | Post-deployment outcome data (violation reduction after patrol) |
