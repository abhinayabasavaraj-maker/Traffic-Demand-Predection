---
title: ParkPulse
emoji: 🚦
colorFrom: red
colorTo: gray
sdk: streamlit
sdk_version: "1.37.1"
app_file: app.py
pinned: false
short_description: Parking enforcement intelligence — hotspot detection, PPI scoring, patrol allocation
---

# ParkPulse — Parking Enforcement Intelligence

**Flipkart GRID · Problem Statement 1 · Bangalore**

ParkPulse turns raw parking violation records into actionable enforcement decisions through a purpose-built dispatch-style dashboard — hotspot detection, priority ranking, next-day forecasting, and patrol allocation.

---

## Dashboard

### Overview
Interactive Bangalore map showing 164 named illegal-parking hotspots colored by risk tier (Critical / High / Medium / Low). Circle size scales with daily violation frequency. Top-5 ranked list with the driving reason per hotspot. Filter the entire view by police station.

### Hotspot Detail
Click any junction to see its full profile — PPI component breakdown (frequency, severity, repeat offenders, persistence), hour-of-day and day-of-week enforcement patterns, vehicle type mix, and a violation forecast strip with backtested MAE.

### Patrol Allocation Simulator
Set available patrol units (1–30). A Mixed-Integer Linear Program distributes them optimally across predicted hotspots in under a second. Critical-tier junctions are guaranteed at least one unit. Deployment map updates live.

### Data & Methodology
Full cleaning steps, PPI formula, severity weight table, backtest metrics, and known limitations — written to be honest about what the system can and cannot claim.

---

## How It Works

```
298,450 violation records  (Nov 2023 – Apr 2024 · Bangalore)
        ↓
Clean   UTC→IST correction · approved-only filter · multi-label parsing
        ↓
Cluster DBSCAN on lat/lon  → 236 geographic hotspots
        ↓
Score   Parking Pressure Index (PPI)
        frequency × 0.4 + severity × 0.3 + repeat × 0.2 + persistence × 0.1
        ↓
Forecast  LightGBM · MAE 11.40/day · beats 7-day rolling baseline
        ↓
Allocate  MILP (PuLP) · optimal in <1 second · fully explainable
```

---

## Key Findings

- **49.5% of records (147,880)** had no usable junction attribution — handled with an explicit fallback, not dropped
- Timestamps are UTC. Converted to IST, enforcement peaks at **10:00 IST** — morning patrol sweeps, not when vehicles actually park
- **28.9%** of validation statuses were rejected/duplicate — all scoring uses `approved` records only
- Top hotspot: **Btp051 - Safina Plaza Junction** · 27.3 violations/day · Critical tier
- PPI weight sensitivity check: **STABLE** — top-15 ranking changes by at most 1 junction across all ±10% weight perturbations

---

## Honest Limitations

- PPI is a **priority proxy**, not a measured traffic-flow metric (no speed/volume data in this dataset)
- Forecast covers only the top-15 highest-volume junctions; low-history junctions are explicitly excluded
- Historical system only — no real-time feed; live enforcement triggering requires a traffic-flow API integration

---

## Tech Stack

Streamlit · Folium · Plotly · LightGBM · PuLP · pandas · scikit-learn · PyArrow

All open-source. No API keys required.

---

*Source code and full pipeline on [GitHub](https://github.com/aditcool-dev/ParkPulse)*
