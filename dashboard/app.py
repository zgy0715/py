import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pandas as pd
import streamlit as st
from dashboard.config import PAGE_TITLE, PAGE_ICON, LAYOUT
from dashboard.data.api_loader import load_all
from dashboard.data.loader import load_redis_hotspot
from dashboard.views.overview import render as render_overview
from dashboard.views.github_trending import render as render_github_trending
from dashboard.views.export import render as render_export
from dashboard.views.multi_source import render as render_multi_source
from dashboard.views.trends import render as render_trends

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded",
)

# Inject dark glass theme CSS (inline to avoid import caching issues)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+SC:wght@300;400;500;600;700;900&display=swap');

.stApp {
  background: #06060D;
  font-family: 'Noto Sans SC', system-ui, -apple-system, sans-serif;
}
.main .block-container {
  padding-top: 2rem;
  max-width: 100%;
}

h1, h2, h3, h4 {
  font-family: 'Noto Sans SC', system-ui, -apple-system, sans-serif !important;
  color: #EDEDF5 !important;
  font-weight: 700 !important;
  letter-spacing: -0.3px !important;
}
h1 { font-size: 28px !important; }
h2 { font-size: 22px !important; }
h3 { font-size: 17px !important; }

/* All text */
.stMarkdown, .stTitle, .stHeader, .stSubheader, .stCaption, .stText {
  color: #EDEDF5 !important;
  font-family: 'Noto Sans SC', system-ui, -apple-system, sans-serif !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
  background: rgba(12,12,26,0.96);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] * {
  color: #EDEDF5 !important;
  font-family: 'Noto Sans SC', system-ui, -apple-system, sans-serif !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  font-weight: 700 !important;
}
[data-testid="stSidebar"] .stButton > button {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  color: #9494B8 !important;
  border-radius: 10px !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
  font-family: 'Noto Sans SC', sans-serif !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(255,255,255,0.08) !important;
  color: #EDEDF5 !important;
  border-color: rgba(255,255,255,0.15) !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #00D4FF, #06B6D4) !important;
  color: #000 !important;
  border: none !important;
  font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
  opacity: 0.9 !important;
}
[data-testid="stSidebar"] hr {
  border-color: rgba(255,255,255,0.06) !important;
}

/* Metric cards */
[data-testid="stMetric"] {
  background: rgba(18,18,36,0.7);
  backdrop-filter: blur(24px) saturate(150%);
  -webkit-backdrop-filter: blur(24px) saturate(150%);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px;
  padding: 18px 20px;
  transition: all 0.25s ease;
}
[data-testid="stMetric"]:hover {
  border-color: rgba(255,255,255,0.12);
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
[data-testid="stMetric"] label {
  font-family: 'Noto Sans SC', sans-serif !important;
  font-size: 12px !important;
  color: #9494B8 !important;
  font-weight: 500 !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
  font-family: 'JetBrains Mono', 'Consolas', monospace !important;
  font-size: 28px !important;
  font-weight: 700 !important;
  color: #EDEDF5 !important;
}

/* Buttons */
.stButton > button {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  color: #9494B8 !important;
  border-radius: 10px !important;
  font-weight: 500 !important;
  transition: all 0.2s ease !important;
  font-family: 'Noto Sans SC', sans-serif !important;
}
.stButton > button:hover {
  background: rgba(255,255,255,0.08) !important;
  color: #EDEDF5 !important;
  border-color: rgba(255,255,255,0.15) !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #00D4FF, #06B6D4) !important;
  color: #000 !important;
  border: none !important;
  font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
  opacity: 0.9 !important;
}

/* Dataframe / Table */
[data-testid="stDataFrame"], .stDataFrame {
  background: rgba(18,18,36,0.7) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 14px !important;
  overflow: hidden !important;
}
[data-testid="stDataFrame"] th, .stDataFrame th {
  background: rgba(255,255,255,0.04) !important;
  color: #9494B8 !important;
  font-family: 'Noto Sans SC', sans-serif !important;
  font-weight: 600 !important;
  border-bottom: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stDataFrame"] td, .stDataFrame td {
  color: #9494B8 !important;
  font-family: 'JetBrains Mono', 'Consolas', monospace !important;
  font-size: 12px !important;
  border-bottom: 1px solid rgba(255,255,255,0.04) !important;
}
[data-testid="stDataFrame"] tr:hover td, .stDataFrame tr:hover td {
  background: rgba(255,255,255,0.02) !important;
}

/* Tabs */
[data-testid="stTabs"] { background: transparent !important; }
[data-testid="stTabs"] [role="tablist"] {
  background: rgba(255,255,255,0.02) !important;
  border-radius: 10px !important;
  padding: 4px !important;
  gap: 2px !important;
}
[data-testid="stTabs"] [role="tab"] {
  background: transparent !important;
  color: #9494B8 !important;
  border-radius: 8px !important;
  font-family: 'Noto Sans SC', sans-serif !important;
  font-weight: 500 !important;
  padding: 8px 18px !important;
  border: none !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: rgba(255,255,255,0.08) !important;
  color: #EDEDF5 !important;
}

/* Select / Multiselect / Input */
[data-testid="stSelectbox"], [data-testid="stMultiSelect"], .stTextInput input {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 8px !important;
  color: #EDEDF5 !important;
}

/* Expander */
[data-testid="stExpander"] {
  background: rgba(18,18,36,0.5) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 14px !important;
}
[data-testid="stExpander"] summary {
  color: #EDEDF5 !important;
  font-weight: 600 !important;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* Info/Warning boxes */
[data-testid="stInfo"], [data-testid="stWarning"] {
  background: rgba(18,18,36,0.5) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 10px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.06); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.12); }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600, show_spinner="正在通过 API 加载数据...")
