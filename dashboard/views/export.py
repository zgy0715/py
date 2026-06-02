import io

import pandas as pd
import streamlit as st

from ..components.filters import export_filters


def render(session_state):
    st.header("Export Data")

    df = session_state.df_all
    if df.empty:
        st.warning("No data to export.")
        return

    selected_sources = export_filters(df, key_prefix="exp_")
    filtered = df.copy()
    if selected_sources and "source" in filtered.columns:
        filtered = filtered[filtered["source"].isin(selected_sources)]

    all_cols = filtered.columns.tolist()
    default_cols = [c for c in [
        "source", "title", "name", "owner", "language",
        "stars", "stars_since", "forks", "hot_score", "url", "crawl_time",
    ] if c in all_cols]

    with st.sidebar:
        st.divider()
        st.subheader("Export Columns")
        selected_cols = st.multiselect(
            "Select columns to export",
            all_cols, default=default_cols, key="exp_cols",
        )

    display_df = filtered[selected_cols].copy() if selected_cols else filtered.copy()
    if "crawl_time" in display_df.columns:
        display_df = display_df.sort_values("crawl_time", ascending=False)

    st.subheader("Preview (first 50 rows)")
    st.dataframe(display_df.head(50), use_container_width=True, height=400)

    csv_data = display_df.to_csv(index=False, encoding="utf-8-sig")

    st.subheader("Download")
    st.download_button(
        label="Download CSV (UTF-8 BOM, Excel-compatible)",
        data=csv_data,
        file_name="tech_hotspot_export.csv",
        mime="text/csv",
        type="primary",
    )

    st.caption(
        f"{len(display_df)} rows | "
        f"{len(selected_cols) if selected_cols else len(all_cols)} columns"
    )
