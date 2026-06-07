from datetime import datetime

# ============================================================
# Scrapy 基础设置
# ============================================================

BOT_NAME = "github_trending"
SPIDER_MODULES = ["github_trending.spiders"]
NEWSPIDER_MODULE = "github_trending.spiders"

# ============================================================
# 反爬与合规
# ============================================================

ROBOTSTXT_OBEY = False                    # GitHub robots.txt 禁止 /trending，关闭以允许抓取
COOKIES_ENABLED = False                   # 不使用 cookies（静态页面无需）

# 默认请求头，模拟真实浏览器
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# ============================================================
# 下载器 & 并发控制（温和策略，减轻对目标站点的压力）
# ============================================================

DOWNLOAD_DELAY = 4                        # 基础下载延迟（秒）
CONCURRENT_REQUESTS_PER_DOMAIN = 1        # 同域名并发数

# AutoThrottle - 自动调节延迟
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3              # 起始延迟
AUTOTHROTTLE_MAX_DELAY = 10               # 最大延迟
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5     # 目标并发度
AUTOTHROTTLE_DEBUG = False

# ============================================================
# 重试与超时
# ============================================================

RETRY_ENABLED = True
RETRY_TIMES = 3                           # 最多重试 3 次
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
DOWNLOAD_TIMEOUT = 30
DNS_TIMEOUT = 10

# ============================================================
# 中间件
# ============================================================

DOWNLOADER_MIDDLEWARES = {
    # 优先尝试 fake-useragent（如果安装了 scrapy-fake-useragent）
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,  # 禁用内置 UA
    "github_trending.middlewares.RandomUserAgentMiddleware": 400,
    "github_trending.middlewares.ProxyMiddleware": 750,   # 代理中间件（预留）
}

SPIDER_MIDDLEWARES = {
    "github_trending.middlewares.GitHubTrendingSpiderMiddleware": 543,
}

# ============================================================
# Pipeline（去重）
# ============================================================

ITEM_PIPELINES = {
    "github_trending.pipelines.DedupPipeline": 300,
}

# Dedup 配置：设为 True 启用 SQLite 持久化去重
DEDUP_USE_SQLITE = False
DEDUP_SQLITE_PATH = "dedup.db"

# ============================================================
# Feed 导出 - CSV
# ============================================================

FEEDS = {
    # 输出文件由命令行参数 -o 或 run_spider.py 动态指定
}

# 显式指定 CSV 导出字段顺序
FEED_EXPORT_FIELDS = [
    "rank", "name", "owner", "description", "language",
    "stars", "stars_since", "forks", "topics", "url",
    "crawl_time", "since", "page",
]

FEED_EXPORT_ENCODING = "utf-8-sig"        # BOM 头，兼容 Excel 打开中文

# ============================================================
# 日志
# ============================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================
# 代理池（预留，按需配置）
# ============================================================

# PROXY_POOL = [
#     "http://proxy1.example.com:8080",
#     "http://proxy2.example.com:8080",
# ]

# ============================================================
# MongoDB（预留）
# ============================================================

# MONGO_URI = "mongodb://localhost:27017"
# MONGO_DB = "github_trending"

# ============================================================
# 其他
# ============================================================

TELNETCONSOLE_ENABLED = False
URLLENGTH_LIMIT = 2083
