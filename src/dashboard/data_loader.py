"""
Dashboard data loader — reads precomputed Parquet artifacts.
All heavy computation happens in the pipeline; this module only reads.
"""
from __future__ import annotations

import json
from functools import lru_cache

import pandas as pd
import streamlit as st

from src.config import (
    ALLOCATION_PARQUET,
    FORECAST_PARQUET,
    HOTSPOTS_PARQUET,
    JUNCTION_DAILY_PARQUET,
    PPI_PARQUET,
    TEMPORAL_PARQUET,
    VIOLATIONS_CLEAN_PARQUET,
)


@st.cache_data(ttl=3600)
def load_ppi() -> pd.DataFrame:
    df = pd.read_parquet(PPI_PARQUET)
    return df


@st.cache_data(ttl=3600)
def load_hotspots() -> pd.DataFrame:
    df = pd.read_parquet(HOTSPOTS_PARQUET)
    return df


@st.cache_data(ttl=3600)
def load_junction_daily() -> pd.DataFrame:
    df = pd.read_parquet(JUNCTION_DAILY_PARQUET)
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=3600)
def load_temporal() -> pd.DataFrame:
    return pd.read_parquet(TEMPORAL_PARQUET)


@st.cache_data(ttl=3600)
def load_forecast() -> pd.DataFrame:
    return pd.read_parquet(FORECAST_PARQUET)


@st.cache_data(ttl=3600)
def load_allocation() -> pd.DataFrame:
    return pd.read_parquet(ALLOCATION_PARQUET)


@st.cache_data(ttl=3600)
def load_violations_sample(n: int = 50_000) -> pd.DataFrame:
    """Load a sample of violations_clean for vehicle-mix analysis."""
    df = pd.read_parquet(
        VIOLATIONS_CLEAN_PARQUET,
        columns=["violation_id", "junction_name_norm", "vehicle_type",
                 "is_validated", "created_date_ist", "created_hour_ist",
                 "vehicle_number", "violation_labels_str"],
    )
    return df[df["is_validated"]].reset_index(drop=True)


def artifacts_exist() -> bool:
    """Return True only if all required artifacts have been generated."""
    return all(
        p.exists()
        for p in [PPI_PARQUET, HOTSPOTS_PARQUET, JUNCTION_DAILY_PARQUET,
                  TEMPORAL_PARQUET, FORECAST_PARQUET, ALLOCATION_PARQUET]
    )


@st.cache_data(ttl=3600)
def load_feature_importance() -> pd.DataFrame:
    """Load precomputed LightGBM feature importances."""
    from src.config import DATA_PROCESSED
    import pandas as pd
    path = DATA_PROCESSED / "feature_importances.parquet"
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame(columns=["feature", "importance"])
