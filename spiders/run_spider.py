#!/usr/bin/env python3
"""
独立运行脚本 — 抓取 GitHub Trending 热门项目。

用法:
    python run_spider.py                               # 同时生成日、周、月三榜数据
    python run_spider.py --single daily                # 仅生成日榜
    python run_spider.py --single weekly               # 仅生成周榜
    python run_spider.py --single monthly              # 仅生成月榜
    python run_spider.py --languages python,javascript # 自定义语言

输出文件:
    github_trending_daily.csv
    github_trending_weekly.csv
    github_trending_monthly.csv
每次运行覆盖同名旧文件。
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_crawler(since, languages=None, log_level="INFO"):
    """执行单个周期的爬虫任务"""
    output_file = f"../data/github_trending_{since}.csv"
    
    print()
    print("=" * 70)
    print(f"  GitHub Trending Crawler - {since.upper()}")
    print("=" * 70)
    print(f"  Since      : {since}")
    print(f"  Languages  : {languages or '(default: 14 languages)'}")
    print(f"  Output     : {output_file} (overwrite)")
    print("=" * 70)
    print()

    # 构建 Scrapy 命令
    cmd = [
        sys.executable, "-m", "scrapy",
        "crawl", "github_trending_ai",
        "-s", f"LOG_LEVEL={log_level}",
        "-O", output_file,      # -O 覆盖模式
        "-a", f"since={since}",
    ]
    
    if languages:
        cmd.extend(["-a", f"languages={languages}"])

    result = subprocess.run(cmd)
    return result.returncode


def main():
    os.chdir(Path(__file__).parent)
    parser = argparse.ArgumentParser(
        description="GitHub Trending 爬虫 — 抓取 GitHub 热门项目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_spider.py                  # 同时生成日、周、月三榜
  python run_spider.py --single daily   # 仅生成日榜
  python run_spider.py --languages rust,go,python
        """,
    )
    parser.add_argument(
        "--single",
        choices=["daily", "weekly", "monthly"],
        default=None,
        help="仅运行单个周期（默认: 同时运行日、周、月三榜）",
    )
    parser.add_argument(
        "--languages",
        type=str,
        default=None,
        help="要抓取的编程语言，逗号分隔 (默认: 主流 14 种语言)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)",
    )

    args = parser.parse_args()

    # 确定要运行的周期列表
    if args.single:
        cycles = [args.single]
    else:
        cycles = ["daily", "weekly", "monthly"]

    print()
    print("=" * 70)
    print("  GitHub Trending Crawler - 批量模式")
    print("=" * 70)
    print(f"  Target cycles: {', '.join(cycles)}")
    print(f"  Languages    : {args.languages or '(default: 14 languages)'}")
    print("=" * 70)
    print()

    # 依次运行每个周期的爬虫
    for cycle in cycles:
        return_code = run_crawler(cycle, args.languages, args.log_level)
        if return_code != 0:
            print(f"\n❌  {cycle} 榜单抓取失败 (exit code: {return_code})")
            sys.exit(return_code)
        print(f"\n✅  {cycle} 榜单抓取完成")

    print("\n" + "=" * 70)
    print("  🎉 所有榜单抓取完成！")
    print("=" * 70)
    print("  输出文件:")
    for cycle in cycles:
        print(f"    - github_trending_{cycle}.csv")
    print("=" * 70)


if __name__ == "__main__":
    main()
