"""
Phase 3 — Parking Pressure Index (PPI)
Computes a documented composite score per junction per trailing window.
Runs a ±10% weight sensitivity check and logs stability of top-15 ranking.
"""
from __future__ import annotations

import logging
import sqlite3

import numpy as np
import pandas as pd

from src.config import (
    DATA_PROCESSED,
    JUNCTION_PLACEHOLDER_NAMES,
    PPI_PARQUET,
    PPI_SENSITIVITY_DELTA,
    PPI_TIER_QUANTILES,
    PPI_WEIGHTS,
    PPI_WINDOW_DAYS,
    SQLITE_DB,
    JUNCTION_DAILY_PARQUET,
    EMERGING_SHORT_WINDOW_DAYS,
    EMERGING_LONG_WINDOW_DAYS,
    EMERGING_THRESHOLD_RATIO,
    EMERGING_MIN_DAILY_VIOLATIONS,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def _minmax_norm(s: pd.Series) -> pd.Series:
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series(0.5, index=s.index)
    return (s - mn) / (mx - mn)


def compute_ppi(
    jd: pd.DataFrame,
    weights: dict | None = None,
    window_days: int = PPI_WINDOW_DAYS,
) -> pd.DataFrame:
    """
    Compute PPI scores for all junctions over the trailing `window_days`
    ending at the last date in `jd`.
    """
    if weights is None:
        weights = PPI_WEIGHTS

    last_date = jd["date"].max()
    start_date = last_date - pd.Timedelta(days=window_days)
    window = jd[(jd["date"] >= start_date) & (jd["date"] <= last_date)].copy()

    # ── Exclude placeholder junction names ───────────────────────────────────
    # Single source of truth: JUNCTION_PLACEHOLDER_NAMES in config.py.
    # "No Junction" (147,880 records) and "Unknown" (5 records) are null-buckets
    # covering violations with no usable junction attribution — not real locations.
    window = window[~window["junction_name_norm"].isin(JUNCTION_PLACEHOLDER_NAMES)]
    window = window[window["junction_name_norm"].notna()]

    # ── Component computation ─────────────────────────────────────────────────
    grp = window.groupby("junction_name_norm")

    # 1. Violation frequency (validated violations / day in window)
    freq = grp["n_violations_validated"].sum() / window_days

    # 2. Severity (mean of daily mean_severity_weight)
    sev = grp["mean_severity_weight"].mean()

    # 3. Repeat-offender ratio = days with repeat vehicles / total days present
    #    (proxy since we don't have per-record repeat flag at this stage)
    repeat_ratio = grp["n_repeat_vehicles"].sum() / grp["n_violations_validated"].sum().replace(0, np.nan)
    repeat_ratio = repeat_ratio.fillna(0)

    # 4. Persistence = distinct days with ≥1 violation / window_days
    persistence = grp["date"].count() / window_days

    scores = pd.DataFrame(
        {
            "violation_frequency": freq,
            "severity_component": sev,
            "repeat_offender_ratio": repeat_ratio,
            "persistence": persistence,
        }
    ).reset_index()

    # ── Emerging Hotspot Detection ──────────────────────────────────────────
    jd_clean = jd[~jd["junction_name_norm"].isin(JUNCTION_PLACEHOLDER_NAMES)]
    short_start = last_date - pd.Timedelta(days=EMERGING_SHORT_WINDOW_DAYS)
    long_start = last_date - pd.Timedelta(days=EMERGING_SHORT_WINDOW_DAYS + EMERGING_LONG_WINDOW_DAYS)

    short_df = jd_clean[(jd_clean["date"] >= short_start) & (jd_clean["date"] <= last_date)]
    long_df = jd_clean[(jd_clean["date"] >= long_start) & (jd_clean["date"] < short_start)]

    short_mean = short_df.groupby("junction_name_norm")["n_violations_validated"].mean()
    long_mean = long_df.groupby("junction_name_norm")["n_violations_validated"].mean()

    # Compute velocity (ratio)
    velocity = short_mean / long_mean.replace(0, np.nan).fillna(0.1)
    velocity = velocity.fillna(1.0).round(3)

    vel_map = velocity.to_dict()
    short_mean_map = short_mean.to_dict()

    scores["trend_velocity"] = scores["junction_name_norm"].map(vel_map).fillna(1.0)
    scores["short_term_mean"] = scores["junction_name_norm"].map(short_mean_map).fillna(0.0)
    scores["is_emerging"] = (
        (scores["trend_velocity"] >= EMERGING_THRESHOLD_RATIO) &
        (scores["short_term_mean"] >= EMERGING_MIN_DAILY_VIOLATIONS)
    ).astype(int)

    # ── Normalisation ─────────────────────────────────────────────────────────
    scores["freq_norm"] = _minmax_norm(scores["violation_frequency"])
    scores["sev_norm"] = _minmax_norm(scores["severity_component"])
    scores["repeat_norm"] = _minmax_norm(scores["repeat_offender_ratio"])
    scores["persist_norm"] = _minmax_norm(scores["persistence"])

    w = weights
    scores["ppi_raw"] = (
        w["frequency"] * scores["freq_norm"]
        + w["severity"] * scores["sev_norm"]
        + w["repeat"] * scores["repeat_norm"]
        + w["persistence"] * scores["persist_norm"]
    )
    scores["ppi_score"] = (scores["ppi_raw"] * 100).round(2)

    # ── Tier assignment (quantile-based) ──────────────────────────────────────
    q_critical = scores["ppi_score"].quantile(PPI_TIER_QUANTILES["Critical"])
    q_high = scores["ppi_score"].quantile(PPI_TIER_QUANTILES["High"])
    q_medium = scores["ppi_score"].quantile(PPI_TIER_QUANTILES["Medium"])

    def _tier(v: float) -> str:
        if v >= q_critical:
            return "Critical"
        if v >= q_high:
            return "High"
        if v >= q_medium:
            return "Medium"
        return "Low"

    scores["ppi_tier"] = scores["ppi_score"].apply(_tier)
    scores["window_start"] = start_date.date()
    scores["window_end"] = last_date.date()

    # Add police_station (dominant for each junction)
    station_map = (
        jd.groupby("junction_name_norm")["police_station"]
        .agg(lambda x: x.mode().iloc[0] if len(x) > 0 else "Unknown")
        .reset_index()
    )
    scores = scores.merge(station_map, on="junction_name_norm", how="left")

    return scores.sort_values("ppi_score", ascending=False).reset_index(drop=True)


def _sensitivity_check(jd: pd.DataFrame, base_scores: pd.DataFrame) -> bool:
    """
    Perturb each weight by ±10% (renormalized) and check whether the top-15
    ranking is stable. Returns True if stable.
    """
    top15_base = set(base_scores.head(15)["junction_name_norm"])
    delta = PPI_SENSITIVITY_DELTA
    stable = True

    for key in PPI_WEIGHTS:
        for sign in [+1, -1]:
            perturbed = {k: v for k, v in PPI_WEIGHTS.items()}
            perturbed[key] *= 1 + sign * delta
            total = sum(perturbed.values())
            perturbed = {k: v / total for k, v in perturbed.items()}

            alt = compute_ppi(jd, weights=perturbed)
            top15_alt = set(alt.head(15)["junction_name_norm"])
            overlap = len(top15_base & top15_alt)

            log.info(
                "Sensitivity: %s %+.0f%% → top-15 overlap = %d/15 (%s)",
                key, sign * delta * 100, overlap,
                "STABLE" if overlap >= 13 else "UNSTABLE",
            )
            if overlap < 13:
                stable = False

    return stable


def run_ppi() -> pd.DataFrame:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    jd = pd.read_parquet(JUNCTION_DAILY_PARQUET)
    jd["date"] = pd.to_datetime(jd["date"])

    log.info("Computing PPI over trailing %d-day window …", PPI_WINDOW_DAYS)
    scores = compute_ppi(jd)

    # ── Sensitivity check ──────────────────────────────────────────────────
    log.info("Running ±%.0f%% weight sensitivity check …", PPI_SENSITIVITY_DELTA * 100)
    stable = _sensitivity_check(jd, scores)
    log.info("Top-15 PPI ranking sensitivity: %s", "STABLE" if stable else "UNSTABLE — see Risk Log")

    # ── Save ───────────────────────────────────────────────────────────────
    out = scores[[
        "junction_name_norm", "police_station",
        "violation_frequency", "severity_component", "repeat_offender_ratio", "persistence",
        "freq_norm", "sev_norm", "repeat_norm", "persist_norm",
        "ppi_score", "ppi_tier",
        "trend_velocity", "is_emerging",
        "window_start", "window_end",
    ]]
    # ── Assertion: no placeholder names in the output ────────────────────────
    bad_rows = out[
        out["junction_name_norm"].isin(JUNCTION_PLACEHOLDER_NAMES) |
        out["junction_name_norm"].isna()
    ]
    assert len(bad_rows) == 0, (
        f"BUG: placeholder junction names found in PPI output: "
        f"{bad_rows['junction_name_norm'].tolist()}"
    )
    assert "Unknown" not in out["junction_name_norm"].values, "Unknown leaked into ppi_scores!"
    assert "No Junction" not in out["junction_name_norm"].values, "No Junction leaked into ppi_scores!"
    log.info("Assertions passed: no placeholder junction names in PPI output.")

    out.to_parquet(PPI_PARQUET, index=False)
    log.info("ppi_scores: %d junctions → %s", len(out), PPI_PARQUET)

    conn = sqlite3.connect(SQLITE_DB)
    out_s = out.copy()
    out_s["window_start"] = out_s["window_start"].astype(str)
    out_s["window_end"] = out_s["window_end"].astype(str)
    out_s.to_sql("ppi_scores", conn, if_exists="replace", index=False)
    conn.close()

    # Log top-10
    log.info("Top-10 junctions by PPI:")
    for _, row in out.head(10).iterrows():
        log.info(
            "  [%s] %s | PPI=%.1f | freq=%.2f/day",
            row["ppi_tier"], row["junction_name_norm"],
            row["ppi_score"], row["violation_frequency"],
        )

    return out


if __name__ == "__main__":
    run_ppi()
