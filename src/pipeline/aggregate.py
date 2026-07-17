"""
Phase 2 — Aggregation Pipeline
Produces:
  - junction_daily (aggregated counts per junction × date)
  - temporal_patterns (hour/dow/month aggregates per hotspot)
"""
from __future__ import annotations

import json
import logging
import sqlite3

import pandas as pd

from src.config import (
    DATA_PROCESSED,
    JUNCTION_DAILY_PARQUET,
    SQLITE_DB,
    TEMPORAL_PARQUET,
    VIOLATIONS_CLEAN_PARQUET,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def _load_clean(parquet: bool = True) -> pd.DataFrame:
    if parquet:
        df = pd.read_parquet(VIOLATIONS_CLEAN_PARQUET)
        df["violation_labels"] = df["violation_labels_str"].apply(json.loads)
    else:
        conn = sqlite3.connect(SQLITE_DB)
        df = pd.read_sql("SELECT * FROM violations_clean", conn)
        conn.close()
    return df


def build_junction_daily(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build the junction_daily aggregation table."""
    if df is None:
        df = _load_clean()

    # Work on validated records only (core rule)
    df_v = df[df["is_validated"]].copy()

    # --- Per-vehicle prior appearance count (for repeat-offender ratio) ---
    vehicle_appearance_count = (
        df_v.groupby(["junction_name_norm", "vehicle_number"])
        .size()
        .reset_index(name="appearances")
    )

    # A "repeat" vehicle at a junction has >1 appearance
    repeat_vehicles = vehicle_appearance_count[vehicle_appearance_count["appearances"] > 1]
    repeat_set = set(
        zip(repeat_vehicles["junction_name_norm"], repeat_vehicles["vehicle_number"])
    )

    df_v["is_repeat"] = df_v.apply(
        lambda r: (r["junction_name_norm"], r["vehicle_number"]) in repeat_set, axis=1
    )

    # Daily aggregation
    grp = df_v.groupby(["junction_name_norm", "created_date_ist"])

    jd = grp.agg(
        n_violations_validated=("violation_id", "count"),
        n_distinct_vehicles=("vehicle_number", "nunique"),
        n_repeat_vehicles=("is_repeat", "sum"),
        mean_severity_weight=("severity_weight", "mean"),
        dominant_vehicle_type=("vehicle_type", lambda x: x.mode().iloc[0] if len(x) > 0 else None),
        police_station=("police_station", lambda x: x.mode().iloc[0] if len(x) > 0 else None),
    ).reset_index()

    jd = jd.rename(columns={"created_date_ist": "date"})
    jd["date"] = pd.to_datetime(jd["date"])

    # Also add all-records count
    all_grp = df.groupby(["junction_name_norm", "created_date_ist"]).agg(
        n_violations_all=("violation_id", "count")
    ).reset_index().rename(columns={"created_date_ist": "date"})
    all_grp["date"] = pd.to_datetime(all_grp["date"])

    jd = jd.merge(all_grp, on=["junction_name_norm", "date"], how="left")
    jd["n_violations_all"] = jd["n_violations_all"].fillna(0).astype(int)

    jd.to_parquet(JUNCTION_DAILY_PARQUET, index=False)
    log.info("junction_daily: %d rows → %s", len(jd), JUNCTION_DAILY_PARQUET)

    conn = sqlite3.connect(SQLITE_DB)
    df_s = jd.copy()
    df_s["date"] = df_s["date"].astype(str)
    df_s.to_sql("junction_daily", conn, if_exists="replace", index=False)
    conn.close()

    return jd


def build_temporal_patterns(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build hour/dow/month aggregates per junction (validated records only)."""
    if df is None:
        df = _load_clean()

    df_v = df[df["is_validated"]].copy()

    # Hour distribution per junction
    hour_df = (
        df_v.groupby(["junction_name_norm", "created_hour_ist"])
        .size()
        .reset_index(name="count")
        .assign(dimension="hour", dimension_value=lambda x: x["created_hour_ist"].astype(str))
        [["junction_name_norm", "dimension", "dimension_value", "count"]]
    )

    # Day-of-week distribution
    dow_labels = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    dow_df = (
        df_v.groupby(["junction_name_norm", "created_dow"])
        .size()
        .reset_index(name="count")
        .assign(
            dimension="dow",
            dimension_value=lambda x: x["created_dow"].map(dow_labels),
        )
        [["junction_name_norm", "dimension", "dimension_value", "count"]]
    )

    # Month distribution
    month_labels = {
        11: "Nov-23", 12: "Dec-23", 1: "Jan-24", 2: "Feb-24",
        3: "Mar-24", 4: "Apr-24",
    }
    month_df = (
        df_v.groupby(["junction_name_norm", "created_month"])
        .size()
        .reset_index(name="count")
        .assign(
            dimension="month",
            dimension_value=lambda x: x["created_month"].map(month_labels),
        )
        [["junction_name_norm", "dimension", "dimension_value", "count"]]
    )

    temporal = pd.concat([hour_df, dow_df, month_df], ignore_index=True)

    temporal.to_parquet(TEMPORAL_PARQUET, index=False)
    log.info("temporal_patterns: %d rows → %s", len(temporal), TEMPORAL_PARQUET)

    conn = sqlite3.connect(SQLITE_DB)
    temporal.to_sql("temporal_patterns", conn, if_exists="replace", index=False)
    conn.close()

    return temporal


def run_aggregation() -> None:
    df = _load_clean()
    log.info("Loaded violations_clean: %d rows", len(df))

    # Citywide hourly sanity-check (enforcement-action time)
    hour_counts = df[df["is_validated"]]["created_hour_ist"].value_counts().sort_index()
    peak_hour = hour_counts.idxmax()
    log.info(
        "Citywide IST hour distribution peak: %02d:00 (expected ~10–11 IST). "
        "Hours 0–13 account for %.1f%% of validated records.",
        peak_hour,
        hour_counts[hour_counts.index <= 13].sum() / hour_counts.sum() * 100,
    )

    build_junction_daily(df)
    build_temporal_patterns(df)
    log.info("Aggregation complete.")


if __name__ == "__main__":
    run_aggregation()
