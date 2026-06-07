import os
import streamlit as st
from ..config import CSV_FILES


@st.cache_data(ttl=60, show_spinner=False)
def _check_csv():
    for path in CSV_FILES.values():
        if os.path.exists(path):
            return True
    return False


def detect_data_sources():
    sources = {"csv": False, "mongodb": False, "redis": False}

    sources["csv"] = _check_csv()

    from ..utils.clients import get_mongodb_client, get_redis_client
    _, db = get_mongodb_client()
    if db is not None:
        sources["mongodb"] = True

    r = get_redis_client()
    if r is not None:
        sources["redis"] = True

    return sources


def get_tier(sources):
    if sources["redis"]:
        return 3
    if sources["mongodb"]:
        return 2
    if sources["csv"]:
        return 1
    return 0
