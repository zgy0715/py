#!/usr/bin/env python3
"""
Tech Hotspot 爬虫系统 — 启动脚本

功能:
  1. 将起始 URL 推送到 Redis 各队列
  2. 依次启动四个爬虫（也可手动单独运行）

用法:
  python run_hotspot.py              # 推送 URL + 启动全部爬虫
  python run_hotspot.py --push-only  # 只推送 URL，不启动爬虫
  python run_hotspot.py --spider github_trending  # 只启动指定爬虫
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import redis

# 各爬虫的 Redis Key 与起始 URL
SPIDER_URLS = {
    "github_trending": {
        "key": "github:start_urls",
        "urls": [
            # daily
            "https://github.com/trending?since=daily",
            "https://github.com/trending/python?since=daily",
            "https://github.com/trending/javascript?since=daily",
            "https://github.com/trending/typescript?since=daily",
            "https://github.com/trending/rust?since=daily",
            "https://github.com/trending/go?since=daily",
            "https://github.com/trending/java?since=daily",
            "https://github.com/trending/c++?since=daily",
            "https://github.com/trending/ruby?since=daily",
            "https://github.com/trending/c%23?since=daily",
            "https://github.com/trending/swift?since=daily",
            "https://github.com/trending/kotlin?since=daily",
            "https://github.com/trending/shell?since=daily",
            "https://github.com/trending/php?since=daily",
            "https://github.com/trending/c?since=daily",
            # weekly
            "https://github.com/trending?since=weekly",
            "https://github.com/trending/python?since=weekly",
            "https://github.com/trending/javascript?since=weekly",
            "https://github.com/trending/typescript?since=weekly",
            "https://github.com/trending/rust?since=weekly",
            "https://github.com/trending/go?since=weekly",
            "https://github.com/trending/java?since=weekly",
            "https://github.com/trending/c++?since=weekly",
            "https://github.com/trending/ruby?since=weekly",
            "https://github.com/trending/c%23?since=weekly",
            "https://github.com/trending/swift?since=weekly",
            "https://github.com/trending/kotlin?since=weekly",
            "https://github.com/trending/shell?since=weekly",
            "https://github.com/trending/php?since=weekly",
            "https://github.com/trending/c?since=weekly",
            # monthly
            "https://github.com/trending?since=monthly",
            "https://github.com/trending/python?since=monthly",
            "https://github.com/trending/javascript?since=monthly",
            "https://github.com/trending/typescript?since=monthly",
            "https://github.com/trending/rust?since=monthly",
            "https://github.com/trending/go?since=monthly",
            "https://github.com/trending/java?since=monthly",
            "https://github.com/trending/c++?since=monthly",
            "https://github.com/trending/ruby?since=monthly",
            "https://github.com/trending/c%23?since=monthly",
            "https://github.com/trending/swift?since=monthly",
            "https://github.com/trending/kotlin?since=monthly",
            "https://github.com/trending/shell?since=monthly",
            "https://github.com/trending/php?since=monthly",
            "https://github.com/trending/c?since=monthly",
        ],
    },
    "hackernews": {
        "key": "hn:start_urls",
        "urls": [
            "https://news.ycombinator.com/news?p=1",
            "https://news.ycombinator.com/news?p=2",
            "https://news.ycombinator.com/news?p=3",
        ],
    },
    "arxiv": {
        "key": "arxiv:start_urls",
        "urls": [
            "https://arxiv.org/list/cs.AI/recent",
            "https://arxiv.org/list/cs.LG/recent",
            "https://arxiv.org/list/cs.CL/recent",
        ],
    },
    "reddit": {
        "key": "reddit:start_urls",
        "urls": [
            "https://www.reddit.com/r/MachineLearning/hot.json?limit=50",
        ],
    },
}

REDIS_HOST = "localhost"
REDIS_PORT = 6379


def _redis_client():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    try:
        r.ping()
    except redis.ConnectionError:
        print("[ERROR] Cannot connect to Redis at localhost:6379. Is Redis running?")
        sys.exit(1)
    return r


def push_urls(spider_name: str | None = None):
    """推送起始 URL 到 Redis。spider_name 为 None 则推送全部。"""
    r = _redis_client()
    targets = {spider_name: SPIDER_URLS[spider_name]} if spider_name else SPIDER_URLS

    for name, cfg in targets.items():
        key = cfg["key"]
        urls = cfg["urls"]
        for url in urls:
            r.lpush(key, url)
        print(f"[PUSH] {name}: {len(urls)} URLs -> {key}")

    r.close()
    print("[DONE] URLs pushed.\n")


def run_spider(name: str):
    """启动单个爬虫（阻塞）。"""
    cmd = [
        sys.executable, "-m", "scrapy",
        "crawl", name,
    ]
    print(f"[RUN] SCRAPY_SETTINGS_MODULE=scrapy_hotspot.settings {' '.join(cmd)}")
    env = {**os.environ, "SCRAPY_SETTINGS_MODULE": "scrapy_hotspot.settings"}
    subprocess.run(cmd, env=env)


def main():
    os.chdir(Path(__file__).parent)
    parser = argparse.ArgumentParser(description="Tech Hotspot Crawler Launcher")
    parser.add_argument("--push-only", action="store_true", help="Only push URLs, don't run spiders")
    parser.add_argument("--spider", type=str, help="Run a single spider by name")
    args = parser.parse_args()

    if args.push_only:
        push_urls()
        return

    if args.spider:
        push_urls(args.spider)
        run_spider(args.spider)
    else:
        push_urls()
        # 依次启动全部爬虫（每个是长驻进程，需在不同终端中并行）
        print("Starting all spiders sequentially (Ctrl+C to stop)...\n")
        print("Tip: For parallel execution, run each spider in a separate terminal:\n")
        for spider_name in SPIDER_URLS:
            print(
                f"  python -m scrapy crawl {spider_name} "
                f"-s SCRAPY_SETTINGS_MODULE=scrapy_hotspot.settings"
            )
        print()
        for spider_name in SPIDER_URLS:
            print(f"\n{'='*60}")
            print(f"  Starting: {spider_name}")
            print(f"{'='*60}")
            try:
                run_spider(spider_name)
            except KeyboardInterrupt:
                print(f"\n[STOPPED] {spider_name} interrupted. Moving to next...")
                continue


if __name__ == "__main__":
    main()
