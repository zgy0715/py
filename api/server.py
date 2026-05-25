"""
Tech Hotspot API — 统一数据层
提供 MongoDB / CSV / Redis 数据的 RESTful 接口，供前端使用。
"""
import csv
import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "tech_hotspot"

CSV_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CSV_FILES = {
    "daily": os.path.join(CSV_DIR, "github_trending_daily.csv"),
    "weekly": os.path.join(CSV_DIR, "github_trending_weekly.csv"),
    "monthly": os.path.join(CSV_DIR, "github_trending_monthly.csv"),
}

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# ---------- 工具函数 ----------

def _doc_to_item(doc, idx):
    """将 MongoDB 文档转成前端需要的格式"""
    name = doc.get("unique_id", "")
    title = doc.get("title", "")
    source = doc.get("source", "")
    if source in ("hn", "reddit") and title:
        display_name = title
    elif title and not name:
        display_name = title
    else:
        display_name = name
    return {
        "rank": idx + 1,
        "name": display_name,
        "unique_id": name,
        "title": title,
        "owner": doc.get("author", ""),
        "language": doc.get("language") or "Unknown",
        "stars": doc.get("stars") or 0,
        "stars_since": doc.get("stars_since") or 0,
        "forks": doc.get("forks") or 0,
        "hot_score": doc.get("hot_score") or 0,
        "description": doc.get("description") or "",
        "topics": doc.get("topics") or [],
        "url": doc.get("url") or "",
        "source": source,
        "score": doc.get("score") or 0,
        "comments": doc.get("comments") or 0,
        "published_at": doc.get("published_at"),
        "crawl_time": doc.get("crawl_time") or "",
    }


def _get_collections():
    """返回所有 hotspot_* 集合名，按日期降序"""
    try:
        colls = [c for c in db.list_collection_names() if c.startswith("hotspot_")]
        colls.sort(reverse=True)
        return colls
    except Exception:
        return []


# ---------- API 路由 ----------

@app.route("/api/collections")
def collections():
    """列出可用日期集合"""
    return jsonify(_get_collections())


@app.route("/api/sources")
def sources():
    """列出所有数据源及其在各集合中的数量"""
    result = {}
    try:
        for coll_name in _get_collections():
            pipeline = [{"$group": {"_id": "$source", "count": {"$count": {}}}}]
            src_counts = {r["_id"]: r["count"] for r in db[coll_name].aggregate(pipeline)}
            result[coll_name] = src_counts
    except Exception:
        pass
    return jsonify(result)


@app.route("/api/hotspot")
def hotspot():
    """
    获取热点数据。

    参数:
        collection  - 集合名，默认最新 (如 hotspot_2026_05_18)
        source      - 数据源筛选 (github / hn / arxiv / reddit)，默认全部
        range       - 时间范围筛选 (daily / weekly / monthly)，仅对 github 有效
        sort_by     - 排序字段，默认 hot_score
        order       - 排序方向，默认 desc
        limit       - 返回条数，默认 200
        offset      - 偏移量，默认 0
        use_csv     - 是否使用 CSV 数据（仅 github 有效），默认 false
    """
    source = request.args.get("source")
    range_val = request.args.get("range")
    sort_by = request.args.get("sort_by", "hot_score")
    order = request.args.get("order", "desc")
    limit = int(request.args.get("limit", 200))
    offset = int(request.args.get("offset", 0))
    use_csv = request.args.get("use_csv", "false").lower() in ("true", "1", "yes")

    if source == "github" and use_csv:
        csv_rows = _read_csv(range_val or "daily")
        for r in csv_rows:
            if "hot_score" not in r or not r["hot_score"]:
                r["hot_score"] = r.get("stars_since", 0) * 10 + r.get("forks", 0) * 5
        reverse = order == "desc"
        csv_rows.sort(key=lambda r: r.get(sort_by, 0) or 0, reverse=reverse)
        items = csv_rows[offset:offset + limit]
        for i, item in enumerate(items):
            item["rank"] = offset + i + 1
            item["source"] = "github"
            item["since"] = range_val or "daily"
        return jsonify(items)

    coll_name = request.args.get("collection")
    if not coll_name:
        colls = _get_collections()
        if not colls:
            return jsonify([])
        coll_name = colls[0]

    query = {}
    if source:
        query["source"] = source
    if range_val:
        query["range"] = range_val

    sort_dir = -1 if order == "desc" else 1
    docs = list(
        db[coll_name]
        .find(query)
        .sort(sort_by, sort_dir)
        .skip(offset)
        .limit(limit)
    )

    items = [_doc_to_item(doc, i) for i, doc in enumerate(docs)]
    return jsonify(items)