def _init_data():
    return load_all()

if "data_loaded" not in st.session_state:
    sources, tier, df_csv, df_mongo, df_all = _init_data()
    # Coerce numeric columns to avoid object-dtype nlargest errors
    for col in ["stars", "stars_since", "forks", "hot_score"]:
        if col in df_all.columns:
            df_all[col] = pd.to_numeric(df_all[col], errors='coerce').fillna(0)
    st.session_state.sources = sources
    st.session_state.tier = tier
    st.session_state.df_csv = df_csv
    st.session_state.df_mongo = df_mongo
    st.session_state.df_redis = load_redis_hotspot()
    st.session_state.df_all = df_all
    st.session_state.data_loaded = True

# ---- sidebar ----
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
      <div style="width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#00D4FF,#06B6D4);
        display:flex;align-items:center;justify-content:center;box-shadow:0 0 16px rgba(0,212,255,0.2)">
        <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="3" fill="#000" opacity="0.5"/>
          <circle cx="10" cy="10" r="7" stroke="#000" stroke-width="2" opacity="0.3"/>
        </svg>
      </div>
      <span style="font-size:18px;font-weight:700;letter-spacing:-0.3px">Hotspot</span>
    </div>
    """, unsafe_allow_html=True)

    tier = st.session_state.tier
    tier_labels = {
        0: "No data source",
        1: "CSV (Tier 1)",
        2: "CSV + MongoDB (Tier 2)",
        3: "CSV + MongoDB + Redis (Tier 3)",
    }
    tier_colors = {0: "#EF4444", 1: "#00D4FF", 2: "#A855F7", 3: "#10B981"}
    tc = tier_colors.get(tier, "#EF4444")
    st.markdown(f"""
    <div style="padding:8px 12px;border-radius:8px;background:rgba(255,255,255,0.03);
      border:1px solid rgba(255,255,255,0.06);margin:8px 0 16px 0;font-size:12px;
      display:flex;align-items:center;gap:8px">
      <span style="width:8px;height:8px;border-radius:50%;background:{tc};display:inline-block"></span>
      {tier_labels.get(tier, tier_labels[0])}
    </div>
    """, unsafe_allow_html=True)

    pages = {
        "Overview": render_overview,
        "GitHub Trending": render_github_trending,
    }
    if tier >= 2:
        pages["Multi-Source"] = render_multi_source
        pages["Trends"] = render_trends
    pages["Export"] = render_export

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Overview"

    for label in pages:
        is_current = st.session_state.current_page == label
        btn_type = "primary" if is_current else "secondary"
        if st.button(label, use_container_width=True, key=f"nav_{label}", type=btn_type):
            st.session_state.current_page = label

    st.divider()
    st.caption(f"{len(st.session_state.df_all)} records · Tier {tier}")

render_fn = pages[st.session_state.current_page]
render_fn(st.session_state)
