"""
混合数据加载器 — CSV 直接读取保证完整数据，API 获取 MongoDB 多源和系统状态。
"""
import json
import pandas as pd
import streamlit as st
import requests
from dashboard.config import CSV_FILES

API_BASE = "http://localhost:5000"


def _fetch(path):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None


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
def _load_csv_direct(since):
    """直接读取 CSV 文件获取完整数据"""
    path = CSV_FILES.get(since)
    if not path:
        return pd.DataFrame()
    try:
        import os
        if not os.path.exists(path):
            return pd.DataFrame()
        df = pd.read_csv(path)
        df["crawl_time"] = pd.to_datetime(df["crawl_time"], errors="coerce")
        df["source"] = "github"
        df["since"] = since
        if "stars_since" in df.columns:
            forks = df["forks"] if "forks" in df.columns else 0
            df["hot_score"] = df["stars_since"].fillna(0).astype(int) * 10 + forks.fillna(0).astype(int) * 5 if isinstance(forks, pd.Series) else df["stars_since"].fillna(0).astype(int) * 10
        if "topics" in df.columns:
            df["topics"] = df["topics"].apply(_parse_topics)
        return df
    except Exception as e:
        st.warning(f"CSV 读取失败 {since}: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner="正在加载数据...")
def load_all():
    sources = {"csv": False, "mongodb": False, "redis": False}
    tier = 0

    # 1. 系统状态检测
    status = _fetch("/api/system/status")
    if status:
        sources = status.get("sources", sources)
        tier = status.get("tier", 0)

    # 2. CSV 直接读取（完整数据）
    csv_frames = []
    for since in ["daily", "weekly", "monthly"]:
        df = _load_csv_direct(since)
        if not df.empty:
            csv_frames.append(df)
    df_csv = pd.concat(csv_frames, ignore_index=True) if csv_frames else pd.DataFrame()

    # 3. MongoDB 多源数据（按源分别拉取）
    mongo_frames = []
    if sources.get("mongodb"):
        collections = _fetch("/api/collections")
        if collections:
            mongo_info = status.get("mongo_collections", {}) or {}
            best_coll = collections[0]
            best_src_count = 0
            for coll_name in collections:
                src_list = (mongo_info.get(coll_name, {}) or {}).get("sources", [])
                if len(src_list) > best_src_count:
                    best_src_count = len(src_list)
                    best_coll = coll_name
            src_count = {}
            for s in (mongo_info.get(best_coll, {}) or {}).get("sources", []):
                src_count[s] = 0
            for src in (list(src_count.keys()) or ["arxiv", "hn", "reddit"]):
                if src == "github":
                    continue
                src_data = _fetch(
                    f"/api/hotspot?collection={best_coll}&source={src}&sort_by=hot_score&limit=300"
                )
                if src_data:
                    for item in src_data:
                        item["crawl_time"] = pd.to_datetime(item.get("crawl_time"), errors="coerce")
                        item["published_at"] = pd.to_datetime(item.get("published_at"), errors="coerce")
                        if not item.get("title"):
                            item["title"] = item.get("name", "").split("/")[-1] if "/" in item.get("name", "") else item.get("name", "")
                        if not item.get("name") and item.get("title"):
                            item["name"] = item["title"]
                    mongo_frames.append(pd.DataFrame(src_data))

    df_mongo = pd.concat(mongo_frames, ignore_index=True) if mongo_frames else pd.DataFrame()

    # 4. 合并 df_all
    if not df_mongo.empty and not df_csv.empty:
        df_all = pd.concat([df_csv, df_mongo], ignore_index=True)
    elif not df_mongo.empty:
        df_all = df_mongo
    else:
        df_all = df_csv

    # 5. 数值转换
    for df in [df_csv, df_mongo, df_all]:
        if df.empty:
            continue
        for col in ["stars", "stars_since", "forks", "hot_score", "score", "comments"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        for col in ["crawl_time", "published_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    # 6. 补全 name/title 互填，确保所有行都有显示名称
    for df in [df_csv, df_mongo, df_all]:
        if df.empty:
            continue
        if "name" in df.columns and "title" in df.columns:
            df["name"] = df["name"].fillna(df["title"])
            df["title"] = df["title"].fillna(df["name"])
        elif "name" in df.columns and "title" not in df.columns:
            df["title"] = df["name"]
        elif "title" in df.columns and "name" not in df.columns:
            df["name"] = df["title"]

    # 7. 为非 GitHub 数据填充 since 字段，避免 groupby NaN
    if "since" in df_all.columns:
        df_all["since"] = df_all["since"].fillna("all")

    # 8. 填充空 language 字段
    for df in [df_csv, df_mongo, df_all]:
        if df.empty:
            continue
        if "language" in df.columns:
            df["language"] = df["language"].fillna("Unknown")

    return sources, tier, df_csv, df_mongo, df_all
