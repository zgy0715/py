import pandas as pd
import streamlit as st

from ..components.charts import (
    bar_chart_top, histogram, density_heatmap,
    scatter_chart, empty_chart,
)
from ..config import COLOR_MAP

PERIOD_LABELS = {"daily": "Today", "weekly": "This Week", "monthly": "This Month", "all": "All Sources"}


def render(session_state):
    st.header("Trends Analysis")

    df = session_state.df_all
    if df.empty:
        st.warning("No data available.")
        return

    # Period comparison KPIs
    if "since" in df.columns:
        st.subheader("Three Period KPI Comparison")
        cols = st.columns(3)
        for idx, period in enumerate(["daily", "weekly", "monthly"]):
            pdf = df[df["since"] == period]
            name_col = "name" if "name" in pdf.columns else "title"
            score_col = "stars_since" if "stars_since" in pdf.columns else "hot_score"
            dedup = pdf.drop_duplicates(subset=[name_col]) if name_col in pdf.columns else pdf

            with cols[idx]:
                st.metric(f"{PERIOD_LABELS[period]} · Projects", len(dedup))
                if score_col in dedup.columns and not dedup.empty:
                    st.metric(
                        f"{PERIOD_LABELS[period]} · Avg New Stars",
                        f"{dedup[score_col].mean():.0f}",
                    )
        st.divider()

    # Project count comparison
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Project Count per Period")
        if "since" in df.columns:
            since_counts = df["since"].value_counts().reset_index()
            since_counts.columns = ["since", "count"]
            since_counts["since"] = since_counts["since"].map(PERIOD_LABELS).fillna(since_counts["since"].astype(str))
            fig = bar_chart_top(since_counts, "count", "since", "Projects per Period", top_n=len(since_counts))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(empty_chart(), use_container_width=True)

    with col2:
        st.subheader("Avg New Stars per Period")
        if "since" in df.columns and "stars_since" in df.columns:
            avg = df.groupby("since")["stars_since"].mean().reset_index()
            avg.columns = ["since", "avg_stars"]
            avg["since"] = avg["since"].map(PERIOD_LABELS).fillna(avg["since"].astype(str))
            avg = avg.sort_values("avg_stars", ascending=True)
            fig = bar_chart_top(avg, "avg_stars", "since", "Avg New Stars per Period", top_n=len(avg))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(empty_chart(), use_container_width=True)

    # Language trend comparison
    if "language" in df.columns and "since" in df.columns:
        st.subheader("Top Languages per Period")
        cols = st.columns(3)
        for idx, period in enumerate(["daily", "weekly", "monthly"]):
            pdf = df[df["since"] == period]
            dedup = pdf.drop_duplicates(subset=["name"] if "name" in pdf.columns else ["title"])
            with cols[idx]:
                lang_counts = dedup["language"].value_counts().reset_index()
                lang_counts.columns = ["language", "count"]
                fig = bar_chart_top(
                    lang_counts.head(8), "count", "language",
                    f"{PERIOD_LABELS[period]} · Language Top 8", top_n=8,
                )
                st.plotly_chart(fig, use_container_width=True)

    # Language x Period heatmap
    if "since" in df.columns and "language" in df.columns:
        st.subheader("Language x Period Heatmap")
        dedup = df.drop_duplicates(subset=["name"] if "name" in df.columns else ["title"]).copy()
        dedup["since"] = dedup["since"].map(PERIOD_LABELS).fillna(dedup["since"].astype(str))
        fig = density_heatmap(dedup, x="since", y="language", title="Language Distribution Heatmap")
        st.plotly_chart(fig, use_container_width=True)

    # Stars vs Forks by period
    if "stars" in df.columns and "forks" in df.columns and "since" in df.columns:
        st.subheader("Stars vs Forks (by Period)")
        dedup = df.drop_duplicates(subset=["name"] if "name" in df.columns else ["title"]).copy()
        name_col = "name" if "name" in dedup.columns else "title"
        dedup["since"] = dedup["since"].map(PERIOD_LABELS).fillna(dedup["since"].astype(str))
        fig = scatter_chart(
            dedup.head(300), x="stars", y="forks", color="since",
            title="Stars vs Forks (colored by period)", hover_name=name_col,
        )
        st.plotly_chart(fig, use_container_width=True)
