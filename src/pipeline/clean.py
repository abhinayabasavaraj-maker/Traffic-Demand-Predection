"""
Phase 1 — Cleaning Pipeline
Produces violations_clean (Parquet + SQLite table).
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
from pathlib import Path

import pandas as pd

from src.config import (
    DATA_PROCESSED,
    DEFAULT_SEVERITY_WEIGHT,
    IST_OFFSET_HOURS,
    RAW_CSV,
    RANDOM_STATE,
    SEVERITY_WEIGHTS,
    SQLITE_DB,
    VALID_STATUSES,
    VIOLATIONS_CLEAN_PARQUET,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def _parse_label_string(raw: str) -> list[str]:
    """Parse a violation_type / offence_code JSON-array-like string to a Python list."""
    if not isinstance(raw, str):
        return []
    raw = raw.strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(v).strip().upper() for v in parsed]
    except json.JSONDecodeError:
        pass
    # Fallback: strip brackets, split on comma
    raw = re.sub(r"[\[\]]", "", raw)
    return [v.strip().strip('"').upper() for v in raw.split(",") if v.strip()]


def _compute_severity(labels: list[str]) -> float:
    """Average severity weight across all violation labels for one record."""
    if not labels:
        return DEFAULT_SEVERITY_WEIGHT
    weights = [SEVERITY_WEIGHTS.get(lbl, DEFAULT_SEVERITY_WEIGHT) for lbl in labels]
    return round(sum(weights) / len(weights), 4)


def run_cleaning(raw_csv: Path = RAW_CSV, out_parquet: Path = VIOLATIONS_CLEAN_PARQUET) -> pd.DataFrame:
    """Load, clean, and save violations_clean. Returns the cleaned DataFrame."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    log.info("Loading raw CSV …")
    df = pd.read_csv(raw_csv, low_memory=False)
    log.info("Raw rows: %d, columns: %d", len(df), df.shape[1])

    # ── De-duplicate on id ───────────────────────────────────────────────────
    before = len(df)
    df = df.drop_duplicates(subset="id")
    log.info("After id de-dup: %d rows (removed %d)", len(df), before - len(df))

    # ── Rename primary key ───────────────────────────────────────────────────
    df = df.rename(columns={"id": "violation_id"})

    # ── Drop columns that are 100% null (description, closed_datetime, etc.) ─
    always_null = [c for c in df.columns if df[c].isna().all()]
    log.info("Dropping 100%%-null columns: %s", always_null)
    df = df.drop(columns=always_null)

    # ── Parse violation labels ───────────────────────────────────────────────
    df["violation_labels"] = df["violation_type"].apply(_parse_label_string)
    df["n_labels"] = df["violation_labels"].apply(len)
    df["severity_weight"] = df["violation_labels"].apply(_compute_severity)

    # ── Timestamps ───────────────────────────────────────────────────────────
    df["created_datetime_utc"] = pd.to_datetime(df["created_datetime"], utc=True, format="mixed")
    df["created_datetime_ist"] = df["created_datetime_utc"] + pd.Timedelta(hours=IST_OFFSET_HOURS)
    df["created_date_ist"] = df["created_datetime_ist"].dt.date
    df["created_hour_ist"] = df["created_datetime_ist"].dt.hour
    df["created_dow"] = df["created_datetime_ist"].dt.dayofweek  # 0=Mon
    df["created_month"] = df["created_datetime_ist"].dt.month

    # ── Validation flag ───────────────────────────────────────────────────────
    df["is_validated"] = df["validation_status"].isin(VALID_STATUSES)

    # Sanity-check: report rejected %
    non_null_status = df["validation_status"].dropna()
    rejected_pct = (non_null_status.isin({"rejected", "duplicate"})).mean() * 100
    log.info(
        "validation_status — null: %.1f%%, rejected+duplicate: %.1f%% of non-null (expected ~28.7%%)",
        df["validation_status"].isna().mean() * 100,
        rejected_pct,
    )

    # ── Normalise junction_name ───────────────────────────────────────────────
    df["junction_name_norm"] = (
        df["junction_name"].fillna("Unknown").str.strip().str.title()
    )

    # ── Select and reorder final columns ─────────────────────────────────────
    cols = [
        "violation_id",
        "latitude",
        "longitude",
        "junction_name_norm",
        "police_station",
        "vehicle_number",
        "vehicle_type",
        "violation_labels",
        "n_labels",
        "severity_weight",
        "created_datetime_utc",
        "created_datetime_ist",
        "created_date_ist",
        "created_hour_ist",
        "created_dow",
        "created_month",
        "validation_status",
        "is_validated",
    ]
    df_clean = df[cols].copy()

    log.info("violations_clean: %d rows, %d columns", len(df_clean), df_clean.shape[1])
    assert len(df_clean) == 298450, f"Row count mismatch: {len(df_clean)} (expected 298450)"

    # ── Save to Parquet ───────────────────────────────────────────────────────
    # Convert list column to string for Parquet compatibility
    df_clean["violation_labels_str"] = df_clean["violation_labels"].apply(json.dumps)
    df_clean.to_parquet(out_parquet, index=False)
    log.info("Saved Parquet → %s", out_parquet)

    # ── Save to SQLite ────────────────────────────────────────────────────────
    df_sqlite = df_clean.drop(columns=["violation_labels"]).copy()
    df_sqlite["created_datetime_utc"] = df_sqlite["created_datetime_utc"].astype(str)
    df_sqlite["created_datetime_ist"] = df_sqlite["created_datetime_ist"].astype(str)
    df_sqlite["created_date_ist"] = df_sqlite["created_date_ist"].astype(str)
    conn = sqlite3.connect(SQLITE_DB)
    df_sqlite.to_sql("violations_clean", conn, if_exists="replace", index=False)
    conn.close()
    log.info("Saved SQLite → %s (table: violations_clean)", SQLITE_DB)

    return df_clean


if __name__ == "__main__":
    run_cleaning()
