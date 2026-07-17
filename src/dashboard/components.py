"""
ParkPulse — UI components (visual rebuild).
All charts are built with explicit layout/margin/font settings — no Plotly defaults.
"""
from __future__ import annotations

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from src.config import (
    MAP_CENTER,
    MAP_ZOOM,
    TIER_COLORS,
    TIER_ICONS,
)

# ── Design tokens (mirrored from CSS for Python-side use) ─────────────────────
BG_CARD   = "#141A21"
BG_DARK   = "#0B0F14"
TXT_PRI   = "#E8ECEF"
TXT_MUT   = "#8B96A3"
BORDER    = "rgba(255,255,255,0.07)"

# Tier colors (desaturated for instrumentation feel)
TC = {
    "Critical": "#E5484D",
    "High":     "#F2994A",
    "Medium":   "#F2C94C",
    "Low":      "#2ECC71",
}

CHART_FONT = dict(family="IBM Plex Mono, JetBrains Mono, monospace", color=TXT_PRI)
LABEL_FONT = dict(family="Inter, IBM Plex Sans, sans-serif", color=TXT_MUT, size=11)

PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=CHART_FONT,
)


# ── Tier badge HTML ───────────────────────────────────────────────────────────

def tier_badge_html(tier: str, size: str = "0.78rem") -> str:
    color = TC.get(tier, "#888")
    return (
        f'<span style="display:inline-block;background:{color}22;color:{color};'
        f'border:1px solid {color}55;padding:2px 10px;border-radius:4px;'
        f'font-size:{size};font-family:Inter,sans-serif;font-weight:600;'
        f'letter-spacing:0.04em;">{tier.upper()}</span>'
    )


# ── Overview map ──────────────────────────────────────────────────────────────

