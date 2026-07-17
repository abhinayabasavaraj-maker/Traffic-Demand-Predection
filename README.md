<div align="center">

# 🅿️ ParkPulse

### Parking-Induced Congestion Intelligence

**Flipkart GRID 7.0 · PS1**

*Bangalore loses traffic flow to illegal parking every day — nobody knows where it's worst, what it'll look like tomorrow, or where to send a patrol. ParkPulse answers all three.*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://huggingface.co/spaces/Adit555/ParkPulse)
[![LightGBM](https://img.shields.io/badge/LightGBM-Forecasting-success?logo=leaflet&logoColor=white)](https://github.com/microsoft/LightGBM)
[![Offline](https://img.shields.io/badge/Runs-100%25%20Offline-blue)](#tech-stack)

**[▶ Try the Live Dashboard](https://huggingface.co/spaces/Adit555/ParkPulse)** · **[View Source](https://github.com/aditcool-dev/ParkPulse)** · **[Full Methodology](docs/TECHNICAL_OVERVIEW.md)**

</div>

---

## The Problem → The Pipeline → The Payoff

Enforcement teams currently react to parking complaints one at a time, with no city-wide view of where the problem is concentrated, how it's trending, or how to deploy limited patrol units efficiently.

**ParkPulse turns 298K raw violation records into a same-day decision tool** — in three explainable stages, with zero black boxes:

```
   RAW DATA              RANK & FORECAST              ACT
┌──────────────┐      ┌────────────────────┐      ┌──────────────────┐
│ 298,450      │ ──▶  │ 164 named junctions │ ──▶  │ MILP-optimized    │
│ violations   │      │ scored + forecast   │      │ patrol allocation │
│ (cleaned)    │      │ next-day volume     │      │ in <1 second      │
└──────────────┘      └────────────────────┘      └──────────────────┘
```

---

## ⚡ What It Does

| Stage | Module | Output |
|---|---|---|
| 🧹 Clean & normalise | `pipeline/clean.py` | 298,450 records, UTC→IST corrected, severity-weighted |
| 📍 Geographic clustering | `pipeline/hotspots.py` | 236 DBSCAN clusters across Bangalore |
| 🏆 Named-hotspot ranking | `models/ppi.py` | PPI score + tier for 164 real junctions |
| 📈 Violation forecast | `models/forecast.py` | LightGBM next-day predictions, top-15 junctions |
| 🚓 Patrol allocation | `models/allocation.py` | MILP unit assignment, optimal in under 1 second |
| 📊 Dashboard | `dashboard/app.py` | 4-screen Streamlit app |

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt

# Place the raw CSV in data/raw/ before running
python -m src.pipeline.run_all      # ~20 seconds end-to-end

streamlit run src/dashboard/app.py
```

One command regenerates every artifact from the raw CSV. The dashboard itself reads precomputed Parquet files — **no live model inference during the demo**, so judges see instant load times, not spinners.

> Prefer not to install anything? **[Open the live Space →](https://huggingface.co/spaces/Adit555/ParkPulse)**

---

## 📐 Why These Numbers Matter

| Metric | Value | Why it matters |
|---|---|---|
| Dataset | 298,450 records · Nov 2023–Apr 2024 · Bangalore | Six months of real enforcement data |
| Validated records | 115,400 (`approved` status only) | Only confirmed violations drive scoring |
| Named junctions ranked | 164 | 49.5% of records lacked a usable junction name — handled explicitly, not dropped silently |
| DBSCAN clusters | 236 geographic hotspots | Captures unnamed/informal hotspots too |
| Forecast MAE | **11.40** violations/day | Beats the 7-day rolling baseline (12.33) on held-out Mar 2024 data |
| PPI sensitivity | 14–15/15 top-15 overlap | Rankings barely move under ±10% weight perturbation — not a fragile metric |
| Pipeline runtime | ~20 seconds | Full reproducibility on a laptop, no cluster needed |
| Dashboard load | <2 seconds | Everything precomputed — built for live judging |

---

## 🖥️ Dashboard Walkthrough

**1 · Overview** — Bangalore map with PPI-tiered hotspot circles, top-5 ranked list, full junction table, filterable by police station.

**2 · Hotspot Detail** — Per-junction drill-down: PPI component breakdown, hourly/day-of-week enforcement patterns, vehicle type mix, forecast with backtested error band.

**3 · Patrol Allocation** — Set available patrol units → MILP distributes them optimally in under a second, with a numbered deployment map.

**4 · Data & Methodology** — Cleaning steps, PPI formula, severity weights, backtest results, known limitations — written to **pre-empt judge questions before they're asked.**

---

## 🧠 Design Decisions (Read This Before Asking "Why Not X?")

**Why not reinforcement learning?**
RL needs outcome feedback — did violations actually drop after a patrol was deployed? That data doesn't exist yet. MILP is fully explainable, solves in milliseconds, and is the right tool *until* post-deployment outcome data is collected. RL is the natural v2, not a thing we missed.

**Why is PPI called a "proxy," not a ground-truth metric?**
No speed or traffic-volume data exists in this dataset. PPI is built from violation counts, severity weights, repeat offenders, and persistence — a legitimate enforcement-priority signal, but **not** a measured traffic-impact number. Labelled honestly everywhere it appears, including the dashboard itself.

**Why is 49.5% of the data "unattributable"?**
The raw data contains `"No Junction"` as a literal field value for violations with no recorded location name. These span all 54 police stations and every part of the city — not a real place. They still feed the geographic DBSCAN clustering (lat/long-based) but are excluded from the named-hotspot ranking. Fully documented on the Methodology page, not buried.

---

## 🗂️ Project Structure

```
src/
├── config.py               # Single source of truth for all parameters
├── pipeline/
│   ├── clean.py            # Phase 1 — parse, timezone fix, validation filter
│   ├── aggregate.py        # Phase 2 — per-junction daily aggregation
│   ├── hotspots.py         # Phase 2 — DBSCAN geographic clustering
│   └── run_all.py          # Entry point — runs all phases in order
├── models/
│   ├── ppi.py              # Parking Pressure Index + sensitivity check
│   ├── forecast.py         # LightGBM/XGBoost + naive baselines
│   └── allocation.py       # MILP patrol allocation (PuLP)
└── dashboard/
    ├── app.py              # Streamlit app — 4 pages
    ├── components.py       # Charts, maps, badges
    └── data_loader.py      # Cached artifact readers

data/
├── raw/                    # Place source CSV here (gitignored)
└── processed/              # Pipeline outputs (gitignored, regenerable)

docs/
└── TECHNICAL_OVERVIEW.md   # Full methodology, module specs, metric table
```

---

## 🛠️ Tech Stack

`Python 3.11` · `pandas` · `scikit-learn (DBSCAN)` · `LightGBM` · `XGBoost` · `PuLP` · `Streamlit` · `Folium` · `Plotly` · `PyArrow`

**100% open-source. No paid API keys. Runs fully offline.**

---

## 📚 Documentation

Full methodology, module specs, severity weight table, and metric details live in **[`docs/TECHNICAL_OVERVIEW.md`](docs/TECHNICAL_OVERVIEW.md)** — built so a judge can self-serve every "how does this work" question without interrupting the demo.

---

<div align="center">

**Built for Flipkart GRIDLOCK 7.0 · PS1** — turning six months of parking violations into next-day, explainable enforcement decisions.

</div>