@app.route("/api/hotspot/stats")
def hotspot_stats():
    """
    聚合统计。

    参数:
        collection  - 集合名，默认最新
        source      - 数据源筛选，默认全部
    """
    coll_name = request.args.get("collection")
    if not coll_name:
        colls = _get_collections()
        if not colls:
            return jsonify({})
        coll_name = colls[0]

    source = request.args.get("source")
    match = {}
    if source:
        match["source"] = source

    pipeline = [
        {"$match": match},
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "total_stars": {"$sum": "$stars"},
                "total_forks": {"$sum": "$forks"},
                "total_hot_score": {"$sum": "$hot_score"},
                "avg_stars": {"$avg": "$stars"},
                "avg_hot_score": {"$avg": "$hot_score"},
                "max_stars": {"$max": "$stars"},
                "max_hot_score": {"$max": "$hot_score"},
                "min_stars": {"$min": "$stars"},
            }
        },
    ]
    agg = list(db[coll_name].aggregate(pipeline))
    if not agg:
        return jsonify({})

    result = agg[0]
    result.pop("_id", None)
    result["avg_stars"] = round(result.get("avg_stars") or 0)
    result["avg_hot_score"] = round(result.get("avg_hot_score") or 0)

    # 语言分布
    lang_pipeline = [
        {"$match": match},
        {"$group": {"_id": "$language", "count": {"$count": {}}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    result["languages"] = [
        {"name": r["_id"] or "Unknown", "count": r["count"]}
        for r in db[coll_name].aggregate(lang_pipeline)
    ]

    return jsonify(result)


@app.route("/api/hotspot/top")
def hotspot_top():
    """
    Top-N 项目（按指标排序）。

    参数:
        collection  - 集合名，默认最新
        source      - 数据源，默认 github
        metric      - 排序指标 (stars / stars_since / hot_score)，默认 stars_since
        limit       - 返回条数，默认 10
    """
    coll_name = request.args.get("collection")
    if not coll_name:
        colls = _get_collections()
        if not colls:
            return jsonify([])
        coll_name = colls[0]

    source = request.args.get("source", "github")
    metric = request.args.get("metric", "stars_since")
    limit = int(request.args.get("limit", 10))

    docs = list(
        db[coll_name]
        .find({"source": source})
        .sort(metric, -1)
        .limit(limit)
    )

    items = [_doc_to_item(doc, i) for i, doc in enumerate(docs)]
    return jsonify(items)


# ========== CSV / Redis 辅助函数 ==========

CSV_COLS = ["rank", "name", "owner", "description", "language", "stars",
            "stars_since", "forks", "topics", "url", "crawl_time", "since", "page"]


def _read_csv(since="daily"):
    """读取单个 CSV 文件并返回 dict 列表"""
    path = CSV_FILES.get(since)
    if not path or not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for col in ["stars", "stars_since", "forks", "rank"]:
                try:
                    row[col] = int(row.get(col, 0) or 0)
                except (ValueError, TypeError):
                    row[col] = 0
            row["source"] = "github"
            row["since"] = since
            rows.append(row)
    return rows


def _read_csv_all():
    """合并三个时间维度的 CSV 数据"""
    result = []
    for since in ["daily", "weekly", "monthly"]:
        rows = _read_csv(since)
        for r in rows:
            if "hot_score" not in r or not r["hot_score"]:
                r["hot_score"] = r.get("stars_since", 0) * 10 + r.get("forks", 0) * 5
        result.extend(rows)
    return result


def _get_redis_client():
    try:
        from redis import Redis
        r = Redis(host="localhost", port=6379, socket_timeout=3)
        r.ping()
        return r
    except Exception:
        return None


def _load_redis_hotspot():
    """从 Redis 加载热点排行榜数据"""
    r = _get_redis_client()
    if r is None:
        return []
    try:
        items = r.zrevrange("hotspot:all", 0, -1, withscores=True)
        if not items:
            return []
        rows = []
        for member_bytes, hot_score in items:
            member = member_bytes.decode("utf-8") if isinstance(member_bytes, bytes) else member_bytes
            data_raw = r.hgetall(f"item:{member}")
            if data_raw:
                data = {
                    k.decode("utf-8") if isinstance(k, bytes) else k:
                    v.decode("utf-8") if isinstance(v, bytes) else v
                    for k, v in data_raw.items()
                }
                data["hot_score"] = hot_score
                rows.append(data)
        return rows
    except Exception:
        return []


def _check_data_sources():
    """检测所有数据源可用状态"""
    sources = {"csv": False, "mongodb": False, "redis": False}

    # CSV
    for path in CSV_FILES.values():
        if os.path.exists(path):
            sources["csv"] = True
            break

    # MongoDB
    try:
        client.admin.command("ping")
        sources["mongodb"] = True
    except Exception:
        pass

    # Redis
    r = _get_redis_client()
    if r is not None:
        sources["redis"] = True

    # Tier: 0=none, 1=csv, 2=csv+mongo, 3=csv+mongo+redis
    tier = 0
    if sources["redis"]:
        tier = 3
    elif sources["mongodb"]:
        tier = 2
    elif sources["csv"]:
        tier = 1

    return sources, tier


# ========== 系统状态 / 爬虫检测 API ==========


@app.route("/api/system/status")
def system_status():
    """数据源健康检查 — 爬虫是否正常运行"""
    sources, tier = _check_data_sources()

    # MongoDB 集合统计
    mongo_stats = {}
    for coll_name in _get_collections():
        docs = list(db[coll_name].find({}, {"_id": 0, "source": 1}))
        sources_in_coll = list(set(d.get("source", "?") for d in docs))
        mongo_stats[coll_name] = {
            "total": len(docs),
            "sources": sources_in_coll,
        }

    # CSV 统计
    csv_stats = {}
    for since in ["daily", "weekly", "monthly"]:
        rows = _read_csv(since)
        csv_stats[since] = {"total": len(rows)}

    # Redis 统计
    redis_count = len(_load_redis_hotspot())

    tier_labels = {
        0: "无数据源",
        1: "CSV (Tier 1)",
        2: "CSV + MongoDB (Tier 2)",
        3: "CSV + MongoDB + Redis (Tier 3)",
    }

    return jsonify({
        "sources": sources,
        "tier": tier,
        "tier_label": tier_labels.get(tier, "未知"),
        "mongo_collections": mongo_stats,
        "csv_stats": csv_stats,
        "redis_count": redis_count,
    })


@app.route("/api/system/overview")
def system_overview():
    """全局概览统计（聚合 CSV + MongoDB）"""
    # 从 CSV 读取 GitHub 数据
    csv_data = _read_csv_all()
    github_df = csv_data

    # 从 MongoDB 读取非 GitHub 数据
    mongo_docs = []
    try:
        for coll_name in _get_collections():
            docs = list(db[coll_name].find(
                {"source": {"$ne": "github"}},
                {"_id": 0}
            ).limit(500))
            mongo_docs.extend(docs)
    except Exception:
        pass

    total_projects = len(github_df) + len(mongo_docs)

    # GitHub 统计
    gh_total_stars = sum(r.get("stars", 0) or 0 for r in github_df)
    gh_total_forks = sum(r.get("forks", 0) or 0 for r in github_df)
    gh_languages = set(r.get("language", "Unknown") for r in github_df if r.get("language"))
    gh_total_stars_since = sum(r.get("stars_since", 0) or 0 for r in github_df)

    # MongoDB 统计
    mongo_total = len(mongo_docs)
    mongo_sources = list(set(d.get("source", "?") for d in mongo_docs)) if mongo_docs else []

    # 各 source 数量
    source_counts = {"github": len(github_df)}
    for s in mongo_sources:
        source_counts[s] = sum(1 for d in mongo_docs if d.get("source") == s)

    return jsonify({
        "total_projects": total_projects,
        "github": {
            "total": len(github_df),
            "total_stars": gh_total_stars,
            "total_forks": gh_total_forks,
            "total_stars_since": gh_total_stars_since,
            "languages": len(gh_languages),
            "languages_list": sorted(gh_languages) if gh_languages else [],
        },
        "mongo": {
            "total": mongo_total,
            "sources": mongo_sources,
        },
        "source_counts": source_counts,
    })


@app.route("/api/system/periods")
def system_periods():
    """按时间维度（daily/weekly/monthly）的统计"""
    result = {}
    for since in ["daily", "weekly", "monthly"]:
        rows = _read_csv(since)
        if not rows:
            result[since] = {"total": 0}
            continue

        total_stars = sum(r.get("stars", 0) or 0 for r in rows)
        total_stars_since = sum(r.get("stars_since", 0) or 0 for r in rows)
        total_forks = sum(r.get("forks", 0) or 0 for r in rows)
        avg_stars_since = round(total_stars_since / len(rows)) if rows else 0
        languages = set(r.get("language", "Unknown") for r in rows if r.get("language"))

        # Top 10
        sorted_rows = sorted(rows, key=lambda r: r.get("stars_since", 0) or 0, reverse=True)
        top10 = []
        for r in sorted_rows[:10]:
            top10.append({
                "rank": r.get("rank", 0),
                "name": r.get("name", ""),
                "owner": r.get("owner", ""),
                "stars": r.get("stars", 0),
                "stars_since": r.get("stars_since", 0),
                "forks": r.get("forks", 0),
                "language": r.get("language", "Unknown"),
                "description": r.get("description", ""),
                "url": r.get("url", ""),
            })

        result[since] = {
            "total": len(rows),
            "total_stars": total_stars,
            "total_stars_since": total_stars_since,
            "total_forks": total_forks,
            "avg_stars_since": avg_stars_since,
            "languages": len(languages),
            "top10": top10,
        }

    return jsonify(result)


@app.route("/api/system/history")
def system_history():
    """爬虫历史 — 各集合各来源的采集时间和数量"""
    history = []
    for coll_name in _get_collections():
        pipeline = [
            {"$group": {
                "_id": {"source": "$source"},
                "count": {"$sum": 1},
                "last_crawl": {"$max": "$crawl_time"},
                "first_crawl": {"$min": "$crawl_time"},
            }}
        ]
        results = list(db[coll_name].aggregate(pipeline))
        sources_info = []
        for r in results:
            sources_info.append({
                "source": r["_id"]["source"],
                "count": r["count"],
                "last_crawl": r.get("last_crawl", ""),
                "first_crawl": r.get("first_crawl", ""),
            })

        # 总数量
        total = db[coll_name].count_documents({})
        history.append({
            "collection": coll_name,
            "total": total,
            "sources": sources_info,
        })

    # CSV 最近采集时间
    csv_latest = {}
    for since in ["daily", "weekly", "monthly"]:
        rows = _read_csv(since)
        if rows:
            times = [r.get("crawl_time", "") for r in rows if r.get("crawl_time")]
            csv_latest[since] = {
                "count": len(rows),
                "latest_crawl": max(times) if times else None,
            }
        else:
            csv_latest[since] = {"count": 0, "latest_crawl": None}

    return jsonify({
        "mongo_history": history,
        "csv_history": csv_latest,
    })


# ---------- 启动 ----------

if __name__ == "__main__":
    print(f"[API] MongoDB: {MONGO_URI} / {DB_NAME}")
    print(f"[API] Collections: {_get_collections()}")
    app.run(host="0.0.0.0", port=5000, debug=True)