def build_overview_map(
    ppi_df: pd.DataFrame,
    hotspots_df: pd.DataFrame,
    selected_hotspot: str | None = None,
    station_filter: str | None = None,
) -> folium.Map:
    m = folium.Map(
        location=MAP_CENTER,
        zoom_start=MAP_ZOOM,
        tiles="CartoDB dark_matter",
    )

    display = ppi_df.copy()
    if station_filter:
        display = display[display["police_station"] == station_filter]

    # Normalise frequency to radius 6–28px
    freq_vals = display["violation_frequency"].clip(lower=0)
    f_min, f_max = freq_vals.min(), freq_vals.max()

    def _radius(f: float) -> float:
        if f_max == f_min:
            return 12
        return 6 + (f - f_min) / (f_max - f_min) * 22

    for _, row in display.iterrows():
        junc = row["junction_name_norm"]
        tier = row["ppi_tier"]
        color = TC.get(tier, "#888")
        ppi   = row["ppi_score"]
        freq  = row["violation_frequency"]

        hs_row = hotspots_df[hotspots_df["dominant_junction_name"] == junc]
        if len(hs_row) == 0:
            continue
        lat = hs_row.iloc[0]["centroid_lat"]
        lon = hs_row.iloc[0]["centroid_lon"]

        r = _radius(freq)
        is_em = int(row.get("is_emerging", 0)) == 1
        em_text = "<br><span style='color:#E5484D;font-weight:600;font-size:10px;'>⚠️ EMERGING HOTSPOT</span>" if is_em else ""

        popup_html = (
            f"<div style='font-family:Inter,sans-serif;font-size:13px;"
            f"background:#141A21;color:#E8ECEF;padding:10px 14px;"
            f"border-radius:6px;min-width:180px;'>"
            f"<b style='color:{color};'>{junc}</b>{em_text}<br>"
            f"<span style='color:#8B96A3;font-size:11px;'>{tier} tier</span><br><br>"
            f"PPI&nbsp;&nbsp;<b style='font-family:monospace;'>{ppi:.1f}</b><br>"
            f"Freq&nbsp;<b style='font-family:monospace;'>{freq:.1f}</b>/day</div>"
        )

        folium.CircleMarker(
            location=[lat, lon],
            radius=r,
            color="#E5484D" if is_em else color,
            weight=2.5 if is_em else 1.5,
            fill=True,
            fill_color="#E5484D" if is_em else color,
            fill_opacity=0.65 if is_em else 0.55,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{junc} {'(⚠️ EMERGING)' if is_em else ''} · PPI {ppi:.1f} · {tier}",
        ).add_to(m)

    # Docked legend (bottom-right)
    legend_html = """
    <div style="position:fixed;bottom:24px;right:16px;z-index:9999;
                background:#141A21;border:1px solid rgba(255,255,255,0.12);
                padding:12px 16px;border-radius:6px;font-family:Inter,sans-serif;
                font-size:12px;color:#E8ECEF;min-width:170px;">
      <div style="font-weight:600;margin-bottom:8px;letter-spacing:0.05em;
                  color:#8B96A3;font-size:11px;">PPI TIER</div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
        <div style="width:12px;height:12px;border-radius:50%;background:#E5484D;flex-shrink:0;"></div>
        <span style="color:#E5484D;font-weight:600;">CRITICAL</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
        <div style="width:12px;height:12px;border-radius:50%;background:#F2994A;flex-shrink:0;"></div>
        <span style="color:#F2994A;font-weight:600;">HIGH</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
        <div style="width:12px;height:12px;border-radius:50%;background:#F2C94C;flex-shrink:0;"></div>
        <span style="color:#F2C94C;font-weight:600;">MEDIUM</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
        <div style="width:12px;height:12px;border-radius:50%;background:#2ECC71;flex-shrink:0;"></div>
        <span style="color:#2ECC71;font-weight:600;">LOW</span>
      </div>
      <div style="border-top:1px solid rgba(255,255,255,0.08);padding-top:8px;
                  color:#8B96A3;font-size:10px;">
        Circle radius = violations/day
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


# ── PPI breakdown bar chart ───────────────────────────────────────────────────

def ppi_breakdown_chart(row: pd.Series) -> go.Figure:
    labels = ["Frequency ×0.4", "Severity ×0.3", "Repeat ×0.2", "Persistence ×0.1"]
    values = [
        float(row.get("freq_norm",    0)) * 0.4,
        float(row.get("sev_norm",     0)) * 0.3,
        float(row.get("repeat_norm",  0)) * 0.2,
        float(row.get("persist_norm", 0)) * 0.1,
    ]
    bar_colors = [TC["Critical"], TC["High"], TC["Medium"], TC["Low"]]
    max_track = 0.42   # ceiling = max possible (0.4) + breathing room

    # Per-bar: if bar fills >30% of track, put label inside; otherwise outside
    text_positions, text_colors = [], []
    for v in values:
        if v / max_track > 0.30:
            text_positions.append("inside")
            text_colors.append("#0B0F14")
        else:
            text_positions.append("outside")
            text_colors.append(TXT_PRI)

    fig = go.Figure()
    for lbl, val, col, tpos, tcol in zip(
        labels, values, bar_colors, text_positions, text_colors
    ):
        fig.add_trace(go.Bar(
            x=[val],
            y=[lbl],
            orientation="h",
            marker_color=col,
            marker_line_width=0,
            text=[f"{val:.3f}"],
            textposition=tpos,
            insidetextanchor="end" if tpos == "inside" else None,
            textfont=dict(family="IBM Plex Mono,monospace", size=11, color=tcol),
            cliponaxis=False,
            showlegend=False,
            width=0.55,
        ))

    fig.update_layout(
        **PLOTLY_BASE,
        height=210,
        margin=dict(l=0, r=60, t=8, b=0),
        barmode="overlay",
        xaxis=dict(
            range=[0, max_track],
            showgrid=False,
            showticklabels=False,
            zeroline=False,
            fixedrange=True,
        ),
        yaxis=dict(
            tickfont=dict(family="Inter,sans-serif", size=11, color=TXT_MUT),
            automargin=True,
            fixedrange=True,
            categoryorder="array",
            categoryarray=list(reversed(labels)),
        ),
        bargap=0.0,
    )
    return fig


# ── Temporal charts ───────────────────────────────────────────────────────────

def hourly_chart(temporal_df: pd.DataFrame, junction: str) -> go.Figure:
    sub = temporal_df[
        (temporal_df["junction_name_norm"] == junction) &
        (temporal_df["dimension"] == "hour")
    ].copy()
    if len(sub) == 0:
        return _empty_chart("No hourly data")
    sub["hour"] = sub["dimension_value"].astype(int)
    sub = sub.sort_values("hour")

    fig = go.Figure(go.Bar(
        x=sub["hour"],
        y=sub["count"],
        marker_color=TC["High"],
        marker_line_width=0,
    ))
    fig.update_layout(
        **PLOTLY_BASE,
        height=240,
        margin=dict(l=0, r=0, t=32, b=56),
        title=dict(
            text="Violations by Hour (IST)",
            font=dict(family="Inter,sans-serif", size=13, color=TXT_MUT),
            x=0, xanchor="left",
        ),
        xaxis=dict(
            title=dict(text="Hour (IST)", font=LABEL_FONT),
            tickfont=dict(family="IBM Plex Mono,monospace", size=10, color=TXT_MUT),
            gridcolor="rgba(255,255,255,0.04)",
            tickmode="array",
            tickvals=list(range(0, 24, 2)),
        ),
        yaxis=dict(
            title=dict(text="Violations", font=LABEL_FONT),
            tickfont=dict(family="IBM Plex Mono,monospace", size=10, color=TXT_MUT),
            gridcolor="rgba(255,255,255,0.04)",
        ),
    )
    # Annotation anchored below the plot — enough bottom margin so it never clips
    fig.add_annotation(
        text="Enforcement-action time, not offense-occurrence time",
        xref="paper", yref="paper",
        x=0, y=-0.20,
        showarrow=False,
        font=dict(family="Inter,sans-serif", size=10, color=TXT_MUT),
        align="left",
        xanchor="left",
    )
    return fig


def dow_chart(temporal_df: pd.DataFrame, junction: str) -> go.Figure:
    sub = temporal_df[
        (temporal_df["junction_name_norm"] == junction) &
        (temporal_df["dimension"] == "dow")
    ].copy()
    if len(sub) == 0:
        return _empty_chart("No day-of-week data")
    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    sub["ord"] = sub["dimension_value"].map({d: i for i, d in enumerate(order)})
    sub = sub.sort_values("ord")

    fig = go.Figure(go.Bar(
        x=sub["dimension_value"],
        y=sub["count"],
        marker_color=TC["Low"],
        marker_line_width=0,
    ))
    fig.update_layout(
        **PLOTLY_BASE,
        height=200,
        margin=dict(l=0, r=0, t=32, b=0),
        title=dict(
            text="Violations by Day of Week",
            font=dict(family="Inter,sans-serif", size=13, color=TXT_MUT),
            x=0, xanchor="left",
        ),
        xaxis=dict(
            tickfont=dict(family="Inter,sans-serif", size=11, color=TXT_MUT),
            categoryorder="array",
            categoryarray=order,
            gridcolor="rgba(255,255,255,0.04)",
        ),
        yaxis=dict(
            tickfont=dict(family="IBM Plex Mono,monospace", size=10, color=TXT_MUT),
            gridcolor="rgba(255,255,255,0.04)",
        ),
    )
    return fig


# ── Vehicle mix — clean donut, NO secondary chart ─────────────────────────────

def vehicle_mix_chart(violations_sample: pd.DataFrame, junction: str) -> go.Figure:
    sub = violations_sample[violations_sample["junction_name_norm"] == junction]
    if len(sub) == 0:
        return _empty_chart("No vehicle data for this junction")

    mix = sub["vehicle_type"].value_counts().reset_index()
    mix.columns = ["vtype", "count"]
    # Keep top-6, fold rest into "Other"
    if len(mix) > 6:
        top = mix.head(6).copy()
        other_count = mix.iloc[6:]["count"].sum()
        top = pd.concat(
            [top, pd.DataFrame([{"vtype": "Other", "count": other_count}])],
            ignore_index=True,
        )
        mix = top

    palette = ["#E5484D", "#F2994A", "#F2C94C", "#2ECC71", "#5B8DEF", "#A78BFA", "#8B96A3"]
    colors = palette[: len(mix)]

    fig = go.Figure(go.Pie(
        labels=mix["vtype"],
        values=mix["count"],
        hole=0.52,
        marker=dict(colors=colors, line=dict(color=BG_DARK, width=2)),
        textinfo="none",           # no text ON the pie slices — avoids all overlap
        hovertemplate="<b>%{label}</b><br>%{value:,} violations<br>%{percent}<extra></extra>",
        showlegend=True,
        direction="clockwise",
        sort=True,
    ))

    fig.update_layout(
        **PLOTLY_BASE,
        height=280,
        margin=dict(l=0, r=0, t=32, b=0),
        title=dict(
            text="Vehicle Mix",
            font=dict(family="Inter,sans-serif", size=13, color=TXT_MUT),
            x=0, xanchor="left",
        ),
        legend=dict(
            orientation="v",
            x=0.62,
            y=0.5,
            xanchor="left",
            yanchor="middle",
            font=dict(family="Inter,sans-serif", size=11, color=TXT_PRI),
            bgcolor="rgba(0,0,0,0)",
            itemsizing="constant",
        ),
    )
    # Constrain pie domain so it doesn't overlap the legend
    fig.update_traces(domain=dict(x=[0, 0.58], y=[0.04, 0.96]))
    return fig


# ── Forecast chart ────────────────────────────────────────────────────────────

def forecast_chart(forecast_df: pd.DataFrame, junction: str) -> go.Figure:
    sub = forecast_df[forecast_df["hotspot_id"] == junction].copy()
    if len(sub) == 0:
        return _empty_chart("No forecast data for this junction")

    sub["forecast_date"] = pd.to_datetime(sub["forecast_date"])
    actuals = sub[sub["actual_violations"].notna()].sort_values("forecast_date").tail(21)
    future  = sub[sub["actual_violations"].isna()].sort_values("forecast_date")

    fig = go.Figure()

    if len(actuals) > 0:
        fig.add_trace(go.Scatter(
            x=actuals["forecast_date"],
            y=actuals["actual_violations"],
            mode="lines+markers",
            name="Actual",
            line=dict(color="#5B8DEF", width=2),
            marker=dict(size=4, color="#5B8DEF"),
        ))
        fig.add_trace(go.Scatter(
            x=actuals["forecast_date"],
            y=actuals["baseline_rolling7_predicted"],
            mode="lines",
            name="7-day baseline",
            line=dict(color=TXT_MUT, width=1, dash="dot"),
        ))

    if len(future) > 0:
        mae = _compute_mae(actuals) if len(actuals) > 0 else None
        error_band = mae if mae else float(future["predicted_violations"].mean()) * 0.2
        fig.add_trace(go.Scatter(
            x=future["forecast_date"],
            y=future["predicted_violations"],
            mode="markers",
            name="Forecast",
            marker=dict(symbol="diamond", size=12, color=TC["Critical"],
                        line=dict(width=1, color="#fff")),
            error_y=dict(type="constant", value=error_band,
                         visible=True, color=TC["High"], thickness=1.5),
        ))

    mae = _compute_mae(actuals) if len(actuals) > 0 else None
    title_str = "Violation Forecast" + (f"  ·  Backtest MAE ±{mae:.1f}" if mae else "")

    fig.update_layout(
        **PLOTLY_BASE,
        height=300,
        margin=dict(l=0, r=0, t=40, b=32),
        title=dict(
            text=title_str,
            font=dict(family="Inter,sans-serif", size=13, color=TXT_MUT),
            x=0, xanchor="left",
        ),
        xaxis=dict(
            tickfont=dict(family="IBM Plex Mono,monospace", size=10, color=TXT_MUT),
            gridcolor="rgba(255,255,255,0.04)",
        ),
        yaxis=dict(
            title=dict(text="Violations", font=LABEL_FONT),
            tickfont=dict(family="IBM Plex Mono,monospace", size=10, color=TXT_MUT),
            gridcolor="rgba(255,255,255,0.04)",
        ),
        legend=dict(
            orientation="h",
            x=0, y=-0.12,
            xanchor="left",
            font=dict(family="Inter,sans-serif", size=11, color=TXT_MUT),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


# ── Allocation map ────────────────────────────────────────────────────────────

def build_allocation_map(
    allocation_df: pd.DataFrame,
    hotspots_df: pd.DataFrame,
    ppi_df: pd.DataFrame,
    draw_route: bool = False,
) -> folium.Map:
    m = folium.Map(location=MAP_CENTER, zoom_start=MAP_ZOOM, tiles="CartoDB dark_matter")

    merged = allocation_df[allocation_df["units_assigned"] > 0].merge(
        ppi_df[["junction_name_norm", "ppi_tier"]],
        left_on="hotspot_id", right_on="junction_name_norm",
        how="left",
    )

    locations = []

    for _, row in merged.iterrows():
        hs_row = hotspots_df[hotspots_df["dominant_junction_name"] == row["hotspot_id"]]
        if len(hs_row) == 0:
            continue
        lat   = hs_row.iloc[0]["centroid_lat"]
        lon   = hs_row.iloc[0]["centroid_lon"]
        tier  = row.get("ppi_tier", "Low")
        color = TC.get(tier, "#888")
        units = int(row["units_assigned"])
        name  = row["hotspot_id"]
        fc    = row.get("forecasted_violations", 0)

        locations.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "color": color,
            "units": units,
            "tier": tier,
            "fc": fc
        })

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=(
                    f'<div style="background:{color};color:#0B0F14;'
                    f'width:30px;height:30px;border-radius:50%;'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'font-weight:700;font-size:13px;font-family:IBM Plex Mono,monospace;'
                    f'border:2px solid rgba(255,255,255,0.3);">{units}</div>'
                ),
                icon_size=(30, 30),
                icon_anchor=(15, 15),
            ),
            tooltip=(
                f"<b>{name}</b> · {units} unit(s)<br>"
                f"Tier: {tier} · Forecast: {fc:.0f} violations"
            ),
        ).add_to(m)

    if draw_route and locations:
        # Solve TSP
        hq = {"name": "City Police HQ", "lat": 12.97, "lon": 77.59}
        unvisited = locations.copy()
        current = hq
        route = [hq]
        while unvisited:
            nearest = min(unvisited, key=lambda x: (x["lat"] - current["lat"])**2 + (x["lon"] - current["lon"])**2)
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        route.append(hq)

        # Draw HQ Marker
        folium.Marker(
            location=[hq["lat"], hq["lon"]],
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
            tooltip="<b>City Police HQ</b> (Start/End of patrol route)",
        ).add_to(m)

        # Draw Route Lines
        route_coords = [[loc["lat"], loc["lon"]] for loc in route]
        folium.PolyLine(
            route_coords,
            color="#3b82f6",  # Cool neon blue color
            weight=4,
            opacity=0.8,
            dash_array="5, 10",
            tooltip="Optimized Patrol Dispatch Path (TSP)",
        ).add_to(m)

    return m


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compute_mae(actuals: pd.DataFrame) -> float | None:
    valid = actuals.dropna(subset=["actual_violations", "predicted_violations"])
    if len(valid) == 0:
        return None
    return float((valid["actual_violations"] - valid["predicted_violations"]).abs().mean())


def _empty_chart(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(family="Inter,sans-serif", size=13, color=TXT_MUT),
    )
    fig.update_layout(
        **PLOTLY_BASE,
        height=200,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def feature_importance_chart(importance_df: pd.DataFrame) -> go.Figure:
    """Build Explainable AI feature importance chart."""
    if len(importance_df) == 0:
        return _empty_chart("No feature importance data")
    
    # Take top 10 features
    df = importance_df.head(10).sort_values("importance", ascending=True)
    
    fig = go.Figure(go.Bar(
        x=df["importance"],
        y=df["feature"],
        orientation="h",
        marker_color="#5B8DEF",
        marker_line_width=0,
    ))
    
    fig.update_layout(
        **PLOTLY_BASE,
        height=240,
        margin=dict(l=0, r=10, t=32, b=10),
        title=dict(
            text="Forecast Drivers (Explainable AI Feature Importance)",
            font=dict(family="Inter,sans-serif", size=13, color=TXT_MUT),
            x=0, xanchor="left",
        ),
        xaxis=dict(
            title=dict(text="Feature Split Gain", font=LABEL_FONT),
            tickfont=dict(family="IBM Plex Mono,monospace", size=10, color=TXT_MUT),
            gridcolor="rgba(255,255,255,0.04)",
        ),
        yaxis=dict(
            tickfont=dict(family="IBM Plex Mono,monospace", size=10, color=TXT_MUT),
            gridcolor="rgba(255,255,255,0.04)",
        ),
    )
    return fig


def hourly_tomorrow_forecast_chart(temporal_df: pd.DataFrame, junction: str, tomorrow_daily_prediction: float) -> go.Figure:
    """Project tomorrow's hourly distribution based on historical pattern and tomorrow forecast."""
    sub = temporal_df[
        (temporal_df["junction_name_norm"] == junction) &
        (temporal_df["dimension"] == "hour")
    ].copy()
    
    if len(sub) == 0:
        return _empty_chart("No historical hourly distribution to project forecast")
        
    sub["hour"] = sub["dimension_value"].astype(int)
    sub = sub.sort_values("hour")
    
    # Calculate proportion
    total_count = sub["count"].sum()
    if total_count == 0:
        return _empty_chart("No historical hourly count")
        
    sub["proportion"] = sub["count"] / total_count
    sub["tomorrow_projected"] = sub["proportion"] * tomorrow_daily_prediction
    
    fig = go.Figure()
    # Draw line
    fig.add_trace(go.Scatter(
        x=sub["hour"],
        y=sub["tomorrow_projected"],
        mode="lines+markers",
        name="Projected",
        line=dict(color=TC["Critical"], width=2.5),
        marker=dict(size=5, color=TC["Critical"]),
    ))
    
    fig.update_layout(
        **PLOTLY_BASE,
        height=240,
        margin=dict(l=0, r=0, t=32, b=10),
        title=dict(
            text="Tomorrow's Projected Hourly Activity",
            font=dict(family="Inter,sans-serif", size=13, color=TXT_MUT),
            x=0, xanchor="left",
        ),
        xaxis=dict(
            title=dict(text="Hour (IST)", font=LABEL_FONT),
            tickfont=dict(family="IBM Plex Mono,monospace", size=10, color=TXT_MUT),
            gridcolor="rgba(255,255,255,0.04)",
            tickmode="array",
            tickvals=list(range(0, 24, 2)),
        ),
        yaxis=dict(
            title=dict(text="Projected Violations", font=LABEL_FONT),
            tickfont=dict(family="IBM Plex Mono,monospace", size=10, color=TXT_MUT),
            gridcolor="rgba(255,255,255,0.04)",
        ),
    )
    return fig


