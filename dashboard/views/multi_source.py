import pandas as pd
import streamlit as st

from ..components.charts import (
    bar_chart_top, pie_chart, scatter_chart, histogram, box_chart, empty_chart,
)
from ..components.filters import multi_source_filters
from ..components.metrics import kpi_row
from ..config import COLOR_MAP


def render(session_state):
    st.header("Multi-Source Compare")

    df = session_state.df_all
    if df.empty:
        st.warning("No data available.")
        return

    if "source" not in df.columns or df["source"].nunique() < 2:
        st.info("Multi-source comparison requires MongoDB multi-platform data.")
        return

    selected_sources = multi_source_filters(df, key_prefix="ms_")
    filtered = df[df["source"].isin(selected_sources)] if selected_sources else df

    render_kpi_section(filtered)
    render_ranking_section(filtered)
    render_distribution_section(filtered)


def render_kpi_section(df):
    metrics = []
    for source in sorted(df["source"].unique()):
        subset = df[df["source"] == source]
        metrics.append((f"{source.upper()} Count", len(subset), None))
        if "hot_score" in subset.columns:
            avg = f"{subset['hot_score'].mean():.1f}"
            metrics.append((f"{source.upper()} Avg Hot Score", avg, None))
    kpi_row(metrics)

    if "hot_score" in df.columns and "source" in df.columns:
        st.caption("Note: Hot scores use different formulas per source and are not directly comparable across platforms.")


def render_ranking_section(df):
    st.subheader("Global Hot Score Top 20")
    if "hot_score" not in df.columns:
        st.info("No hot score data.")
        return

    dedup_keys = [c for c in ["unique_id", "name", "title"] if c in df.columns]
    dedup = df.drop_duplicates(subset=[dedup_keys[0]]) if dedup_keys else df
    name_col = "name"
    if "name" in dedup.columns and "title" in dedup.columns:
        dedup = dedup.copy()
        dedup["display_name"] = dedup["name"].fillna(dedup["title"])
        name_col = "display_name"
    elif "title" in dedup.columns and "name" not in dedup.columns:
        name_col = "title"

    fig = bar_chart_top(
        dedup.nlargest(20, "hot_score"), "hot_score",
        name_col if name_col in dedup.columns else dedup.columns[0],
        "Global Top 20 by Hot Score", color="source", top_n=20,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_distribution_section(df):
    if "hot_score" not in df.columns:
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Hot Score Distribution")
        fig = histogram(df, x="hot_score", color="source",
                        title="Hot Score Distribution by Source", barmode="overlay")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Hot Score Box Plot")
        fig = box_chart(df, x="source", y="hot_score", color="source",
                        title="Hot Score Box Plot by Source")
        st.plotly_chart(fig, use_container_width=True)



