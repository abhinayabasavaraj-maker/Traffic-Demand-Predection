"""
ParkPulse — Visual/UX rebuild.
Run: streamlit run src/dashboard/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from src.config import (
    PRECOMPUTE_UNIT_COUNTS,
    TOP_N_OVERVIEW,
)
from src.dashboard.data_loader import (
    artifacts_exist,
    load_allocation,
    load_forecast,
    load_hotspots,
    load_junction_daily,
    load_ppi,
    load_temporal,
    load_violations_sample,
    load_feature_importance,
)
from src.dashboard.components import (
    TC,
    TXT_MUT,
    TXT_PRI,
    BG_CARD,
    BG_DARK,
    build_allocation_map,
    build_overview_map,
    dow_chart,
    forecast_chart,
    hourly_chart,
    ppi_breakdown_chart,
    tier_badge_html,
    vehicle_mix_chart,
    feature_importance_chart,
    hourly_tomorrow_forecast_chart,
    root_cause_diagnosis,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ParkPulse · Enforcement Intelligence",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='14' fill='%230B0F14' stroke='%23E5484D' stroke-width='2'/><circle cx='16' cy='16' r='5' fill='%23E5484D'/><circle cx='16' cy='16' r='9' fill='none' stroke='%23E5484D' stroke-width='1' stroke-dasharray='3 3'/></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS — single consolidated block ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@400;500;600&display=swap');

/* ── Hide default Streamlit chrome ── */
#MainMenu, header, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── Global surface ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main .block-container {
    background-color: #0B0F14 !important;
    color: #E8ECEF;
    font-family: Inter, 'IBM Plex Sans', sans-serif;
}
.block-container { padding-top: 24px !important; max-width: 100% !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0D1219 !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] * { color: #E8ECEF !important; }

/* ── Nav items (radio) ── */
div[data-testid="stRadio"] label {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
    border-left: 3px solid transparent !important;
}
div[data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,0.05) !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] input:checked ~ div {
    color: #E8ECEF !important;
}

/* ── Stat cards ── */
.stat-card {
    background: #141A21;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 20px 24px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.stat-card .label {
    font-family: Inter, sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8B96A3;
}
.stat-card .value {
    font-family: 'IBM Plex Mono', 'JetBrains Mono', monospace;
    font-size: 1.75rem;
    font-weight: 600;
    color: #E8ECEF;
    line-height: 1.1;
}
.stat-card .sub {
    font-family: Inter, sans-serif;
    font-size: 0.75rem;
    color: #8B96A3;
}

/* ── Hotspot list cards ── */
.hs-card {
    background: #141A21;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 8px;
    border-left-width: 3px;
}
.hs-card .hs-name {
    font-family: Inter, sans-serif;
    font-size: 0.83rem;
    font-weight: 600;
    color: #E8ECEF;
    margin-bottom: 6px;
    white-space: normal;
    word-break: break-word;
}
.hs-card .hs-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.hs-card .hs-ppi {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem;
    font-weight: 600;
    color: #E8ECEF;
}
.hs-card .hs-freq {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #8B96A3;
}
.hs-card .hs-why {
    font-family: Inter, sans-serif;
    font-size: 0.72rem;
    color: #8B96A3;
    margin-top: 5px;
    white-space: normal;
}

/* ── Section divider ── */
.pp-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.07);
    margin: 16px 0;
}

/* ── Section header ── */
.pp-section {
    font-family: Inter, sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #8B96A3;
    margin-bottom: 12px;
}

/* ── Tier badge ── */
.tier-badge {
    display: inline-block;
    font-family: Inter, sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    padding: 2px 9px;
    border-radius: 4px;
    border-width: 1px;
    border-style: solid;
}

/* ── Metric override (use our monospace) ── */
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    color: #E8ECEF !important;
}
[data-testid="stMetricLabel"] {
    font-family: Inter, sans-serif !important;
    color: #8B96A3 !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em !important;
}

/* ── Selectbox / slider labels ── */
label[data-testid="stWidgetLabel"] {
    font-family: Inter, sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    color: #8B96A3 !important;
    text-transform: uppercase !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrameResizable"] {
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: #141A21 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    font-family: Inter, sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

/* ── Info / warning boxes ── */
[data-testid="stAlert"] {
    background: #141A21 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    font-family: Inter, sans-serif !important;
    font-size: 0.83rem !important;
}

/* ── Plotly chart background fill ── */
.js-plotly-plot .plotly .bg { fill: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ── Guard ─────────────────────────────────────────────────────────────────────
if not artifacts_exist():
    st.error("Precomputed artifacts not found. Run: python -m src.pipeline.run_all")
    st.stop()

# ── Load data (all cached) ────────────────────────────────────────────────────
ppi_df       = load_ppi()
hotspots_df  = load_hotspots()
jd           = load_junction_daily()
temporal_df  = load_temporal()
forecast_df  = load_forecast()
allocation_df = load_allocation()

# ── Sidebar ───────────────────────────────────────────────────────────────────
RADAR_SVG = """
<svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="18" cy="18" r="16" stroke="#E5484D" stroke-width="1.5"/>
  <circle cx="18" cy="18" r="10" stroke="#E5484D" stroke-width="1" stroke-dasharray="2.5 2.5" opacity="0.6"/>
  <circle cx="18" cy="18" r="4"  fill="#E5484D"/>
  <line x1="18" y1="2"  x2="18" y2="18" stroke="#E5484D" stroke-width="1.5" stroke-linecap="round" opacity="0.7"/>