def root_cause_diagnosis(violations_sample: pd.DataFrame, junction: str) -> dict[str, str]:
    """Diagnose the root cause of illegal parking at a junction and provide policy recommendations."""
    sub = violations_sample[violations_sample["junction_name_norm"] == junction]
    if len(sub) == 0:
        return {
            "category": "Unknown",
            "diagnostic": "Insufficient sample data to diagnose root cause.",
            "recommendation": "Deploy a temporary scout unit to evaluate local layout."
        }
        
    # Get all violation labels
    import json
    all_labels = []
    for lbl_str in sub["violation_labels_str"].dropna():
        try:
            lbls = json.loads(lbl_str)
            if isinstance(lbls, list):
                all_labels.extend(lbls)
        except:
            pass
            
    if not all_labels:
        # Fallback to generic
        return {
            "category": "General Encroachment",
            "diagnostic": "Generic illegal parking without specific category label.",
            "recommendation": "Standard patrol deployment with routine drive-by enforcement."
        }
        
    # Find most frequent label
    from collections import Counter
    top_label = Counter(all_labels).most_common(1)[0][0]
    
    if "SCHOOL" in top_label:
        return {
            "category": "School Drop-Off Congestion",
            "diagnostic": "High concentration of violations near schools. Peaks around school hours due to parents double-parking.",
            "recommendation": "Stagger school timings by 30 mins; mandate designated pick-up/drop-off slots; add physical barriers on sidewalks."
        }
    elif "BUS STOP" in top_label:
        return {
            "category": "Public Transit Obstruction",
            "diagnostic": "Vehicles blocking bus bays, forcing public buses to halt on active road lanes and stalling traffic.",
            "recommendation": "Install camera enforcement on bus bumpers; construct raised bus bays; double the fine for bus stop obstruction."
        }
    elif "FOOTPATH" in top_label:
        return {
            "category": "Pedestrian Path Obstruction",
            "diagnostic": "Motorcycles and cars parking on sidewalks, endangering pedestrians and forcing them onto active roadway.",
            "recommendation": "Install street-side concrete bollards (bollard gates); step up foot-patrol fine issuing; tow vehicles immediately."
        }
    elif "MAIN ROAD" in top_label:
        return {
            "category": "Arterial Road Choking",
            "diagnostic": "Vehicles double-parking or parking on major travel lanes, reducing road capacity by 33-50% in key corridors.",
            "recommendation": "Declare a tow-away corridor; install clear 'TOW ZONE' signs; use private towing contractors for rapid removal."
        }
    elif "SIGNAL" in top_label or "CROSSING" in top_label:
        return {
            "category": "Intersection Gridlock",
            "diagnostic": "Vehicles parked too close to signals or road junctions, restricting turning radius and creating safety blind spots.",
            "recommendation": "Paint yellow 'Keep Clear' grid boxes; increase penalty for parking within 15 meters of any traffic light."
        }
    else:
        return {
            "category": "Commercial Area Spillover",
            "diagnostic": "High volume of generic WRONG/NO PARKING violations. Driven by shoppers and delivery agents due to lack of local parking spots.",
            "recommendation": "Introduce smart paid parking sensors; allocate dedicated delivery cargo zones; partner with commercial malls for shared parking."
        }
