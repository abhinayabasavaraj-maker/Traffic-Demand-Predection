"""
Phase 2 — Hotspot Detection (DBSCAN on lat/lon)
Produces hotspots.parquet and the hotspots SQLite table.
"""
from __future__ import annotations

import json
import logging
import sqlite3

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from src.config import (
    DATA_PROCESSED,
    DBSCAN_EPS,
    DBSCAN_MIN_SAMPLES,
    HOTSPOTS_PARQUET,
    JUNCTION_PLACEHOLDER_NAMES,
    RANDOM_STATE,
    SQLITE_DB,
    VIOLATIONS_CLEAN_PARQUET,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)


def run_dbscan(
    eps: float = DBSCAN_EPS,
    min_samples: int = DBSCAN_MIN_SAMPLES,
) -> pd.DataFrame:
    """Run DBSCAN on validated violation lat/lon and build the hotspots table."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(VIOLATIONS_CLEAN_PARQUET)
    df_v = df[df["is_validated"]].copy()
    log.info("Running DBSCAN on %d validated records (eps=%.4f, min_samples=%d)", len(df_v), eps, min_samples)

    coords = df_v[["latitude", "longitude"]].values
    db = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1).fit(coords)
    df_v = df_v.copy()
    df_v["cluster_id"] = db.labels_

    n_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
    n_noise = (db.labels_ == -1).sum()
    log.info(
        "DBSCAN result: %d clusters, %d noise points (%.1f%% of validated)",
        n_clusters, n_noise, n_noise / len(df_v) * 100,
    )

    # ── Build hotspots table ─────────────────────────────────────────────────
    records = []
    clustered = df_v[df_v["cluster_id"] != -1]

    for cluster_id, grp in clustered.groupby("cluster_id"):
        centroid_lat = grp["latitude"].mean()
        centroid_lon = grp["longitude"].mean()

        # Dominant junction names — filter placeholders (from config, single source of truth)
        junc_counts = grp["junction_name_norm"].value_counts()
        junc_counts = junc_counts[~junc_counts.index.isin(JUNCTION_PLACEHOLDER_NAMES)]
        dominant_junctions = junc_counts.head(3).index.tolist()

        dominant_police_station = grp["police_station"].mode().iloc[0] if len(grp) > 0 else None

        # Fallback label hierarchy: real junction → police_station → coordinate
        if len(junc_counts) > 0:
            dominant_junction = junc_counts.index[0]
        elif dominant_police_station:
            dominant_junction = f"Near {dominant_police_station}"
        else:
            dominant_junction = f"Cluster near ({centroid_lat:.3f}, {centroid_lon:.3f})"

        records.append(
            {
                "cluster_id": int(cluster_id),
                "centroid_lat": round(centroid_lat, 6),
                "centroid_lon": round(centroid_lon, 6),
                "dominant_junction_name": dominant_junction,
                "dominant_junction_names": json.dumps(dominant_junctions),
                "dominant_police_station": dominant_police_station,
                "n_points": len(grp),
                "n_distinct_vehicles": grp["vehicle_number"].nunique(),
                "date_range_start": str(grp["created_date_ist"].min()),
                "date_range_end": str(grp["created_date_ist"].max()),
            }
        )

    hotspots = pd.DataFrame(records).sort_values("n_points", ascending=False).reset_index(drop=True)
    hotspots["rank"] = range(1, len(hotspots) + 1)

    hotspots.to_parquet(HOTSPOTS_PARQUET, index=False)
    log.info("hotspots: %d clusters → %s", len(hotspots), HOTSPOTS_PARQUET)

    conn = sqlite3.connect(SQLITE_DB)
    hotspots.to_sql("hotspots", conn, if_exists="replace", index=False)
    conn.close()

    # Log top-5 for manual spot-check
    log.info("Top-5 clusters by volume:")
    for _, row in hotspots.head(5).iterrows():
        log.info(
            "  Cluster %d | %s | %d pts | centre (%.4f, %.4f)",
            row["cluster_id"], row["dominant_junction_name"],
            row["n_points"], row["centroid_lat"], row["centroid_lon"],
        )

    return hotspots


if __name__ == "__main__":
    run_dbscan()