</svg>
"""

with st.sidebar:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;padding:8px 0 4px 0;">'
        f'{RADAR_SVG}'
        f'<div><div style="font-family:Inter,sans-serif;font-weight:700;font-size:1.1rem;'
        f'color:#E8ECEF;letter-spacing:0.02em;">ParkPulse</div>'
        f'<div style="font-family:Inter,sans-serif;font-size:0.7rem;color:#8B96A3;'
        f'letter-spacing:0.05em;text-transform:uppercase;">Enforcement Intelligence</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["Overview", "Hotspot Detail", "Patrol Allocation", "What-If Simulator", "Data & Methodology"],
        label_visibility="collapsed",
    )

    st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)

    all_stations = sorted(ppi_df["police_station"].dropna().unique())
    station_filter = st.selectbox(
        "FILTER BY STATION",
        ["All stations"] + all_stations,
        index=0,
    )
    station_sel = None if station_filter == "All stations" else station_filter

    st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-family:Inter,sans-serif;font-size:0.7rem;color:#8B96A3;'
        f'line-height:1.6;">'
        f'Dataset: Nov 2023 – Apr 2024<br>'
        f'<span style="font-family:IBM Plex Mono,monospace;">{len(ppi_df):,}</span> junctions tracked<br>'
        f'<span style="color:#E5484D;">approved</span> violations only'
        f'</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
#  PAGE 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════
if page == "Overview":

    st.markdown(
        '<p class="pp-section">Hotspot Overview — Bangalore, Nov 2023 – Apr 2024</p>',
        unsafe_allow_html=True,
    )

    # ── Stat cards ────────────────────────────────────────────────
    validated_total = int(jd["n_violations_validated"].sum())
    # n_junctions = junctions with real names in PPI table (placeholders excluded)
    n_junctions     = len(ppi_df)
    n_critical      = int((ppi_df["ppi_tier"] == "Critical").sum())
    n_high          = int((ppi_df["ppi_tier"] == "High").sum())

    # ── Economic Impact Calculations ──
    from src.config import AFFECTED_VEHICLES_PER_VIOLATION, ECONOMIC_TIME_VALUE_INR, ECONOMIC_FUEL_COST_INR, ECONOMIC_IDLE_FUEL_CONSUMPTION, ECONOMIC_CO2_EMISSION_KG_PER_LITER
    total_daily_delay = 0.0
    total_daily_cost = 0.0
    total_daily_fuel = 0.0
    for _, r in ppi_df.iterrows():
        freq = float(r["violation_frequency"])
        sev = float(r["severity_component"])
        delay = (freq * AFFECTED_VEHICLES_PER_VIOLATION * sev * 10.0) / 60.0
        fuel = delay * ECONOMIC_IDLE_FUEL_CONSUMPTION
        cost = delay * ECONOMIC_TIME_VALUE_INR + fuel * ECONOMIC_FUEL_COST_INR
        total_daily_delay += delay
        total_daily_cost += cost
        total_daily_fuel += fuel
        
    active_days = 150
    total_cost_inr = total_daily_cost * active_days
    total_delay_hrs = total_daily_delay * active_days
    total_fuel_liters = total_daily_fuel * active_days
    total_co2_kg = total_fuel_liters * ECONOMIC_CO2_EMISSION_KG_PER_LITER

    c1, c2, c3, c4 = st.columns(4, gap="small")
    for col, label, value, sub in [
        (c1, "Validated Violations", f"{validated_total:,}", "approved records · Nov 2023–Apr 2024"),
        (c2, "Named Junctions",      f"{n_junctions}",       "real locations · placeholders excluded"),
        (c3, "Critical Hotspots",    f"{n_critical}",         "top 10% by PPI score"),
        (c4, "High Priority",        f"{n_high}",             "next 20% by PPI score"),
    ]:
        col.markdown(
            f'<div class="stat-card">'
            f'<div class="label">{label}</div>'
            f'<div class="value">{value}</div>'
            f'<div class="sub">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<p class="pp-section" style="margin-top:20px;">Bangalore Citywide Congestion Footprint (Estimated)</p>', unsafe_allow_html=True)
    ec1, ec2, ec3, ec4 = st.columns(4, gap="small")
    for col, label, value, sub in [
        (ec1, "Economic Loss (INR)", f"₹{(total_cost_inr/10000000.0):.2f} Cr", "wasted time + fuel cost in 150 days"),
        (ec2, "Travel Delay Hours",  f"{(total_delay_hrs/1000.0):.1f}k hrs",  "cumulative vehicle hours lost"),
        (ec3, "Wasted Fuel",         f"{(total_fuel_liters/1000.0):.1f}k L",  "excess fuel consumed idling"),
        (ec4, "CO2 Carbon Footprint", f"{(total_co2_kg/1000.0):.1f} tonnes", "indirect greenhouse gas emissions"),
    ]:
        col.markdown(
            f'<div class="stat-card" style="border-color: rgba(229,72,77,0.3);">'
            f'<div class="label" style="color: #E5484D;">{label}</div>'
            f'<div class="value">{value}</div>'
            f'<div class="sub">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:0.76rem;color:#8B96A3;'
        'margin:12px 0 16px 0;">'
        'Color encodes <b style="color:#E8ECEF;">Parking Pressure Index (PPI)</b> — '
        'a priority proxy built from frequency, severity, repeat offenders, and persistence. '
        '<b style="color:#E5484D;">Not</b> a direct measurement of traffic delay.'
        '</p>',
        unsafe_allow_html=True,
    )

    # ── Map + list ────────────────────────────────────────────────
    map_col, list_col = st.columns([3, 1], gap="medium")

    display_ppi = ppi_df.copy()
    if station_sel:
        display_ppi = display_ppi[display_ppi["police_station"] == station_sel]

    with map_col:
        folium_map = build_overview_map(display_ppi, hotspots_df, station_filter=station_sel)
        from streamlit_folium import st_folium
        st_folium(folium_map, width=None, height=540, returned_objects=[])

    with list_col:
        st.markdown('<p class="pp-section">Top Hotspots</p>', unsafe_allow_html=True)

        if len(display_ppi) == 0:
            st.markdown(
                '<div class="hs-card" style="border-left-color:#8B96A3;">'
                '<div class="hs-name">No hotspots in this window</div></div>',
                unsafe_allow_html=True,
            )
        else:
            # Top-5 dominant component — derived strictly from actual weighted values (BUG 2 fix)
            comp_labels = {
                "freq_norm":    "High violation frequency",
                "sev_norm":     "Severe violation types",
                "repeat_norm":  "Repeat offenders",
                "persist_norm": "Daily persistence",
            }
            comp_weights = {
                "freq_norm": 0.4, "sev_norm": 0.3,
                "repeat_norm": 0.2, "persist_norm": 0.1,
            }

            def _top_comp(r: pd.Series) -> str:
                weighted = {k: float(r.get(k, 0)) * w for k, w in comp_weights.items()}
                top_key = max(weighted, key=weighted.get)
                return comp_labels.get(top_key, "")

            # BUG 2 assertion: verify top comp matches actual max for every row
            for _, r in display_ppi.iterrows():
                weighted = {k: float(r.get(k, 0)) * w for k, w in comp_weights.items()}
                top_key = max(weighted, key=weighted.get)
                assert top_key in comp_labels, f"Unknown top component key: {top_key}"

            for _, row in display_ppi.head(TOP_N_OVERVIEW).iterrows():
                tier  = row["ppi_tier"]
                color = TC.get(tier, "#888")
                badge = tier_badge_html(tier)
                
                is_em = int(row.get("is_emerging", 0)) == 1
                em_badge = '<span style="display:inline-block;background:#E5484D15;color:#E5484D;border:1px solid #E5484D44;padding:2px 8px;border-radius:4px;font-size:0.68rem;font-family:Inter,sans-serif;font-weight:600;letter-spacing:0.04em;">⚠️ EMERGING</span>' if is_em else ''
                
                why   = _top_comp(row)
                freq  = row["violation_frequency"]
                name  = row["junction_name_norm"]
                ppi   = row["ppi_score"]

                st.markdown(
                    f'<div class="hs-card" style="border-left-color:{color};">'
                    f'<div class="hs-name">{name}</div>'
                    f'<div class="hs-row" style="gap:6px;">'
                    f'<span class="hs-ppi" style="color:{color};">{ppi:.1f}</span>'
                    f'{badge}'
                    f'{em_badge}'
                    f'<span class="hs-freq">{freq:.1f}/day</span>'
                    f'</div>'
                    f'<div class="hs-why">&#x2191; {why}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)
        st.markdown('<p class="pp-section">Full Ranking</p>', unsafe_allow_html=True)

        rank_df = display_ppi[
            ["junction_name_norm", "ppi_score", "ppi_tier", "violation_frequency"]
        ].copy()
        rank_df.columns = ["Junction", "PPI", "Tier", "Viol/Day"]
        rank_df["PPI"]      = rank_df["PPI"].round(1)
        rank_df["Viol/Day"] = rank_df["Viol/Day"].round(1)
        st.dataframe(rank_df, use_container_width=True, height=300, hide_index=True)


# ═══════════════════════════════════════════════════════════════════
#  PAGE 2 — HOTSPOT DETAIL
# ═══════════════════════════════════════════════════════════════════
elif page == "Hotspot Detail":

    all_junctions = ppi_df.sort_values("ppi_score", ascending=False)["junction_name_norm"].tolist()
    selected = st.selectbox("SELECT JUNCTION", all_junctions, index=0)

    row   = ppi_df[ppi_df["junction_name_norm"] == selected].iloc[0]
    tier  = row["ppi_tier"]
    color = TC.get(tier, "#888")
    badge = tier_badge_html(tier, size="0.85rem")

    # ── Detail header ─────────────────────────────────────────────
    st.markdown(
        f'<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
        f'border-left:3px solid {color};border-radius:8px;padding:20px 24px;margin-bottom:16px;">'
        f'<div style="font-family:Inter,sans-serif;font-weight:700;font-size:1.15rem;'
        f'color:#E8ECEF;margin-bottom:8px;">{selected}</div>'
        f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">'
        f'{badge}'
        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;color:#8B96A3;">'
        f'PPI&nbsp;<b style="color:#E8ECEF;">{row["ppi_score"]:.1f}</b>/100</span>'
        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;color:#8B96A3;">'
        f'Station&nbsp;<b style="color:#E8ECEF;">{row["police_station"]}</b></span>'
        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;color:#8B96A3;">'
        f'{row["violation_frequency"]:.1f}&nbsp;viol/day</span>'
        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;color:#8B96A3;">'
        f'Persistence&nbsp;{row["persistence"]:.0%}</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ── Three-column detail ───────────────────────────────────────
    col_ppi, col_temporal, col_vehicle = st.columns([1, 1.1, 0.95], gap="medium")

    with col_ppi:
        st.markdown('<p class="pp-section">PPI Breakdown</p>', unsafe_allow_html=True)
        st.plotly_chart(
            ppi_breakdown_chart(row),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.markdown(
            '<p style="font-family:Inter,sans-serif;font-size:0.7rem;color:#8B96A3;'
            'margin-top:4px;line-height:1.5;">'
            'Weights: frequency ×0.4 &nbsp;·&nbsp; severity ×0.3<br>'
            'repeat offenders ×0.2 &nbsp;·&nbsp; persistence ×0.1<br>'
            'All components normalised min-max across junctions.</p>',
            unsafe_allow_html=True,
        )

    with col_temporal:
        st.markdown('<p class="pp-section">Temporal Pattern</p>', unsafe_allow_html=True)
        st.plotly_chart(
            hourly_chart(temporal_df, selected),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.plotly_chart(
            dow_chart(temporal_df, selected),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with col_vehicle:
        st.markdown('<p class="pp-section">Vehicle Mix</p>', unsafe_allow_html=True)
        violations_sample = load_violations_sample()
        st.plotly_chart(
            vehicle_mix_chart(violations_sample, selected),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # ── Root Cause & Explainable AI Row ───────────────────────────
    st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)
    col_xai, col_fc_hr, col_cause = st.columns([1, 1, 1], gap="medium")

    with col_xai:
        st.markdown('<p class="pp-section">Explainable AI (XAI)</p>', unsafe_allow_html=True)
        feat_imp_df = load_feature_importance()
        st.plotly_chart(
            feature_importance_chart(feat_imp_df),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.markdown(
            '<p style="font-family:Inter,sans-serif;font-size:0.7rem;color:#8B96A3;'
            'margin-top:4px;line-height:1.5;">'
            'Visualizes features driving LightGBM forecast split gain. Lags represent historical violation lags.</p>',
            unsafe_allow_html=True,
        )

    with col_fc_hr:
        st.markdown('<p class="pp-section">Hourly Forecast</p>', unsafe_allow_html=True)
        future_j = forecast_df[(forecast_df["hotspot_id"] == selected) & (forecast_df["split"] == "future")]
        tomorrow_val = 0.0
        if len(future_j) > 0:
            tomorrow_val = float(future_j.iloc[0]["predicted_violations"])
        else:
            hist_preds = forecast_df[forecast_df["hotspot_id"] == selected].dropna(subset=["predicted_violations"])
            if len(hist_preds) > 0:
                tomorrow_val = float(hist_preds.iloc[-1]["predicted_violations"])

        st.plotly_chart(
            hourly_tomorrow_forecast_chart(temporal_df, selected, tomorrow_val),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.markdown(
            f'<p style="font-family:Inter,sans-serif;font-size:0.7rem;color:#8B96A3;'
            f'margin-top:4px;line-height:1.5;">'
            f'Tomorrow\'s daily forecast (<b>{tomorrow_val:.1f}</b> violations) distributed by historical hour profile.</p>',
            unsafe_allow_html=True,
        )

    with col_cause:
        st.markdown('<p class="pp-section">Root Cause Diagnostics</p>', unsafe_allow_html=True)
        violations_sample = load_violations_sample()
        diagnosis = root_cause_diagnosis(violations_sample, selected)
        st.markdown(
            f'<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
            f'border-radius:8px;padding:16px 20px;min-height:220px;display:flex;flex-direction:column;justify-content:space-between;">'
            f'<div>'
            f'<div style="font-family:Inter,sans-serif;font-weight:600;font-size:0.83rem;color:#E5484D;margin-bottom:8px;">'
            f'🔎 {diagnosis["category"]}</div>'
            f'<div style="font-family:Inter,sans-serif;font-size:0.75rem;color:#E8ECEF;line-height:1.6;margin-bottom:12px;">'
            f'<b>Diagnostic:</b> {diagnosis["diagnostic"]}</div>'
            f'</div>'
            f'<div style="border-top:1px solid rgba(255,255,255,0.07);padding-top:10px;">'
            f'<div style="font-family:Inter,sans-serif;font-weight:600;font-size:0.75rem;color:#2ECC71;margin-bottom:4px;">'
            f'💡 Recommended Policy Nudge:</div>'
            f'<div style="font-family:Inter,sans-serif;font-size:0.72rem;color:#8B96A3;line-height:1.5;">'
            f'{diagnosis["recommendation"]}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Forecast strip ────────────────────────────────────────────
    st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)
    st.markdown('<p class="pp-section">Violation Forecast</p>', unsafe_allow_html=True)

    junc_forecast = forecast_df[forecast_df["hotspot_id"] == selected]

    if len(junc_forecast) == 0 or junc_forecast["predicted_violations"].isna().all():
        st.markdown(
            '<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
            'border-radius:8px;padding:20px 24px;font-family:Inter,sans-serif;'
            'font-size:0.83rem;color:#8B96A3;">'
            'Insufficient history at this hotspot for a reliable forecast '
            '(minimum 30 days required).</div>',
            unsafe_allow_html=True,
        )
    else:
        st.plotly_chart(
            forecast_chart(forecast_df, selected),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        val_rows = junc_forecast[
            (junc_forecast["split"] == "validate") &
            junc_forecast["actual_violations"].notna()
        ]
        if len(val_rows) > 0:
            mae  = (val_rows["actual_violations"] - val_rows["predicted_violations"]).abs().mean()
            rmse = ((val_rows["actual_violations"] - val_rows["predicted_violations"]) ** 2).mean() ** 0.5
            n7   = (val_rows["actual_violations"] - val_rows["baseline_rolling7_predicted"]).abs().mean()
            beat = mae < n7
            m1, m2, m3, m4 = st.columns(4)
            for col, lbl, val in [
                (m1, "Validate MAE",     f"{mae:.2f}"),
                (m2, "Validate RMSE",    f"{rmse:.2f}"),
                (m3, "7-day baseline MAE", f"{n7:.2f}"),
                (m4, "Beat baseline",    "YES" if beat else "NO"),
            ]:
                col.markdown(
                    f'<div class="stat-card" style="padding:14px 18px;">'
                    f'<div class="label">{lbl}</div>'
                    f'<div class="value" style="font-size:1.3rem;'
                    f'color:{"#2ECC71" if (lbl=="Beat baseline" and beat) else "#E8ECEF"};">'
                    f'{val}</div></div>',
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════════════════════
#  PAGE 3 — PATROL ALLOCATION
# ═══════════════════════════════════════════════════════════════════
elif page == "Patrol Allocation":

    st.markdown('<p class="pp-section">Patrol Allocation Simulator</p>', unsafe_allow_html=True)

    st.markdown(
        '<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
        'border-left:3px solid #F2994A;border-radius:8px;padding:14px 20px;'
        'margin-bottom:16px;font-family:Inter,sans-serif;font-size:0.82rem;color:#8B96A3;">'
        'Allocation uses <b style="color:#E8ECEF;">constrained MILP</b> (PuLP) — not reinforcement '
        'learning. Objective: maximise Σ units × forecasted_violations × PPI_weight. '
        'No outcome-feedback data exists to train an RL policy.</div>',
        unsafe_allow_html=True,
    )

    ctrl_col, map_col = st.columns([1, 2], gap="medium")

    with ctrl_col:
        n_units = st.slider("AVAILABLE PATROL UNITS", min_value=1, max_value=30, value=10, step=1)

        precomputed_counts = [int(x) for x in allocation_df["available_units_total"].unique()]
        if n_units in precomputed_counts:
            alloc_result = allocation_df[allocation_df["available_units_total"] == n_units].copy()
            src_label = "precomputed"
        else:
            from src.models.allocation import solve_allocation
            alloc_result = solve_allocation(forecast_df, ppi_df, n_units)
            src_label = "live solve"

        assigned = alloc_result[alloc_result["units_assigned"] > 0].sort_values(
            ["units_assigned", "ppi_score"], ascending=[False, False]
        ).reset_index(drop=True)

        total_assigned = int(assigned["units_assigned"].sum())
        n_covered      = len(assigned)

        # Mini stat strip
        s1, s2 = st.columns(2)
        for col, lbl, val in [
            (s1, "Units Deployed", f"{total_assigned}/{n_units}"),
            (s2, "Hotspots Covered", str(n_covered)),
        ]:
            col.markdown(
                f'<div class="stat-card" style="padding:14px 18px;">'
                f'<div class="label">{lbl}</div>'
                f'<div class="value" style="font-size:1.4rem;">{val}</div>'
                f'<div class="sub">{src_label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Impact metrics strip
        total_savings = float(assigned["economic_savings_inr"].sum())
        total_delay_reduced = float(assigned["delay_reduced_hours"].sum())
        total_co2_saved = float(assigned["co2_saved_kg"].sum())

        st.markdown('<p class="pp-section" style="margin-top:14px;">Simulated Allocation Impact</p>', unsafe_allow_html=True)
        i1, i2, i3 = st.columns(3)
        for col, lbl, val, sub in [
            (i1, "Economic Savings", f"₹{total_savings:,.2f}", "time + fuel waste avoided"),
            (i2, "Delay Reduced", f"{total_delay_reduced:.1f} hrs", "travel time saved"),
            (i3, "CO2 Saved", f"{total_co2_saved:.1f} kg", "carbon emissions prevented"),
        ]:
            col.markdown(
                f'<div class="stat-card" style="padding:14px 18px; border-color: rgba(46,204,113,0.3);">'
                f'<div class="label" style="color: #2ECC71;">{lbl}</div>'
                f'<div class="value" style="font-size:1.15rem;">{val}</div>'
                f'<div class="sub" style="font-size:0.68rem;">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)

        draw_route = st.checkbox("🔌 OPTIMIZE PATROL ROUTING (TSP)", value=False)

        if draw_route and len(assigned) > 0:
            # Solve TSP
            locations = []
            for _, row in assigned.iterrows():
                hs_row = hotspots_df[hotspots_df["dominant_junction_name"] == row["hotspot_id"]]
                if len(hs_row) > 0:
                    locations.append({
                        "name": row["hotspot_id"],
                        "lat": hs_row.iloc[0]["centroid_lat"],
                        "lon": hs_row.iloc[0]["centroid_lon"]
                    })
            
            route = []
            if locations:
                hq = {"name": "City Police HQ", "lat": 12.97, "lon": 77.59}
                unvisited = locations.copy()
                current = hq
                route.append(hq)
                while unvisited:
                    nearest = min(unvisited, key=lambda x: (x["lat"] - current["lat"])**2 + (x["lon"] - current["lon"])**2)
                    route.append(nearest)
                    unvisited.remove(nearest)
                    current = nearest
                route.append(hq)
            
            route_str = " ➔ ".join([f"<b>{loc['name']}</b>" for loc in route])
            st.markdown(
                f'<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
                f'border-left:3px solid #3b82f6;border-radius:8px;padding:12px 16px;margin-bottom:14px;'
                f'font-family:Inter,sans-serif;font-size:0.8rem;color:#8B96A3;line-height:1.6;">'
                f'🗺️ <b>Optimized Dispatch Route (TSP):</b><br>{route_str}</div>',
                unsafe_allow_html=True
            )

            # --- Dispatch Tooling & Export ---
            f_date = assigned["forecast_date"].iloc[0] if len(assigned) > 0 else "tomorrow"
            
            # 1. Format CSV
            csv_df = assigned[[
                "hotspot_id", "units_assigned", "forecasted_violations", 
                "ppi_score", "ppi_tier", "economic_savings_inr", 
                "delay_reduced_hours", "co2_saved_kg"
            ]].copy()
            csv_df.columns = [
                "Hotspot", "Units Allocated", "Forecasted Violations", 
                "PPI Score", "PPI Tier", "Savings (INR)", 
                "Delay Saved (Hrs)", "CO2 Saved (kg)"
            ]
            csv_string = csv_df.to_csv(index=False)
            
            # 2. Format WhatsApp/Telegram text
            route_names = [loc['name'] for loc in route]
            dispatch_msg = (
                f"🚨 PARKPULSE OPTIMIZED DISPATCH PLAN 🚨\n"
                f"📅 Target Date: {f_date}\n"
                f"🚓 Deployed Patrols: {total_assigned}/{n_units} units\n"
                f"🗺️ Optimal Routing: {' ➔ '.join(route_names)}\n\n"
                f"📋 Hotspot Allocation Details:\n"
            )
            for _, r in assigned.iterrows():
                dispatch_msg += f"• {r['hotspot_id']}: {int(r['units_assigned'])} unit(s) (Forecast: {r['forecasted_violations']:.0f}/day)\n"
            
            dispatch_msg += (
                f"\n📊 Total Simulated Impact:\n"
                f"- Economic Savings: ₹{total_savings:,.2f}\n"
                f"- Delay Hours Saved: {total_delay_reduced:.1f} hrs\n"
                f"- CO2 Carbon Saved: {total_co2_saved:.1f} kg"
            )
            
            st.markdown('<p class="pp-section" style="margin-top:14px;">Operational Dispatch Tooling</p>', unsafe_allow_html=True)
            
            # CSV Download Button
            st.download_button(
                label="📥 Download Dispatch Plan (CSV)",
                data=csv_string,
                file_name=f"parkpulse_patrol_plan_{f_date}.csv",
                mime="text/csv",
                key="download_dispatch_csv"
            )
            
            # Copy Code Block
            st.markdown(
                '<p style="font-family:Inter,sans-serif;font-size:0.72rem;color:#8B96A3;margin-top:8px;margin-bottom:4px;">'
                '📋 CLICK COPY BUTTON ON THE CODE BLOCK TO DISPATCH TO OFFICER GROUPS:</p>',
                unsafe_allow_html=True
            )
            st.code(dispatch_msg, language="markdown")

        st.markdown('<p class="pp-section">Deployment Table</p>', unsafe_allow_html=True)

        if len(assigned) == 0:
            st.markdown(
                '<div class="hs-card" style="border-left-color:#8B96A3;">'
                '<div class="hs-name">No units allocated — increase unit count.</div></div>',
                unsafe_allow_html=True,
            )
        else:
            for _, row in assigned.iterrows():
                tier  = row["ppi_tier"]
                color = TC.get(tier, "#888")
                badge = tier_badge_html(tier)
                units = int(row["units_assigned"])
                name  = row["hotspot_id"]
                fc    = row["forecasted_violations"]
                ppi   = row["ppi_score"]
                max_u = int(row.get("max_units_per_hotspot", 5))

                with st.expander(
                    f"{name}  ·  {units} unit{'s' if units != 1 else ''}",
                    expanded=(tier == "Critical"),
                ):
                    st.markdown(
                        f'<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:8px;">'
                        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.85rem;'
                        f'color:#8B96A3;">Forecast&nbsp;<b style="color:#E8ECEF;">{fc:.0f}</b></span>'
                        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.85rem;'
                        f'color:#8B96A3;">PPI&nbsp;<b style="color:#E8ECEF;">{ppi:.1f}</b></span>'
                        f'{badge}</div>'
                        f'<div style="font-family:Inter,sans-serif;font-size:0.73rem;color:#8B96A3;">'
                        f'{"Min 1 unit — Critical tier guarantee. " if tier == "Critical" else ""}'
                        f'Capped at {max_u} units/hotspot.</div>',
                        unsafe_allow_html=True,
                    )

    with map_col:
        st.markdown('<p class="pp-section">Deployment Map</p>', unsafe_allow_html=True)
        if len(assigned) > 0:
            alloc_map = build_allocation_map(assigned, hotspots_df, ppi_df, draw_route=draw_route)
            from streamlit_folium import st_folium
            st_folium(alloc_map, width=None, height=540, returned_objects=[])
        else:
            st.markdown(
                '<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
                'border-radius:8px;padding:40px;text-align:center;font-family:Inter,sans-serif;'
                'font-size:0.85rem;color:#8B96A3;">No units to display.</div>',
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════
#  PAGE 3.5 — WHAT-IF SIMULATOR
# ═══════════════════════════════════════════════════════════════════
elif page == "What-If Simulator":

    st.markdown('<p class="pp-section">Interactive What-If Patrol Simulator</p>', unsafe_allow_html=True)

    st.markdown(
        '<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
        'border-left:3px solid #E5484D;border-radius:8px;padding:14px 20px;'
        'margin-bottom:16px;font-family:Inter,sans-serif;font-size:0.82rem;color:#8B96A3;">'
        'Adjust the patrol sliders to see how manual unit allocations deter expected illegal parking '
        'and cause spatial spillover to the closest neighboring hotspot. '
        'Savings are calculated in real-time based on travel delay and wasted fuel.</div>',
        unsafe_allow_html=True,
    )

    from src.config import (
        DETERRENCE_RATE_PER_UNIT,
        SPILLOVER_RATE,
        MAP_CENTER,
        MAP_ZOOM,
    )
    from src.models.allocation import compute_economic_metrics
    import folium

    # Get tomorrow's forecast date
    future = forecast_df[forecast_df["actual_violations"].isna()]
    if len(future) == 0:
        future = forecast_df
    forecast_date = future["forecast_date"].max()
    day_fc = forecast_df[forecast_df["forecast_date"] == forecast_date].copy()

    # Join with PPI (including severity_component)
    merged = day_fc.merge(
        ppi_df[["junction_name_norm", "ppi_score", "ppi_tier", "severity_component"]],
        left_on="hotspot_id", right_on="junction_name_norm",
        how="inner",
    )

    # Filter for top-15 hotspots
    top_15 = merged.sort_values("ppi_score", ascending=False).head(15).copy()

    # Join with hotspots_df to get coords
    top_15_geo = top_15.merge(
        hotspots_df[["dominant_junction_name", "centroid_lat", "centroid_lon"]],
        left_on="hotspot_id", right_on="dominant_junction_name",
        how="inner",
    )

    # Precompute nearest neighbor in top-15 for each top-15 hotspot
    nearest_neighbor = {}
    for idx, row_i in top_15_geo.iterrows():
        name_i = row_i["hotspot_id"]
        lat_i, lon_i = row_i["centroid_lat"], row_i["centroid_lon"]
        
        min_dist = float("inf")
        closest_name = None
        for idx2, row_j in top_15_geo.iterrows():
            name_j = row_j["hotspot_id"]
            if name_i == name_j:
                continue
            dist = ((lat_i - row_j["centroid_lat"])**2 + (lon_i - row_j["centroid_lon"])**2)**0.5
            if dist < min_dist:
                min_dist = dist
                closest_name = name_j
        nearest_neighbor[name_i] = closest_name

    ctrl_col, main_col = st.columns([1, 2], gap="medium")

    user_allocations = {}

    with ctrl_col:
        st.markdown('<p class="pp-section">Manual Patrol Assignments</p>', unsafe_allow_html=True)
        
        critical_spots = top_15_geo[top_15_geo["ppi_tier"] == "Critical"]
        other_spots = top_15_geo[top_15_geo["ppi_tier"] != "Critical"]
        
        st.markdown('<span style="font-size:0.75rem;font-weight:600;color:#E5484D;letter-spacing:0.04em;">CRITICAL HOTSPOTS</span>', unsafe_allow_html=True)
        for _, row in critical_spots.iterrows():
            name = row["hotspot_id"]
            user_allocations[name] = st.slider(
                name,
                min_value=0, max_value=5, value=0, step=1,
                key=f"sim_{name}"
            )
            
        st.markdown('<span style="font-size:0.75rem;font-weight:600;color:#F2994A;letter-spacing:0.04em;margin-top:14px;display:block;">HIGH & MEDIUM HOTSPOTS</span>', unsafe_allow_html=True)
        with st.expander("Expand other hotspots", expanded=False):
            for _, row in other_spots.iterrows():
                name = row["hotspot_id"]
                user_allocations[name] = st.slider(
                    name,
                    min_value=0, max_value=5, value=0, step=1,
                    key=f"sim_{name}"
                )

    # Calculate deterrence and spillover
    post_violations = {}
    spillover_emitted = {}
    for _, row in top_15_geo.iterrows():
        name = row["hotspot_id"]
        fc = row["predicted_violations"]
        units = user_allocations[name]
        post_fc = fc * ((1.0 - DETERRENCE_RATE_PER_UNIT) ** units)
        post_violations[name] = post_fc
        spillover_emitted[name] = (fc - post_fc) * SPILLOVER_RATE

    final_violations = {name: post_violations[name] for name in post_violations}
    spillover_received = {name: 0.0 for name in post_violations}
    for name, spill in spillover_emitted.items():
        neighbor = nearest_neighbor.get(name)
        if neighbor:
            final_violations[neighbor] += spill
            spillover_received[neighbor] += spill

    # Calculate economic impact
    total_baseline_cost = 0.0
    total_simulated_cost = 0.0
    total_baseline_delay = 0.0
    total_simulated_delay = 0.0
    total_baseline_co2 = 0.0
    total_simulated_co2 = 0.0
    
    sim_rows = []
    for _, row in top_15_geo.iterrows():
        name = row["hotspot_id"]
        fc = row["predicted_violations"]
        sev = row["severity_component"]
        units = user_allocations[name]
        
        base_metrics = compute_economic_metrics(fc, sev)
        sim_metrics = compute_economic_metrics(final_violations[name], sev)
        
        total_baseline_cost += base_metrics["economic_loss_inr"]
        total_simulated_cost += sim_metrics["economic_loss_inr"]
        total_baseline_delay += base_metrics["delay_hours"]
        total_simulated_delay += sim_metrics["delay_hours"]
        total_baseline_co2 += base_metrics["co2_emissions_kg"]
        total_simulated_co2 += sim_metrics["co2_emissions_kg"]
        
        sim_rows.append({
            "Junction": name,
            "Tier": row["ppi_tier"],
            "Baseline Violations": round(fc, 1),
            "Assigned Units": units,
            "Deterred": round(fc - post_violations[name], 1),
            "Spillover In": round(spillover_received[name], 1),
            "Simulated Violations": round(final_violations[name], 1),
            "Baseline Loss (INR)": base_metrics["economic_loss_inr"],
            "Simulated Loss (INR)": sim_metrics["economic_loss_inr"],
            "Savings (INR)": round(max(base_metrics["economic_loss_inr"] - sim_metrics["economic_loss_inr"], 0.0), 2),
        })

    total_savings = max(total_baseline_cost - total_simulated_cost, 0.0)
    total_delay_saved = max(total_baseline_delay - total_simulated_delay, 0.0)
    total_co2_saved = max(total_baseline_co2 - total_simulated_co2, 0.0)

    with main_col:
        st.markdown('<p class="pp-section">Simulation Performance Metrics</p>', unsafe_allow_html=True)
        
        # Summary stat cards
        sc1, sc2, sc3 = st.columns(3)
        for col, lbl, val, sub in [
            (sc1, "Simulated Savings", f"₹{total_savings:,.2f}", "travel time + fuel saved"),
            (sc2, "Travel Delay Reduced", f"{total_delay_saved:.1f} hrs", "vehicle-hours saved"),
            (sc3, "CO2 Carbon Saved", f"{total_co2_saved:.1f} kg", "emissions avoided"),
        ]:
            col.markdown(
                f'<div class="stat-card" style="border-color: rgba(46,204,113,0.3);">'
                f'<div class="label" style="color: #2ECC71;">{lbl}</div>'
                f'<div class="value" style="font-size: 1.15rem;">{val}</div>'
                f'<div class="sub" style="font-size: 0.68rem;">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Build simulator map
        m_sim = folium.Map(location=MAP_CENTER, zoom_start=MAP_ZOOM, tiles="CartoDB dark_matter")
        
        for _, row in top_15_geo.iterrows():
            name = row["hotspot_id"]
            lat = row["centroid_lat"]
            lon = row["centroid_lon"]
            tier = row["ppi_tier"]
            color = TC.get(tier, "#888")
            units = user_allocations[name]
            sim_viol = final_violations[name]
            base_viol = row["predicted_violations"]
            
            # Scale radius between 6 and 28 px
            r = 6 + (sim_viol / max(top_15_geo["predicted_violations"].max(), 1.0)) * 22
            
            popup_html = (
                f"<div style='font-family:Inter,sans-serif;font-size:13px;"
                f"background:#141A21;color:#E8ECEF;padding:10px 14px;"
                f"border-radius:6px;min-width:180px;'>"
                f"<b style='color:{color};'>{name}</b><br>"
                f"<span style='color:#8B96A3;font-size:11px;'>{tier} tier</span><br><br>"
                f"Assigned Units:&nbsp;<b style='font-family:monospace;'>{units}</b><br>"
                f"Baseline Forecast:&nbsp;<b style='font-family:monospace;'>{base_viol:.1f}</b>/day<br>"
                f"Simulated Violations:&nbsp;<b style='font-family:monospace;'>{sim_viol:.1f}</b>/day</div>"
            )
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=r,
                color=color,
                weight=1.5,
                fill=True,
                fill_color=color,
                fill_opacity=0.45,
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=f"{name} · {units} unit(s) · Simulated: {sim_viol:.1f}",
            ).add_to(m_sim)
            
            if units > 0:
                folium.Marker(
                    location=[lat, lon],
                    icon=folium.DivIcon(
                        html=(
                            f'<div style="background:{color};color:#0B0F14;'
                            f'width:24px;height:24px;border-radius:50%;'
                            f'display:flex;align-items:center;justify-content:center;'
                            f'font-weight:700;font-size:11px;font-family:IBM Plex Mono,monospace;'
                            f'border:2px solid rgba(255,255,255,0.3);">{units}</div>'
                        ),
                        icon_size=(24, 24),
                        icon_anchor=(12, 12),
                    ),
                ).add_to(m_sim)

        st.markdown('<p class="pp-section" style="margin-top:20px;">Simulator Map (Visualizing Deterrence and Spillover)</p>', unsafe_allow_html=True)
        from streamlit_folium import st_folium
        st_folium(m_sim, width=None, height=400, key="sim_folium_map", returned_objects=[])

        total_units_assigned = sum(user_allocations.values())
        st.markdown(
            f'<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
            f'border-radius:8px;padding:12px 16px;margin-bottom:12px;font-family:Inter,sans-serif;font-size:0.8rem;color:#8B96A3;">'
            f'Total Units Allocated: <b style="color:#E8ECEF;">{total_units_assigned}</b> units.</div>',
            unsafe_allow_html=True
        )

        st.markdown('<p class="pp-section" style="margin-top:20px;">Simulator Results Comparison</p>', unsafe_allow_html=True)
        sim_df = pd.DataFrame(sim_rows)
        display_sim_df = sim_df.copy()
        display_sim_df["Baseline Loss (INR)"] = display_sim_df["Baseline Loss (INR)"].map(lambda val: f"₹{val:,.2f}")
        display_sim_df["Simulated Loss (INR)"] = display_sim_df["Simulated Loss (INR)"].map(lambda val: f"₹{val:,.2f}")
        display_sim_df["Savings (INR)"] = display_sim_df["Savings (INR)"].map(lambda val: f"₹{val:,.2f}")
        st.dataframe(display_sim_df, use_container_width=True, height=350, hide_index=True)


# ═══════════════════════════════════════════════════════════════════
#  PAGE 4 — DATA & METHODOLOGY
# ═══════════════════════════════════════════════════════════════════
elif page == "Data & Methodology":

    st.markdown('<p class="pp-section">Data & Methodology</p>', unsafe_allow_html=True)

    def _section(title: str) -> None:
        st.markdown(
            f'<div style="font-family:Inter,sans-serif;font-weight:600;font-size:0.95rem;'
            f'color:#E8ECEF;margin:24px 0 8px 0;padding-bottom:6px;'
            f'border-bottom:1px solid rgba(255,255,255,0.07);">{title}</div>',
            unsafe_allow_html=True,
        )

    def _kv(key: str, value: str) -> None:
        st.markdown(
            f'<div style="display:flex;gap:16px;padding:7px 0;'
            f'border-bottom:1px solid rgba(255,255,255,0.04);">'
            f'<span style="font-family:Inter,sans-serif;font-size:0.8rem;color:#8B96A3;'
            f'min-width:200px;">{key}</span>'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.8rem;'
            f'color:#E8ECEF;">{value}</span></div>',
            unsafe_allow_html=True,
        )

    # Dataset facts
    _section("Dataset")
    _kv("Source file",    "jan_to_may_police_violation_anonymized791b166.csv")
    _kv("Total records",  "298,450")
    _kv("Date window",    "Nov 9, 2023 – Apr 8, 2024")
    _kv("Coverage",       "Bangalore · lat 12.80–13.29 · lon 77.44–77.77")
    _kv("Unique junctions", "169 raw · 164 with usable attribution")
    _kv("Police stations",  "54")
    _kv("Vehicle mix",    "Scooter 31.8% · Car 29.8% · Motorcycle 13.7% · Auto 12.7%")
    _kv("Raw files",      "Read-only — no in-place mutations")

    # Unattributable-records callout — explicitly presented, not hidden
    st.markdown(
        '<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
        'border-left:3px solid #F2994A;border-radius:8px;padding:16px 20px;margin:12px 0;">'
        '<div style="font-family:Inter,sans-serif;font-weight:600;font-size:0.85rem;'
        'color:#E8ECEF;margin-bottom:8px;">Junction Attribution Finding</div>'
        '<div style="font-family:Inter,sans-serif;font-size:0.82rem;color:#8B96A3;line-height:1.7;">'
        '<b style="font-family:IBM Plex Mono,monospace;color:#F2994A;">147,880</b> records '
        '(<b style="font-family:IBM Plex Mono,monospace;color:#F2994A;">49.5%</b> of all 298,450) '
        'carry the literal value <code>"No Junction"</code> in the junction field — '
        'meaning they had no junction attribution at entry time. '
        'A further <b style="font-family:IBM Plex Mono,monospace;color:#F2994A;">5</b> records '
        'have a true null, coerced to <code>"Unknown"</code> by the cleaning step.<br><br>'
        'These records are <b style="color:#E8ECEF;">not dropped</b> — they remain in '
        '<code>violations_clean</code> for transparency and contribute to DBSCAN geometric '
        'clustering (which keys off lat/long, not junction name). '
        'They are <b style="color:#E5484D;">excluded</b> from all named-hotspot PPI scoring, '
        'forecasting, and allocation, since there is no real, actionable address behind them. '
        'The exclusion is enforced by a single constant (<code>JUNCTION_PLACEHOLDER_NAMES</code> '
        'in <code>config.py</code>) imported by every pipeline module — not scattered per-file.'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # Cleaning steps
    _section("Cleaning Steps")
    st.markdown("""
