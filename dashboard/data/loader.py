import json
import pandas as pd
import streamlit as st
from ..config import CSV_FILES, HOTSPOT_ZSET_KEY, HOTSPOT_ITEM_PREFIX
from ..utils.clients import get_mongodb_client, get_redis_client


@st.cache_data(ttl=600)
def load_csv(since="daily"):
    path = CSV_FILES.get(since)
    if not path:
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        df["crawl_time"] = pd.to_datetime(df["crawl_time"], errors="coerce")
        df["source"] = "github"
        df["hot_score"] = df["stars_since"].fillna(0) * 10 + df["forks"].fillna(0) * 5
        if "topics" in df.columns:
            df["topics"] = df["topics"].apply(_parse_topics)
        return df
    except Exception:
        return pd.DataFrame()


def _parse_topics(val):
    if isinstance(val, list):
        return val
    if pd.isna(val) or str(val).strip() == "":
        return []
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return [t.strip() for t in str(val).split(",") if t.strip()]


@st.cache_data(ttl=600)
def load_csv_all():
    frames = []
    for since in ["daily", "weekly", "monthly"]:
        df = load_csv(since)
        if not df.empty:
            df["since"] = since
            frames.append(df)
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_mongodb_all():
    _, db = get_mongodb_client()
    if db is None:
        return pd.DataFrame()

    try:
        collections = [
            c for c in db.list_collection_names()
            if c.startswith("hotspot_")
        ]
    except Exception:
        return pd.DataFrame()

    frames = []
    for coll in sorted(collections, reverse=True):
        try:
            docs = list(db[coll].find({}, {"_id": 0}))
            if docs:
                df = pd.DataFrame(docs)
                df["crawl_time"] = pd.to_datetime(df["crawl_time"], errors="coerce")
                df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
                if "topics" in df.columns:
                    df["topics"] = df["topics"].apply(_parse_topics)
                frames.append(df)
        except Exception:
            continue

    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


@st.cache_data(ttl=120)
def load_redis_hotspot():
    r = get_redis_client()
    if r is None:
        return pd.DataFrame()

    try:
        items = r.zrevrange(HOTSPOT_ZSET_KEY, 0, -1, withscores=True)
        if not items:
            return pd.DataFrame()

        rows = []
        for member_bytes, hot_score in items:
            member = member_bytes.decode("utf-8") if isinstance(member_bytes, bytes) else member_bytes
            item_key = f"{HOTSPOT_ITEM_PREFIX}{member}"
            data_raw = r.hgetall(item_key)
            if data_raw:
                data = {
                    k.decode("utf-8") if isinstance(k, bytes) else k:
                    v.decode("utf-8") if isinstance(v, bytes) else v
                    for k, v in data_raw.items()
                }
                data["hot_score"] = hot_score
                rows.append(data)

        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


def get_available_dates(df):
    if "crawl_time" not in df.columns or df.empty:
        return []
    dates = df["crawl_time"].dt.date.dropna().unique()
    return sorted(dates, reverse=True)


def get_available_languages(df):
    if "language" not in df.columns or df.empty:
        return []
    langs = df["language"].dropna().unique()
    return sorted([l for l in langs if l])
