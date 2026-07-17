"""
ParkPulse AI — Master CSS / style injection.
All visual theming lives here. Import inject_css() once at app startup.
"""

MASTER_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Poppins:wght@400;600;700;800&display=swap');

/* ── Reset & base ─────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: #0B1020 !important;
    font-family: 'Inter', sans-serif !important;
    color: #E2E8F0 !important;
}

/* Hide default Streamlit chrome */
#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stSidebar"] > div:first-child { background: #0D1528 !important; border-right: 1px solid rgba(0,217,255,0.12) !important; }
[data-testid="stSidebarNav"] { display: none !important; }

/* Main content area */
[data-testid="stMain"] { background: #0B1020 !important; }
.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Scrollbar ─────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0B1020; }
::-webkit-scrollbar-thumb { background: rgba(0,217,255,0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,217,255,0.6); }

/* ── Top header bar ────────────────────────────────────────────────────────── */
.pp-header {
    background: linear-gradient(135deg, #0D1528 0%, #111827 50%, #0D1528 100%);
    border-bottom: 1px solid rgba(0,217,255,0.15);
    padding: 12px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 1000;
    backdrop-filter: blur(20px);
    box-shadow: 0 4px 30px rgba(0,0,0,0.4);
}
.pp-logo {
    display: flex;
    align-items: center;
    gap: 10px;
}
.pp-logo-text {
    font-family: 'Poppins', sans-serif;
    font-size: 1.45rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00D9FF, #7C4DFF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
}
.pp-logo-sub {
    font-size: 0.65rem;
    color: rgba(0,217,255,0.6);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: -4px;
}
.pp-header-center {
    display: flex;
    align-items: center;
    gap: 20px;
}
.pp-live-badge {
    display: flex;
    align-items: center;
    gap: 7px;
    background: rgba(0,230,118,0.1);
    border: 1px solid rgba(0,230,118,0.3);
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 0.75rem;
    color: #00E676;
    font-weight: 600;
}
.pp-live-dot {
    width: 7px;
    height: 7px;
    background: #00E676;
    border-radius: 50%;
    animation: pulse-green 2s infinite;
    box-shadow: 0 0 8px #00E676;
}
@keyframes pulse-green {
    0%, 100% { opacity:1; transform:scale(1); box-shadow:0 0 8px #00E676; }
    50% { opacity:0.7; transform:scale(1.3); box-shadow:0 0 16px #00E676; }
}
.pp-header-right {
    display: flex;
    align-items: center;
    gap: 16px;
}
.pp-timestamp {
    font-size: 0.72rem;
    color: rgba(226,232,240,0.5);
    font-family: 'Inter', monospace;
}

/* ── Sidebar ───────────────────────────────────────────────────────────────── */
.pp-sidebar-logo {
    padding: 20px 18px 12px;
    border-bottom: 1px solid rgba(0,217,255,0.08);
    margin-bottom: 8px;
}
.pp-sidebar-logo-text {
    font-family: 'Poppins', sans-serif;
    font-size: 1.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00D9FF, #7C4DFF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.pp-sidebar-section {
    padding: 6px 12px;
    font-size: 0.62rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(226,232,240,0.3);
    font-weight: 600;
    margin-top: 8px;
}
.pp-nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 16px;
    margin: 2px 8px;
    border-radius: 10px;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 500;
    color: rgba(226,232,240,0.65);
    transition: all 0.2s ease;
    border: 1px solid transparent;
}
.pp-nav-item:hover {
    background: rgba(0,217,255,0.06);
    color: #E2E8F0;
    border-color: rgba(0,217,255,0.12);
}
.pp-nav-item.active {
    background: linear-gradient(135deg, rgba(0,217,255,0.12), rgba(124,77,255,0.12));
    color: #00D9FF;
    border-color: rgba(0,217,255,0.25);
    font-weight: 600;
    box-shadow: 0 0 20px rgba(0,217,255,0.08);
}
.pp-nav-icon { font-size: 1rem; width: 20px; text-align: center; }

/* ── KPI Cards ─────────────────────────────────────────────────────────────── */
.pp-kpi-card {
    background: #131A2B;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
    cursor: default;
}
.pp-kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 20px 20px 0 0;
}
.pp-kpi-card.cyan::before  { background: linear-gradient(90deg, #00D9FF, #7C4DFF); }
.pp-kpi-card.emerald::before { background: linear-gradient(90deg, #00E676, #00D9FF); }
.pp-kpi-card.orange::before { background: linear-gradient(90deg, #FFB020, #FF5252); }
.pp-kpi-card.red::before    { background: linear-gradient(90deg, #FF5252, #FF8A80); }
.pp-kpi-card.purple::before { background: linear-gradient(90deg, #7C4DFF, #00D9FF); }
.pp-kpi-card.teal::before   { background: linear-gradient(90deg, #00E676, #7C4DFF); }

.pp-kpi-card:hover {
    border-color: rgba(0,217,255,0.2);
    transform: translateY(-3px);
    box-shadow: 0 8px 40px rgba(0,217,255,0.08);
}
.pp-kpi-icon {
    font-size: 1.4rem;
    margin-bottom: 10px;
    opacity: 0.9;
}
.pp-kpi-label {
    font-size: 0.72rem;
    color: rgba(226,232,240,0.5);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 600;
    margin-bottom: 6px;
}
.pp-kpi-value {
    font-family: 'Poppins', sans-serif;
    font-size: 1.9rem;
    font-weight: 800;
    color: #E2E8F0;
    line-height: 1;
    margin-bottom: 6px;
}
.pp-kpi-value.cyan   { color: #00D9FF; }
.pp-kpi-value.emerald { color: #00E676; }
.pp-kpi-value.orange { color: #FFB020; }
.pp-kpi-value.red    { color: #FF5252; }
.pp-kpi-value.purple { color: #7C4DFF; }

.pp-kpi-trend {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 8px;
}
.pp-kpi-trend.up   { background: rgba(0,230,118,0.15); color: #00E676; }
.pp-kpi-trend.down { background: rgba(255,82,82,0.15); color: #FF5252; }
.pp-kpi-trend.neutral { background: rgba(0,217,255,0.12); color: #00D9FF; }

/* ── Section title ─────────────────────────────────────────────────────────── */
.pp-section-title {
    font-family: 'Poppins', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #E2E8F0;
    margin: 0 0 16px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.pp-section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(0,217,255,0.3), transparent);
    margin-left: 8px;
}

/* ── Glass card ─────────────────────────────────────────────────────────────── */
.pp-glass-card {
    background: rgba(19,26,43,0.8);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 22px;
    margin-bottom: 16px;
    transition: border-color 0.3s;
}
.pp-glass-card:hover {
    border-color: rgba(0,217,255,0.15);
}

/* ── Hotspot rank table row ────────────────────────────────────────────────── */
.pp-hotspot-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    margin: 4px 0;
    border-radius: 12px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.05);
    transition: all 0.2s;
    cursor: pointer;
}
.pp-hotspot-row:hover {
    background: rgba(0,217,255,0.05);
    border-color: rgba(0,217,255,0.15);
    transform: translateX(4px);
}
.pp-rank-badge {
    min-width: 26px;
    height: 26px;
    border-radius: 8px;
    background: rgba(0,217,255,0.1);
    color: #00D9FF;
    font-size: 0.72rem;
    font-weight: 700;
    display: flex; align-items: center; justify-content: center;
}
.pp-tier-pill {
    padding: 3px 9px;
    border-radius: 20px;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.pp-tier-pill.Critical { background: rgba(255,82,82,0.2); color: #FF5252; border: 1px solid rgba(255,82,82,0.3); }
.pp-tier-pill.High     { background: rgba(255,176,32,0.2); color: #FFB020; border: 1px solid rgba(255,176,32,0.3); }
.pp-tier-pill.Medium   { background: rgba(0,217,255,0.15); color: #00D9FF; border: 1px solid rgba(0,217,255,0.25); }
.pp-tier-pill.Low      { background: rgba(0,230,118,0.15); color: #00E676; border: 1px solid rgba(0,230,118,0.25); }

/* ── Progress bar ──────────────────────────────────────────────────────────── */
.pp-progress-wrap {
    background: rgba(255,255,255,0.05);
    border-radius: 4px;
    height: 5px;
    overflow: hidden;
    flex: 1;
}
.pp-progress-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.8s ease;
}

/* ── Metric mini card ──────────────────────────────────────────────────────── */
.pp-metric-mini {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 14px 16px;
    text-align: center;
    transition: all 0.2s;
}
.pp-metric-mini:hover {
    border-color: rgba(0,217,255,0.2);
    background: rgba(0,217,255,0.04);
}
.pp-metric-mini-val {
    font-family: 'Poppins', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    margin-bottom: 2px;
}
.pp-metric-mini-label {
    font-size: 0.68rem;
    color: rgba(226,232,240,0.45);
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ── Page title ────────────────────────────────────────────────────────────── */
.pp-page-title {
    font-family: 'Poppins', sans-serif;
    font-size: 1.7rem;
    font-weight: 800;
    background: linear-gradient(135deg, #E2E8F0 30%, #00D9FF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 4px;
    line-height: 1.2;
}
.pp-page-sub {
    font-size: 0.8rem;
    color: rgba(226,232,240,0.45);
    margin-bottom: 20px;
}

/* ── Allocation mission card ───────────────────────────────────────────────── */
.pp-mission-card {
    background: linear-gradient(135deg, rgba(0,217,255,0.08), rgba(124,77,255,0.08));
    border: 1px solid rgba(0,217,255,0.2);
    border-radius: 18px;
    padding: 18px 20px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 14px;
    transition: all 0.25s;
}
.pp-mission-card:hover {
    border-color: rgba(0,217,255,0.4);
    background: linear-gradient(135deg, rgba(0,217,255,0.12), rgba(124,77,255,0.12));
    transform: translateY(-2px);
    box-shadow: 0 6px 30px rgba(0,217,255,0.1);
}
.pp-mission-units {
    min-width: 44px;
    height: 44px;
    border-radius: 12px;
    background: linear-gradient(135deg, #00D9FF, #7C4DFF);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Poppins', sans-serif;
    font-size: 1.2rem;
    font-weight: 800;
    color: white;
    box-shadow: 0 4px 16px rgba(0,217,255,0.3);
}
.pp-mission-info { flex: 1; }
.pp-mission-name {
    font-weight: 700;
    font-size: 0.9rem;
    color: #E2E8F0;
    margin-bottom: 2px;
}
.pp-mission-detail {
    font-size: 0.72rem;
    color: rgba(226,232,240,0.45);
}

/* ── Explainability card ───────────────────────────────────────────────────── */
.pp-explain-card {
    background: rgba(124,77,255,0.06);
    border: 1px solid rgba(124,77,255,0.2);
    border-radius: 14px;
    padding: 14px 18px;
    font-size: 0.8rem;
    color: rgba(226,232,240,0.75);
    line-height: 1.6;
}
.pp-explain-card strong { color: #7C4DFF; }

/* ── Scenario sliders ──────────────────────────────────────────────────────── */
[data-testid="stSlider"] > div > div > div { background: #00D9FF !important; }
[data-testid="stSlider"] .rc-slider-track { background: linear-gradient(90deg, #00D9FF, #7C4DFF) !important; }
[data-testid="stSlider"] .rc-slider-handle {
    border-color: #00D9FF !important;
    box-shadow: 0 0 12px rgba(0,217,255,0.5) !important;
}

/* ── Dataframe override ────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
}

/* ── Select box override ───────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: #131A2B !important;
    border-color: rgba(0,217,255,0.2) !important;
    border-radius: 10px !important;
    color: #E2E8F0 !important;
}

/* ── Radio buttons (sidebar nav) ───────────────────────────────────────────── */
[data-testid="stRadio"] > div {
    background: transparent !important;
}
[data-testid="stRadio"] label {
    color: rgba(226,232,240,0.65) !important;
    font-size: 0.85rem !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    color: #00D9FF !important;
}

/* ── Divider ───────────────────────────────────────────────────────────────── */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* ── Info / warning boxes ──────────────────────────────────────────────────── */
[data-testid="stInfo"] {
    background: rgba(0,217,255,0.07) !important;
    border: 1px solid rgba(0,217,255,0.2) !important;
    border-radius: 12px !important;
    color: #E2E8F0 !important;
}
[data-testid="stWarning"] {
    background: rgba(255,176,32,0.07) !important;
    border: 1px solid rgba(255,176,32,0.25) !important;
    border-radius: 12px !important;
}

/* ── Tab override ──────────────────────────────────────────────────────────── */
[data-testid="stTabs"] {
    background: transparent !important;
}
button[data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(226,232,240,0.5) !important;
    border-bottom: 2px solid transparent !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    padding: 8px 16px !important;
    transition: all 0.2s !important;
}
button[data-baseweb="tab"]:hover {
    color: #E2E8F0 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #00D9FF !important;
    border-bottom-color: #00D9FF !important;
}

/* ── Plotly chart backgrounds ──────────────────────────────────────────────── */
.js-plotly-plot .plotly { border-radius: 14px; }

/* ── Animations ─────────────────────────────────────────────────────────────── */
@keyframes fadeInUp {
    from { opacity:0; transform:translateY(16px); }
    to   { opacity:1; transform:translateY(0); }
}
@keyframes shimmer {
    0%   { background-position: -200% 0; }
    100% { background-position:  200% 0; }
}
.pp-fade-in { animation: fadeInUp 0.4s ease forwards; }

/* Gradient border glow on active card */
.pp-glow-card {
    position: relative;
}
.pp-glow-card::after {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 21px;
    background: linear-gradient(135deg, rgba(0,217,255,0.3), rgba(124,77,255,0.3));
    z-index: -1;
    opacity: 0;
    transition: opacity 0.3s;
}
.pp-glow-card:hover::after { opacity: 1; }

/* ── Pipeline step card ────────────────────────────────────────────────────── */
.pp-pipeline-step {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    transition: all 0.25s;
    margin-bottom: 6px;
}
.pp-pipeline-step:hover {
    border-color: rgba(0,217,255,0.25);
    background: rgba(0,217,255,0.04);
}
.pp-pipeline-num {
    min-width: 30px;
    height: 30px;
    border-radius: 8px;
    background: linear-gradient(135deg, rgba(0,217,255,0.2), rgba(124,77,255,0.2));
    color: #00D9FF;
    font-weight: 800;
    font-size: 0.8rem;
    display: flex; align-items: center; justify-content: center;
    border: 1px solid rgba(0,217,255,0.3);
}
.pp-pipeline-arrow {
    text-align: center;
    color: rgba(0,217,255,0.4);
    font-size: 1.1rem;
    margin: 2px 0;
}

/* ── Model card ────────────────────────────────────────────────────────────── */
.pp-model-card {
    background: linear-gradient(135deg, rgba(124,77,255,0.08), rgba(0,217,255,0.05));
    border: 1px solid rgba(124,77,255,0.2);
    border-radius: 18px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s;
}
.pp-model-card:hover {
    border-color: rgba(124,77,255,0.4);
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(124,77,255,0.15);
}
.pp-model-name {
    font-family: 'Poppins', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #7C4DFF;
    margin-bottom: 6px;
}
.pp-model-desc {
    font-size: 0.75rem;
    color: rgba(226,232,240,0.55);
    line-height: 1.5;
}

/* Override Streamlit button */
[data-testid="stButton"] > button {
    background: linear-gradient(135deg, rgba(0,217,255,0.15), rgba(124,77,255,0.15)) !important;
    border: 1px solid rgba(0,217,255,0.3) !important;
    border-radius: 10px !important;
    color: #00D9FF !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    transition: all 0.2s !important;
    padding: 8px 18px !important;
}
[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, rgba(0,217,255,0.25), rgba(124,77,255,0.25)) !important;
    border-color: rgba(0,217,255,0.5) !important;
    box-shadow: 0 4px 20px rgba(0,217,255,0.2) !important;
    transform: translateY(-1px) !important;
}

/* Expander override */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(0,217,255,0.15) !important;
}

/* Page padding */
.pp-page { padding: 20px 28px; }

"""

import streamlit as st


def inject_css() -> None:
    st.markdown(f"<style>{MASTER_CSS}</style>", unsafe_allow_html=True)


# ── Plotly dark theme base ────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94A3B8", size=11),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        linecolor="rgba(255,255,255,0.08)",
        tickfont=dict(color="#64748B"),
        zerolinecolor="rgba(255,255,255,0.05)",
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        linecolor="rgba(255,255,255,0.08)",
        tickfont=dict(color="#64748B"),
        zerolinecolor="rgba(255,255,255,0.05)",
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(255,255,255,0.08)",
        font=dict(color="#94A3B8"),
    ),
    margin=dict(l=12, r=12, t=40, b=12),
    hoverlabel=dict(
        bgcolor="#131A2B",
        bordercolor="rgba(0,217,255,0.3)",
        font=dict(color="#E2E8F0", family="Inter"),
    ),
    title=dict(font=dict(color="#E2E8F0", size=13, family="Poppins"), x=0.01, xanchor="left"),
)
