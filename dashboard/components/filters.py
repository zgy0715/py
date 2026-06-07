import streamlit as st


def github_filters(df, key_prefix=""):
    st.sidebar.divider()
    st.sidebar.subheader("GitHub Filters")

    languages = sorted(df["language"].dropna().unique())
    selected_langs = st.sidebar.multiselect(
        "Language",
        languages,
        key=f"{key_prefix}langs",
    )

    max_val = int(df["stars_since"].max()) if not df.empty and "stars_since" in df.columns else 1000
    min_stars = st.sidebar.slider(
        "Min New Stars",
        min_value=0,
        max_value=max_val,
        value=0,
        step=10,
        key=f"{key_prefix}min_stars",
    )

    search = st.sidebar.text_input(
        "Search repos",
        placeholder="Enter keyword...",
        key=f"{key_prefix}search",
    )

    return selected_langs, min_stars, search


def multi_source_filters(df, key_prefix=""):
    st.sidebar.divider()
    st.sidebar.subheader("Multi-Source Filters")

    sources = sorted(df["source"].dropna().unique()) if "source" in df.columns else []
    selected_sources = st.sidebar.multiselect(
        "Data Source",
        sources,
        default=sources,
        key=f"{key_prefix}sources",
    )
    return selected_sources


def export_filters(df, key_prefix=""):
    st.sidebar.divider()
    st.sidebar.subheader("Export Filters")

    sources = sorted(df["source"].dropna().unique()) if "source" in df.columns else []
    selected_sources = st.sidebar.multiselect(
        "Data Source",
        sources,
        key=f"{key_prefix}exp_sources",
    )
    return selected_sources