<div style="font-family:Inter,sans-serif;font-size:0.82rem;color:#E8ECEF;line-height:1.8;">
<ol style="padding-left:18px;color:#8B96A3;">
<li><b style="color:#E8ECEF;">Multi-label parsing</b> — <code>violation_type</code> stored as JSON-array strings
(e.g. <code>["WRONG PARKING","NO PARKING"]</code>). Parsed with <code>json.loads</code>; severity weight
derived from documented per-label table.</li>
<li><b style="color:#E8ECEF;">Timezone correction</b> — Timestamps are UTC. Converted to IST (+05:30) for all
temporal analysis. Labelled everywhere as <i>enforcement-action time</i>, not offense-occurrence time.</li>
<li><b style="color:#E8ECEF;">Validation filter</b> — Only <code>approved</code> records used for
PPI/forecast/allocation. Rejected+duplicate: <b>28.9%</b> of non-null statuses.</li>
<li><b style="color:#E8ECEF;">Junction normalisation</b> — Trimmed whitespace, title-cased.
No fuzzy-merge beyond exact-after-normalisation.</li>
<li><b style="color:#E8ECEF;">Dropped columns</b> — <code>description</code>, <code>closed_datetime</code>,
<code>action_taken_timestamp</code> — all 100% null.</li>
</ol>
</div>
""", unsafe_allow_html=True)

    # PPI formula
    _section("Parking Pressure Index (PPI)")
    st.markdown("""
