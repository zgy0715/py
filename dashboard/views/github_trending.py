import pandas as pd
import streamlit as st

from ..components.charts import (
    bar_chart_top, scatter_chart, empty_chart,
)
from ..components.filters import github_filters
from ..config import COLOR_MAP

PERIODS = ["daily", "weekly", "monthly"]
PERIOD_LABELS = {"daily": "Today", "weekly": "This Week", "monthly": "This Month"}


def render(session_state):
    st.header("GitHub Trending")

    df = session_state.df_all
    github_df = df[df["source"] == "github"] if "source" in df.columns else df.copy()

    if github_df.empty:
        st.warning("No GitHub data available.")
        return

    langs, min_stars, search = github_filters(github_df, key_prefix="gh_")

    tabs = st.tabs([PERIOD_LABELS[p] for p in PERIODS])

    for tab, period in zip(tabs, PERIODS):
        with tab:
            period_df = _filter_data(github_df, period, langs, min_stars, search)
            if period_df.empty:
                st.info(f"No matching data for {PERIOD_LABELS[period]}.")
                continue
            render_period_view(period_df, period)


def _filter_data(df, since, langs, min_stars, search):
    filtered = df.copy()
    if "since" in filtered.columns:
        filtered = filtered[filtered["since"] == since]
    if langs:
        filtered = filtered[filtered["language"].isin(langs)]
    if min_stars > 0 and "stars_since" in filtered.columns:
        filtered = filtered[filtered["stars_since"] >= min_stars]
    if search:
        name_col = "name" if "name" in filtered.columns else "title"
        desc_col = "description" if "description" in filtered.columns else None
        mask = filtered[name_col].str.contains(search, case=False, na=False)
        if desc_col and desc_col in filtered.columns:
            mask |= filtered[desc_col].str.contains(search, case=False, na=False)
        filtered = filtered[mask]
    return filtered


def render_period_view(df, period):
    name_col = "name" if "name" in df.columns else "title"
    score_col = "stars_since" if "stars_since" in df.columns else "hot_score"
    dedup = df.drop_duplicates(subset=[name_col]) if name_col in df.columns else df

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Projects", len(dedup))
    with kpi2:
        total_stars = int(dedup["stars"].sum()) if "stars" in dedup.columns else 0
        st.metric("Total Stars", f"{total_stars:,}")
    with kpi3:
        avg_stars = f"{dedup[score_col].mean():.0f}" if score_col in dedup.columns and not dedup.empty else "N/A"
        st.metric("Avg New Stars", avg_stars)
    with kpi4:
        langs_count = dedup["language"].nunique() if "language" in dedup.columns else 0
        st.metric("Languages", langs_count)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("New Stars Top 20")
        if score_col in dedup.columns and not dedup.empty:
            fig = bar_chart_top(
                dedup, score_col, name_col,
                f"{PERIOD_LABELS[period]} · New Stars Top 20", top_n=20,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(empty_chart(), use_container_width=True)

    with col2:
        st.subheader("Language Distribution")
        if "language" in dedup.columns:
            lang_counts = dedup["language"].value_counts().reset_index()
            lang_counts.columns = ["language", "count"]
            lang_counts = lang_counts.head(10)
            fig = bar_chart_top(lang_counts, "count", "language",
                                f"{PERIOD_LABELS[period]} · Language Top 10", top_n=10)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.plotly_chart(empty_chart("No language data"), use_container_width=True)

    # Project table
    st.subheader("All Projects")
    display_cols = _get_display_columns(df)
    disp = dedup[display_cols].copy()
    if score_col in disp.columns:
        disp = disp.sort_values(score_col, ascending=False)
    st.dataframe(disp.head(50), use_container_width=True, height=300)

    # Stars vs Fork
    if "stars" in dedup.columns and "forks" in dedup.columns:
        with st.expander(f"Stars vs Forks"):
            fig = scatter_chart(
                dedup.head(100), x="stars", y="forks", color="language",
                title=f"{PERIOD_LABELS[period]} · Stars vs Forks",
                hover_name=name_col if name_col in dedup.columns else None,
            )
            st.plotly_chart(fig, use_container_width=True)


def _get_display_columns(df):
    cols = []
    for c in ["name", "title", "owner", "description", "language", "stars",
              "stars_since", "forks", "topics", "url"]:
        if c in df.columns:
            cols.append(c)
    return cols
