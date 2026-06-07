#!/usr/bin/env python3
"""从 MongoDB 导出数据为 CSV。"""
import csv
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
DB = "tech_hotspot"
# 导出每个集合
COLLECTIONS = ["hotspot_2026_05_18", "hotspot_2026_05_17"]

FIELDS = [
    "source", "unique_id", "title", "url", "description", "author",
    "language", "score", "comments", "stars", "stars_since", "forks",
    "topics", "hot_score", "published_at", "crawl_time", "extra",
]

client = MongoClient(MONGO_URI)
db = client[DB]

for coll_name in COLLECTIONS:
    output = f"data/{coll_name}.csv"
    docs = list(db[coll_name].find())
    if not docs:
        print(f"No data in {coll_name}")
        continue

    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for doc in docs:
            row = {}
            for field in FIELDS:
                val = doc.get(field, "")
                if isinstance(val, list):
                    val = "; ".join(str(v) for v in val)
                elif isinstance(val, dict):
                    val = str(val)
                row[field] = val
            writer.writerow(row)

    print(f"Exported {len(docs)} rows -> {output}")

client.close()
print("Done.")