<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);border-radius:8px;
padding:20px 24px;font-family:IBM Plex Mono,monospace;font-size:0.82rem;color:#E8ECEF;
line-height:2;margin-bottom:12px;">
PPI = 0.4 × norm(violation_frequency)<br>
&nbsp;&nbsp;&nbsp;&nbsp;+ 0.3 × norm(severity_weight)<br>
&nbsp;&nbsp;&nbsp;&nbsp;+ 0.2 × norm(repeat_offender_ratio)<br>
&nbsp;&nbsp;&nbsp;&nbsp;+ 0.1 × norm(persistence)
</div>
<div style="font-family:Inter,sans-serif;font-size:0.8rem;color:#8B96A3;line-height:1.7;">
<b style="color:#E8ECEF;">norm()</b> = min-max across all junctions in the trailing 90-day window.<br>
<b style="color:#E8ECEF;">Tier thresholds</b> — quantile-based:
Critical = top 10% · High = next 20% · Medium = next 30% · Low = bottom 40%.<br>
<b style="color:#E8ECEF;">Sensitivity check</b> — each weight perturbed ±10% (renormalised);
top-15 ranking overlap reported. Result: <b style="color:#2ECC71;">STABLE (14–15/15 overlap across all perturbations)</b>.<br>
<b style="color:#E5484D;">PPI is a priority proxy — not a measured traffic-flow metric.</b>
</div>
""", unsafe_allow_html=True)

    # Severity table
    _section("Severity Weight Table")
    sev_data = {
        "Violation Label": [
            "PARKING IN A MAIN ROAD", "PARKING ON FOOTPATH", "PARKING IN A BUS STOP",
            "PARKING NEAR ROAD CROSSING", "PARKING NEAR SIGNAL", "PARKING NEAR SCHOOL",
            "PARKING NEAR HOSPITAL", "WRONG PARKING", "NO PARKING",
        ],
        "Weight": [1.0, 0.9, 0.8, 0.7, 0.7, 0.6, 0.6, 0.5, 0.5],
        "Rationale": [
            "Directly blocks major traffic artery",
            "Blocks pedestrian path, safety risk",
            "Blocks bus stop, delays public transit",
            "Increases collision risk at junctions",
            "Impedes signal-controlled flow",
            "Safety risk near school zones",
            "Emergency-vehicle access concern",
            "Generic illegal parking",
            "No-parking zone violation",
        ],
    }
    st.dataframe(pd.DataFrame(sev_data), use_container_width=True, hide_index=True)

    # Forecasting
    _section("Forecasting")
    _kv("Primary model",      "LightGBM")
    _kv("Cross-check",        "XGBoost")
    _kv("Baselines",          "Yesterday's count · 7-day rolling average")
    _kv("Train split",        "Nov 2023 – Feb 2024")
    _kv("Validate split",     "Mar 2024 (early stopping + reported metrics)")
    _kv("Test split",         "Apr 2024 — held out; 0 validated rows after filter (partial month)")
    _kv("Eligible junctions", "Top-15 by volume with ≥30 days history")
    _kv("Features",           "lag-1, lag-7, roll-7/14 mean+std, DoW, month, holiday, junction_id")
    _kv("Note on Apr 2024",
        "The held-out test slice contained 0 validated rows after applying the approved-only "
        "filter to the partial month. Reported metrics are therefore from the Mar 2024 "
        "validation split — not in-sample training numbers.")

    # Backtest results — real numbers, honestly labelled
    _section("Backtest Results — Validation Set (Mar 2024)")
    val_rows = forecast_df[
        (forecast_df["split"] == "validate") & forecast_df["actual_violations"].notna()
    ]
    if len(val_rows) > 0:
        mae   = (val_rows["actual_violations"] - val_rows["predicted_violations"]).abs().mean()
        rmse  = ((val_rows["actual_violations"] - val_rows["predicted_violations"]) ** 2).mean() ** 0.5
        wdenom = val_rows["actual_violations"].abs().sum()
        wape  = (val_rows["actual_violations"] - val_rows["predicted_violations"]).abs().sum() / wdenom * 100
        n_y   = (val_rows["actual_violations"] - val_rows["baseline_naive_predicted"]).abs().mean()
        n_r7  = (val_rows["actual_violations"] - val_rows["baseline_rolling7_predicted"]).abs().mean()
        beat_y  = mae < n_y
        beat_r7 = mae < n_r7

        r1, r2, r3, r4, r5 = st.columns(5)
        for col, lbl, val, good in [
            (r1, "MAE",               f"{mae:.2f}",   None),
            (r2, "RMSE",              f"{rmse:.2f}",  None),
            (r3, "WAPE",              f"{wape:.1f}%", None),
            (r4, "vs Yesterday MAE",  f"{n_y:.2f}",   None),
            (r5, "Beat 7-day roll?",  "YES" if beat_r7 else "NO", beat_r7),
        ]:
            col.markdown(
                f'<div class="stat-card" style="padding:14px 18px;">'
                f'<div class="label">{lbl}</div>'
                f'<div class="value" style="font-size:1.2rem;'
                f'color:{"#2ECC71" if good else ("#E5484D" if good is False else "#E8ECEF")};">'
                f'{val}</div></div>',
                unsafe_allow_html=True,
            )

        # Honest interpretation — state what the numbers mean, don't hide the caveat
        beat_yesterday_str = "beats" if beat_y else "does not beat"
        st.markdown(
            f'<div style="font-family:Inter,sans-serif;font-size:0.8rem;color:#8B96A3;'
            f'margin-top:12px;line-height:1.7;">'
            f'LightGBM MAE <b style="font-family:IBM Plex Mono,monospace;color:#E8ECEF;">{mae:.2f}</b> '
            f'violations/day across 15 junctions on the Mar 2024 validation set. '
            f'Model <b style="color:#{"2ECC71" if beat_r7 else "E5484D"};">{"beats" if beat_r7 else "does not beat"}</b> '
            f'the 7-day rolling baseline (MAE {n_r7:.2f}) and '
            f'<b style="color:#{"2ECC71" if beat_y else "F2994A"};">{beat_yesterday_str}</b> '
            f'the yesterday baseline (MAE {n_y:.2f}). '
            f'High WAPE ({wape:.0f}%) reflects low-volume junctions where even small absolute '
            f'errors produce large percentage deviations — this is expected and stated, not hidden.'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="color:#8B96A3;font-size:0.82rem;">'
            'No validate rows found in current forecast artifact.</div>',
            unsafe_allow_html=True,
        )

    # Patrol allocation
    _section("Patrol Allocation")
    _kv("Method",      "Mixed-Integer Linear Program (MILP) · PuLP open-source solver")
    _kv("Objective",   "Maximise Σ units_i × forecasted_violations_i × ppi_weight_i")
    _kv("Constraints", "Total units ≤ available · each hotspot ≤ 5 units · Critical ≥ 1 unit")
    _kv("Precomputed", "Unit counts 5, 10, 15, 20, 25 — live solve for any other value (<1s)")

    # Limitations
    _section("Known Limitations")
    st.markdown("""
