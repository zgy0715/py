import datetime

import pandas as pd
import streamlit as st

from ..components.charts import (
    bar_chart_top, pie_chart, line_chart, scatter_chart, empty_chart,
)
from ..components.metrics import kpi_row
from ..config import COLOR_MAP

PERIODS = ["daily", "weekly", "monthly"]
PERIOD_LABELS = {"daily": "Today", "weekly": "This Week", "monthly": "This Month"}


def render(session_state):
    st.header("Overview")

    df = session_state.df_all
    if df.empty:
        st.warning("No data available. Run the crawler first.")
        return

    github_df = df[df["source"] == "github"] if "source" in df.columns else df
    total = len(github_df)
    total_stars = int(github_df["stars"].sum()) if "stars" in github_df.columns else 0
    total_langs = github_df["language"].nunique() if "language" in github_df.columns else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Projects", total)
    with col2:
        st.metric("Total Stars", f"{total_stars:,}")
    with col3:
        st.metric("Languages", total_langs)
    with col4:
        avg_hot = f"{github_df['hot_score'].mean():.0f}" if "hot_score" in github_df.columns else "N/A"
        st.metric("Avg Hot Score", avg_hot)

    st.divider()

    # ---- Period cards ----
    st.subheader("Three Periods Overview")
    cols = st.columns(3)

    for idx, period in enumerate(PERIODS):
        period_df = github_df[github_df["since"] == period] if "since" in github_df.columns else github_df
        name_col = "name" if "name" in period_df.columns else "title"
        score_col = "stars_since" if "stars_since" in period_df.columns else "hot_score"
        dedup = period_df.drop_duplicates(subset=[name_col]) if name_col in period_df.columns else period_df

        with cols[idx]:
            count = len(dedup)
            period_total_stars = int(dedup["stars"].sum()) if "stars" in dedup.columns else 0
            period_avg = f"{dedup[score_col].mean():.0f}" if score_col in dedup.columns and not dedup.empty else "N/A"

            st.markdown(f"### {PERIOD_LABELS[period]}")
            st.caption(f"{count} projects")
            st.metric("Total Stars", f"{period_total_stars:,}")
            st.metric("Avg New Stars", period_avg)

            if not dedup.empty and score_col in dedup.columns:
                top3 = dedup.nlargest(3, score_col)
                st.markdown("**Top 3:**")
                for i, (_, row) in enumerate(top3.iterrows()):
                    name = row.get(name_col, "N/A")
                    score = row.get(score_col, 0)
                    st.caption(f"{i+1}. {name} (+{score})")

    st.divider()

    # ---- Charts ----
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Language Distribution")
        if "language" in github_df.columns:
            lang_counts = github_df.drop_duplicates(subset=["name"] if "name" in github_df.columns else ["title"])
            lang_counts = lang_counts["language"].value_counts().reset_index()
            lang_counts.columns = ["language", "count"]
            lang_counts = lang_counts.head(12)
            fig = pie_chart(lang_counts, "language", "count", "Language Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(empty_chart("No language data"), use_container_width=True)

    with col2:
        st.subheader("Top 15 Hot Projects")
        if "hot_score" in github_df.columns and not github_df.empty:
            dedup = github_df.drop_duplicates(subset=["name"] if "name" in github_df.columns else ["title"])
            name_col = "name" if "name" in dedup.columns else "title"
            fig = bar_chart_top(dedup, "hot_score", name_col, "Top 15 by Hot Score", top_n=15)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(empty_chart(), use_container_width=True)

    # ---- Stars vs Fork ----
    if "stars" in github_df.columns and "forks" in github_df.columns:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Stars vs Forks")
            dedup = github_df.drop_duplicates(subset=["name"] if "name" in github_df.columns else ["title"])
            name_col = "name" if "name" in dedup.columns else "title"
            fig = scatter_chart(
                dedup.head(200), x="stars", y="forks", color="language",
                title="Stars vs Forks (by language)", hover_name=name_col,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Period Counts")
            if "since" in github_df.columns:
                since_counts = github_df["since"].value_counts().reset_index()
                since_counts.columns = ["since", "count"]
                since_counts["since"] = since_counts["since"].map(PERIOD_LABELS)
                fig = bar_chart_top(since_counts, "count", "since", "Projects per Period", top_n=3)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.plotly_chart(empty_chart(), use_container_width=True)

    # ---- Time trend ----
    if "crawl_time" in github_df.columns:
        dates = github_df["crawl_time"].dt.date.dropna()
        if len(dates.unique()) >= 2:
            st.divider()
            st.subheader("Recent Trend")
            recent = github_df.copy()
            recent["date"] = recent["crawl_time"].dt.date
            if "since" in recent.columns:
                daily_trend = recent.groupby(["date", "since"]).size().reset_index(name="count")
                daily_trend["since"] = daily_trend["since"].map(PERIOD_LABELS)
                fig = line_chart(daily_trend, "date", "count", "since", "Daily Collection Trend")
                st.plotly_chart(fig, use_container_width=True)
