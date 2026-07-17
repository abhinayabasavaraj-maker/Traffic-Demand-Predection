"""
Phase 3 — Forecasting
LightGBM (primary) + XGBoost (cross-check) + two naive baselines.
Train: Nov 2023 – Feb 2024  |  Validate: Mar 2024  |  Test: Apr 2024 (held-out, touched once)
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    DATA_PROCESSED,
    FORECAST_PARQUET,
    JUNCTION_DAILY_PARQUET,
    JUNCTION_PLACEHOLDER_NAMES,
    LAG_DAYS,
    LGBM_PARAMS,
    MIN_HISTORY_DAYS,
    MODEL_DIR,
    RANDOM_STATE,
    ROLLING_WINDOWS,
    SQLITE_DB,
    TEST_END,
    TEST_START,
    TOP_N_HOTSPOTS,
    TRAIN_END,
    VALIDATE_END,
    VALIDATE_START,
    XGB_PARAMS,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

try:
    import lightgbm as lgb
    LGBM_AVAILABLE = True
except ImportError:
    LGBM_AVAILABLE = False
    log.warning("lightgbm not installed — will use XGBoost only")

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    log.warning("xgboost not installed — will use LightGBM only")


def _make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build lag + rolling + calendar features. Operates on one junction's time series."""
    df = df.sort_values("date").copy()
    target = "n_violations_validated"

    for lag in LAG_DAYS:
        df[f"lag_{lag}"] = df[target].shift(lag)

    for win in ROLLING_WINDOWS:
        df[f"roll_{win}_mean"] = df[target].shift(1).rolling(win, min_periods=1).mean()
        df[f"roll_{win}_std"] = df[target].shift(1).rolling(win, min_periods=1).std().fillna(0)

    df["dow"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    # Simple holiday flag — major Indian national holidays in the dataset window
    holidays = pd.to_datetime([
        "2023-11-14", "2023-12-25", "2024-01-01", "2024-01-26",
        "2024-03-25", "2024-03-29",  # Holi, Good Friday
    ])
    df["is_holiday"] = df["date"].isin(holidays).astype(int)

    return df


def _build_panel(jd: pd.DataFrame, junctions: list[str]) -> pd.DataFrame:
    """Build a feature-engineered panel for all selected junctions."""
    frames = []
    for junc in junctions:
        sub = jd[jd["junction_name_norm"] == junc].copy()
        sub = _make_features(sub)
        frames.append(sub)
    return pd.concat(frames, ignore_index=True)


def _wape(actual: np.ndarray, predicted: np.ndarray) -> float:
    denom = np.abs(actual).sum()
    if denom == 0:
        return np.nan
    return float(np.abs(actual - predicted).sum() / denom * 100)


def run_forecast() -> pd.DataFrame:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    jd = pd.read_parquet(JUNCTION_DAILY_PARQUET)
    jd["date"] = pd.to_datetime(jd["date"])

    # ── Select top-N hotspots by total validated volume ──────────────────────
    vol = (
        jd.groupby("junction_name_norm")["n_violations_validated"]
        .sum()
        .sort_values(ascending=False)
    )

    # Exclude ALL placeholder junction names (single source of truth from config)
    # "No Junction" = 147,880 records (49.5% of dataset) with no junction field
    # "Unknown"     = 5 records where junction_name was null → coerced by clean.py
    # Neither is a real, addressable location.
    vol = vol[~vol.index.isin(JUNCTION_PLACEHOLDER_NAMES)]
    vol = vol[vol.index.notna()]

    # Filter for sufficient history
    history_counts = jd[jd["n_violations_validated"] > 0].groupby("junction_name_norm")["date"].nunique()
    qualified = history_counts[history_counts >= MIN_HISTORY_DAYS].index
    top_junctions = [j for j in vol.index if j in qualified][:TOP_N_HOTSPOTS]
    log.info("Forecasting for %d junctions (min %d days history)", len(top_junctions), MIN_HISTORY_DAYS)

    panel = _build_panel(jd, top_junctions)
    # Use a stable, sorted encoding for junction_id so "tomorrow" predictions use the same map
    junc_id_map = {j: i for i, j in enumerate(sorted(top_junctions))}
    panel["junction_id"] = panel["junction_name_norm"].map(junc_id_map).fillna(0).astype(int)

    feature_cols = (
        [f"lag_{l}" for l in LAG_DAYS]
        + [f"roll_{w}_mean" for w in ROLLING_WINDOWS]
        + [f"roll_{w}_std" for w in ROLLING_WINDOWS]
        + ["dow", "month", "is_weekend", "is_holiday", "junction_id"]
    )
    target_col = "n_violations_validated"

    panel = panel.dropna(subset=feature_cols)

    # ── Split ────────────────────────────────────────────────────────────────
    train = panel[panel["date"] <= TRAIN_END]
    val = panel[(panel["date"] >= VALIDATE_START) & (panel["date"] <= VALIDATE_END)]
    test = panel[(panel["date"] >= TEST_START) & (panel["date"] <= TEST_END)]

    log.info("Split sizes — train: %d, val: %d, test: %d", len(train), len(val), len(test))

    X_train, y_train = train[feature_cols], train[target_col]
    X_val, y_val = val[feature_cols], val[target_col]
    X_test, y_test = test[feature_cols], test[target_col]

    results = []

    # ── Naive baselines ──────────────────────────────────────────────────────
    def _baseline_yesterday(df_split: pd.DataFrame) -> np.ndarray:
        return df_split["lag_1"].fillna(df_split[target_col].mean()).values

    def _baseline_roll7(df_split: pd.DataFrame) -> np.ndarray:
        return df_split["roll_7_mean"].fillna(df_split[target_col].mean()).values

    # ── LightGBM ─────────────────────────────────────────────────────────────
    lgbm_model = None
    if LGBM_AVAILABLE:
        from lightgbm import LGBMRegressor
        lgbm_model = LGBMRegressor(**LGBM_PARAMS)
        lgbm_model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(period=-1)],
        )
        # Save model
        lgbm_model.booster_.save_model(str(MODEL_DIR / "lgbm_v1.txt"))
        log.info("LightGBM model saved.")
        
        # Save feature importances
        imp_df = pd.DataFrame({
            "feature": feature_cols,
            "importance": lgbm_model.feature_importances_
        }).sort_values("importance", ascending=False)
        imp_df.to_parquet(DATA_PROCESSED / "feature_importances.parquet", index=False)
        log.info("Saved feature importances to feature_importances.parquet")

    # ── XGBoost ──────────────────────────────────────────────────────────────
    xgb_model = None
    if XGB_AVAILABLE:
        from xgboost import XGBRegressor
        xgb_model = XGBRegressor(**XGB_PARAMS, early_stopping_rounds=50, eval_metric="mae")
        xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        xgb_model.save_model(str(MODEL_DIR / "xgb_v1.json"))
        log.info("XGBoost model saved.")

    # ── Evaluate on held-out TEST set (touched only once) ────────────────────
    log.info("=" * 60)
    log.info("HELD-OUT TEST SET RESULTS (Apr 2024) — FINAL")
    log.info("=" * 60)

    for split_name, split_df, X_sp, y_sp in [
        ("validate", val, X_val, y_val),
        ("test", test, X_test, y_test),
    ]:
        if len(split_df) == 0:
            log.warning("Split '%s' is empty — skipping evaluation.", split_name)
            continue

        pred_naive_y = _baseline_yesterday(split_df)
        pred_naive_r7 = _baseline_roll7(split_df)
        y_arr = y_sp.values

        for model_name, model in [("lightgbm_v1", lgbm_model), ("xgboost_v1", xgb_model)]:
            if model is None:
                continue
            preds = np.maximum(model.predict(X_sp), 0)

            mae = float(np.abs(y_arr - preds).mean())
            rmse = float(np.sqrt(((y_arr - preds) ** 2).mean()))
            wape = _wape(y_arr, preds)
            mae_naive_y = float(np.abs(y_arr - pred_naive_y).mean())
            mae_naive_r7 = float(np.abs(y_arr - pred_naive_r7).mean())

            log.info(
                "[%s | %s] MAE=%.2f  RMSE=%.2f  WAPE=%.1f%%  "
                "vs naive-yesterday MAE=%.2f  vs naive-roll7 MAE=%.2f  "
                "beat_yesterday=%s  beat_roll7=%s",
                split_name, model_name, mae, rmse, wape,
                mae_naive_y, mae_naive_r7,
                "YES" if mae < mae_naive_y else "NO",
                "YES" if mae < mae_naive_r7 else "NO",
            )

        # Append rows for each junction in this split
        for junc in top_junctions:
            junc_rows = split_df[split_df["junction_name_norm"] == junc]
            if len(junc_rows) == 0:
                continue
            jX = junc_rows[feature_cols]
            jy = junc_rows[target_col].values

            lgbm_pred = np.maximum(lgbm_model.predict(jX), 0) if lgbm_model else np.full(len(jX), np.nan)
            xgb_pred = np.maximum(xgb_model.predict(jX), 0) if xgb_model else np.full(len(jX), np.nan)
            naive_y_pred = _baseline_yesterday(junc_rows)
            naive_r7_pred = _baseline_roll7(junc_rows)

            for i, row in enumerate(junc_rows.itertuples()):
                results.append(
                    {
                        "hotspot_id": junc,
                        "forecast_date": str(row.date.date()),
                        "predicted_violations": float(lgbm_pred[i]) if lgbm_model else float(xgb_pred[i]),
                        "predicted_violations_xgb": float(xgb_pred[i]) if xgb_model else None,
                        "baseline_naive_predicted": float(naive_y_pred[i]),
                        "baseline_rolling7_predicted": float(naive_r7_pred[i]),
                        "actual_violations": float(jy[i]),
                        "model_name": "lightgbm_v1" if lgbm_model else "xgboost_v1",
                        "split": split_name,
                    }
                )

    # ── Build "tomorrow" forecasts (beyond test set — for the allocation sim) -
    last_date = jd["date"].max()
    tomorrow = last_date + pd.Timedelta(days=1)

    # Build junction_id map using the same panel encoding
    junc_id_map = {j: i for i, j in enumerate(sorted(top_junctions))}

    for junc in top_junctions:
        sub = jd[jd["junction_name_norm"] == junc].sort_values("date").copy()
        feat = _make_features(sub).tail(1).copy()
        feat["junction_id"] = junc_id_map.get(junc, 0)
        feat = feat.dropna(subset=feature_cols)
        if len(feat) == 0:
            continue
        lgbm_pred = float(np.maximum(lgbm_model.predict(feat[feature_cols]), 0)[0]) if lgbm_model else None
        xgb_pred_v = float(np.maximum(xgb_model.predict(feat[feature_cols]), 0)[0]) if xgb_model else None
        pred = lgbm_pred if lgbm_pred is not None else xgb_pred_v

        results.append(
            {
                "hotspot_id": junc,
                "forecast_date": str(tomorrow.date()),
                "predicted_violations": pred,
                "predicted_violations_xgb": xgb_pred_v,
                "baseline_naive_predicted": float(sub["n_violations_validated"].iloc[-1]),
                "baseline_rolling7_predicted": float(sub["n_violations_validated"].tail(7).mean()),
                "actual_violations": None,
                "model_name": "lightgbm_v1" if lgbm_model else "xgboost_v1",
                "split": "future",
            }
        )

    result_df = pd.DataFrame(results)

    # ── Assertion: no placeholder hotspot_ids in output ──────────────────────
    bad_ids = result_df[result_df["hotspot_id"].isin(JUNCTION_PLACEHOLDER_NAMES)]
    assert len(bad_ids) == 0, (
        f"BUG: placeholder hotspot_ids in forecast_results: "
        f"{bad_ids['hotspot_id'].unique().tolist()}"
    )
    log.info("Assertion passed: no placeholder hotspot_ids in forecast_results.")

    result_df.to_parquet(FORECAST_PARQUET, index=False)
    log.info("forecast_results: %d rows → %s", len(result_df), FORECAST_PARQUET)

    conn = sqlite3.connect(SQLITE_DB)
    result_df.to_sql("forecast_results", conn, if_exists="replace", index=False)
    conn.close()

    return result_df


if __name__ == "__main__":
    run_forecast()
