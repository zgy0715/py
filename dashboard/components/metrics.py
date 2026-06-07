import streamlit as st


def kpi_card(label, value, delta=None, delta_color="normal"):
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
    )


def kpi_row(metrics_list):
    cols = st.columns(len(metrics_list))
    for col, (label, value, delta) in zip(cols, metrics_list):
        with col:
            kpi_card(label, value, delta)