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
    render_overlap_section(filtered)


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


def render_overlap_section(df):
    sources = df["source"].unique()
    if "github" not in sources or "hn" not in sources:
        return

    st.subheader("GitHub + Hacker News Overlap")

    github_df = df[df["source"] == "github"]
    hn_df = df[df["source"] == "hn"]

    if github_df.empty or hn_df.empty:
        st.info("Not enough data for cross-platform overlap analysis.")
        return

    gh_score_data = github_df[["url", "hot_score", "title", "name"]].copy()
    gh_score_data["gh_title"] = gh_score_data.get("title", gh_score_data.get("name", ""))
    gh_score_data = gh_score_data[["url", "hot_score", "gh_title"]].copy()
    gh_score_data.columns = ["url", "gh_hot_score", "gh_title"]

    hn_score_data = hn_df[["url", "hot_score", "title"]].copy()
    hn_score_data.columns = ["url", "hn_hot_score", "hn_title"]

    merged_url = gh_score_data.merge(hn_score_data, on="url", how="inner")

    if not merged_url.empty:
        st.markdown(f"**{len(merged_url)}** overlapping URLs found.")
        fig = scatter_chart(
            merged_url, x="gh_hot_score", y="hn_hot_score",
            hover_name="gh_title" if "gh_title" in merged_url.columns else None,
            title="GitHub vs Hacker News Hot Score (overlapping URLs)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        gh_names = set()
        for val in github_df["name"].dropna():
            parts = str(val).split("/")
            gh_names.add(parts[-1].lower() if len(parts) > 1 else str(val).lower())
        for val in github_df["title"].dropna():
            gh_names.add(str(val).lower())

        hn_names = set()
        for val in hn_df["title"].dropna():
            hn_names.add(str(val).lower())

        overlap_names = gh_names & hn_names
        if overlap_names:
            st.markdown(f"**{len(overlap_names)}** overlapping project names found (URL-independent match).")
            overlap_rows = []
            for name in overlap_names:
                gh_row = github_df[github_df["name"].str.lower().str.contains(name, na=False) | github_df["title"].str.lower().str.contains(name, na=False)]
                hn_row = hn_df[hn_df["title"].str.lower().str.contains(name, na=False)]
                if not gh_row.empty and not hn_row.empty:
                    overlap_rows.append({
                        "name": name,
                        "gh_hot_score": gh_row.iloc[0].get("hot_score", 0),
                        "hn_hot_score": hn_row.iloc[0].get("hot_score", 0),
                    })
            if overlap_rows:
                overlap_df = pd.DataFrame(overlap_rows)
                fig = scatter_chart(
                    overlap_df, x="gh_hot_score", y="hn_hot_score",
                    hover_name="name",
                    title="GitHub vs Hacker News Hot Score (name overlap)",
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No overlapping URLs or project names between GitHub and Hacker News.")
