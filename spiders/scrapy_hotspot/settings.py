# ============================================================
# Scrapy Hotspot — 多源实时热点爬虫设置
# 使用方式: scrapy crawl <spider> -s SCRAPY_SETTINGS_MODULE=scrapy_hotspot.settings
# ============================================================

BOT_NAME = "scrapy_hotspot"
SPIDER_MODULES = ["scrapy_hotspot.spiders"]
NEWSPIDER_MODULE = "scrapy_hotspot.spiders"

# ============================================================
# 反爬与合规
# ============================================================

ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
}

# ============================================================
# 下载器 & 并发控制
# ============================================================

DOWNLOAD_DELAY = 3
CONCURRENT_REQUESTS_PER_DOMAIN = 1
RANDOMIZE_DOWNLOAD_DELAY = True

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5

# ============================================================
# 重试与超时
# ============================================================

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
DOWNLOAD_TIMEOUT = 30
DNS_TIMEOUT = 10

# ============================================================
# 中间件（复用 github_trending 的 UA / Proxy 中间件）
# ============================================================

DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "github_trending.middlewares.RandomUserAgentMiddleware": 400,
    "github_trending.middlewares.ProxyMiddleware": 750,
}

# ============================================================
# Pipeline 链：去重 → 热度写入 → MongoDB 存储
# ============================================================

ITEM_PIPELINES = {
    "scrapy_hotspot.pipelines.DeduplicationPipeline": 100,
    "scrapy_hotspot.pipelines.RedisHotScorePipeline": 200,
    "scrapy_hotspot.pipelines.MongoDBPipeline": 300,
}

# ============================================================
# scrapy-redis：分布式调度器 & 去重
# ============================================================

SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
SCHEDULER_PERSIST = True
SCHEDULER_IDLE_BEFORE_CLOSE = 30        # 空闲 30 秒后关闭

REDIS_HOST = "localhost"
REDIS_PORT = 6379

# ============================================================
# MongoDB
# ============================================================

MONGODB_URI = "mongodb://localhost:27017"
MONGODB_DATABASE = "tech_hotspot"

# ============================================================
# 热度排行榜 Redis 配置
# ============================================================

HOTSPOT_ZSET_KEY = "hotspot:all"         # 全局排行榜
HOTSPOT_ZSET_TTL = 86400 * 7             # 排行榜保留 7 天
HOTSPOT_ITEM_PREFIX = "item:"            # Item 缓存 Hash 前缀

# ============================================================
# 日志
# ============================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================
# 其他
# ============================================================

TELNETCONSOLE_ENABLED = False
URLLENGTH_LIMIT = 2083
