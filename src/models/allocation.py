"""
Phase 4 — Patrol Allocation (MILP via PuLP)
Maximise coverage-weighted enforcement given available patrol units.
Precomputes allocations for a grid of unit counts, also supports live solve.
"""
from __future__ import annotations

import logging
import sqlite3
import uuid

import pandas as pd

from src.config import (
    ALLOCATION_PARQUET,
    DATA_PROCESSED,
    FORECAST_PARQUET,
    MAX_UNITS_PER_HOTSPOT,
    MIN_UNITS_CRITICAL,
    PPI_PARQUET,
    PRECOMPUTE_UNIT_COUNTS,
    SQLITE_DB,
    TOP_N_HOTSPOTS,
    ECONOMIC_TIME_VALUE_INR,
    ECONOMIC_FUEL_COST_INR,
    ECONOMIC_IDLE_FUEL_CONSUMPTION,
    ECONOMIC_CO2_EMISSION_KG_PER_LITER,
    AFFECTED_VEHICLES_PER_VIOLATION,
    DETERRENCE_RATE_PER_UNIT,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def compute_economic_metrics(violations: float, avg_severity: float) -> dict[str, float]:
    """Calculate Bangalore-specific economic loss parameters."""
    # Delay in minutes per violation = average severity * 10 minutes
    # Total travel delay in hours = (violations * AFFECTED_VEHICLES * avg_severity * 10) / 60
    delay_hours = (violations * AFFECTED_VEHICLES_PER_VIOLATION * avg_severity * 10.0) / 60.0
    
    # Fuel wasted (idling) in liters
    fuel_wasted = delay_hours * ECONOMIC_IDLE_FUEL_CONSUMPTION
    
    # Cost calculations
    time_cost = delay_hours * ECONOMIC_TIME_VALUE_INR
    fuel_cost = fuel_wasted * ECONOMIC_FUEL_COST_INR
    total_cost = time_cost + fuel_cost
    
    # CO2 emissions
    co2_kg = fuel_wasted * ECONOMIC_CO2_EMISSION_KG_PER_LITER
    
    return {
        "delay_hours": round(delay_hours, 1),
        "fuel_wasted_liters": round(fuel_wasted, 1),
        "economic_loss_inr": round(total_cost, 2),
        "co2_emissions_kg": round(co2_kg, 1),
    }


def solve_allocation(
    forecast_df: pd.DataFrame,
    ppi_df: pd.DataFrame,
    available_units: int,
    forecast_date: str | None = None,
    max_per_hotspot: int = MAX_UNITS_PER_HOTSPOT,
    min_critical: int = MIN_UNITS_CRITICAL,
) -> pd.DataFrame:
    """
    Solve the patrol allocation MILP for a given number of available units.

    Objective: maximise Σ x_i · (forecasted_violations_i · ppi_weight_i)
    Constraints:
      Σ x_i ≤ available_units
      x_i ≤ max_per_hotspot  ∀i
      x_i ≥ min_critical     ∀ Critical-tier hotspot i  (if units allow)
    """
    try:
        import pulp
    except ImportError:
        raise ImportError("pulp is required for patrol allocation. Install with: pip install pulp")

    # ── Prepare data ─────────────────────────────────────────────────────────
    if forecast_date is None:
        # Use tomorrow's forecast (most recent future row)
        future = forecast_df[forecast_df["actual_violations"].isna()]
        if len(future) == 0:
            future = forecast_df  # fallback to test set
        forecast_date = future["forecast_date"].max()

    day_fc = forecast_df[forecast_df["forecast_date"] == forecast_date].copy()

    # Join with PPI (including severity_component)
    merged = day_fc.merge(
        ppi_df[["junction_name_norm", "ppi_score", "ppi_tier", "severity_component"]],
        left_on="hotspot_id", right_on="junction_name_norm",
        how="inner",
    )

    if len(merged) == 0:
        log.warning("No matching hotspots for allocation on %s", forecast_date)
        return pd.DataFrame()

    # Normalise PPI score to 0–1 for weight
    ppi_min, ppi_max = merged["ppi_score"].min(), merged["ppi_score"].max()
    if ppi_max == ppi_min:
        merged["ppi_weight"] = 1.0
    else:
        merged["ppi_weight"] = (merged["ppi_score"] - ppi_min) / (ppi_max - ppi_min)

    hotspots = merged.to_dict("records")

    # ── MILP formulation ─────────────────────────────────────────────────────
    prob = pulp.LpProblem("patrol_allocation", pulp.LpMaximize)

    x = {
        h["hotspot_id"]: pulp.LpVariable(
            f"x_{i}", lowBound=0, upBound=max_per_hotspot, cat="Integer"
        )
        for i, h in enumerate(hotspots)
    }

    # Objective
    prob += pulp.lpSum(
        x[h["hotspot_id"]] * h["predicted_violations"] * h["ppi_weight"]
        for h in hotspots
    )

    # Total units constraint
    prob += pulp.lpSum(x[h["hotspot_id"]] for h in hotspots) <= available_units

    # Minimum coverage for Critical hotspots (soft — only if budget allows)
    critical_spots = [h for h in hotspots if h["ppi_tier"] == "Critical"]
    n_critical = len(critical_spots)
    if n_critical * min_critical <= available_units:
        for h in critical_spots:
            prob += x[h["hotspot_id"]] >= min_critical

    # Solve (CBC solver, no external API)
    solver = pulp.PULP_CBC_CMD(msg=0)
    prob.solve(solver)

    status = pulp.LpStatus[prob.status]
    log.info("MILP status: %s | units available: %d | date: %s", status, available_units, forecast_date)

    # ── Build result table ────────────────────────────────────────────────────
    run_id = str(uuid.uuid4())[:8]
    rows = []
    for h in hotspots:
        units = int(round(pulp.value(x[h["hotspot_id"]]) or 0))
        
        # Calculate economic metrics
        fc = h["predicted_violations"]
        sev = h.get("severity_component", 0.6)
        
        baseline = compute_economic_metrics(fc, sev)
        
        # Deterrence effect
        post_fc = fc * ((1.0 - DETERRENCE_RATE_PER_UNIT) ** units)
        post = compute_economic_metrics(post_fc, sev)
        
        savings = round(max(baseline["economic_loss_inr"] - post["economic_loss_inr"], 0.0), 2)
        co2_saved = round(max(baseline["co2_emissions_kg"] - post["co2_emissions_kg"], 0.0), 1)
        delay_reduced = round(max(baseline["delay_hours"] - post["delay_hours"], 0.0), 1)
        
        rows.append(
            {
                "run_id": run_id,
                "hotspot_id": h["hotspot_id"],
                "forecast_date": forecast_date,
                "forecasted_violations": round(fc, 1),
                "ppi_score": round(h["ppi_score"], 2),
                "ppi_tier": h["ppi_tier"],
                "units_assigned": units,
                "economic_loss_baseline_inr": baseline["economic_loss_inr"],
                "economic_savings_inr": savings,
                "co2_saved_kg": co2_saved,
                "delay_reduced_hours": delay_reduced,
                "available_units_total": available_units,
                "max_units_per_hotspot": max_per_hotspot,
                "solve_status": status,
            }
        )

    result = pd.DataFrame(rows).sort_values("units_assigned", ascending=False).reset_index(drop=True)

    # Verify constraint: no hotspot should exceed max_per_hotspot
    assert (result["units_assigned"] <= max_per_hotspot).all(), "max_units_per_hotspot constraint violated!"

    return result


def precompute_allocations(
    forecast_df: pd.DataFrame | None = None,
    ppi_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Precompute allocations for the standard unit-count grid."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    if forecast_df is None:
        forecast_df = pd.read_parquet(FORECAST_PARQUET)
    if ppi_df is None:
        ppi_df = pd.read_parquet(PPI_PARQUET)

    all_results = []
    for n_units in PRECOMPUTE_UNIT_COUNTS:
        log.info("Solving allocation for %d units …", n_units)
        result = solve_allocation(forecast_df, ppi_df, n_units)
        if len(result) > 0:
            all_results.append(result)

    combined = pd.concat(all_results, ignore_index=True)
    combined.to_parquet(ALLOCATION_PARQUET, index=False)
    log.info("allocation_results: %d rows → %s", len(combined), ALLOCATION_PARQUET)

    conn = sqlite3.connect(SQLITE_DB)
    combined.to_sql("allocation_results", conn, if_exists="replace", index=False)
    conn.close()

    return combined


if __name__ == "__main__":
    precompute_allocations()