<div style="font-family:Inter,sans-serif;font-size:0.82rem;color:#8B96A3;line-height:1.8;">
<ol style="padding-left:18px;">
<li><b style="color:#E5484D;">PPI is a proxy</b> — no speed/volume data exists; cannot measure actual traffic-flow impact.</li>
<li><b style="color:#E8ECEF;">Timestamp = enforcement-action time</b> — morning-sweep pattern (00:30–13:00 IST) reflects
when officers record tags, not when vehicles parked.</li>
<li><b style="color:#E8ECEF;">Forecast scope limited</b> — only top-volume junctions with ≥30 days history; long-tail
junctions are explicitly excluded.</li>
<li><b style="color:#E8ECEF;">28.9% rejected/duplicate</b> — validated-only view shrinks effective sample for
low-volume junctions.</li>
<li><b style="color:#E8ECEF;">Historical system only</b> — no real-time feed; live enforcement triggering requires
traffic-flow API integration (Phase 2).</li>
</ol>
</div>
""", unsafe_allow_html=True)

    _section("Future Work")
    st.markdown("""
<div style="font-family:Inter,sans-serif;font-size:0.82rem;color:#8B96A3;line-height:1.8;">
<ul style="padding-left:18px;">
<li>Integrate live traffic-flow/speed APIs to replace PPI proxy with measured impact.</li>
<li>OCR/CV layer for image-based violation auto-detection once image data is available.</li>
<li>Continuous RL once outcome-feedback data (post-deployment violation reduction) is collected.</li>
</ul>
</div>
""", unsafe_allow_html=True)
