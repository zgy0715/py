```markdown
# Prompt：基于 Scrapy + Redis 的多源实时热点爬虫系统（爬虫部分）

你是一个资深的 Scrapy 爬虫工程师。请根据以下要求，实现一套完整的爬虫系统，用于抓取 **当下技术热点**，包含 GitHub Trending、Hacker News、arXiv 最新论文、Reddit 热门帖子四个数据源。**必须使用 Scrapy + Redis（scrapy-redis）** 实现分布式调度、任务队列、去重和实时排行榜。

## 一、总体要求

1. **所有爬虫必须继承 `scrapy_redis.spiders.RedisSpider`**，起始 URL 从 Redis 的 List 或 ZSET 中获取。
2. **使用 Redis 作为调度器和去重过滤器**，在 `settings.py` 中配置。
3. **支持多实例并行**：多个 Scrapy 进程可以同时运行，共享任务队列和去重指纹。
4. **每个数据源独立为一个 Spider**，但有统一的 `settings.py` 和 `pipelines`。
5. **严格遵守爬虫礼仪**：设置下载延迟、随机 User-Agent、AutoThrottle（或固定延迟），避免对目标网站造成压力。
6. **所有爬取的数据输出到 MongoDB**（或 CSV，根据情况选择），但 Redis 用于实时状态管理（排行榜、去重缓存）。

## 二、项目目录结构

```
scrapy_hotspot/
├── scrapy_hotspot/
│   ├── __init__.py
│   ├── items.py                 # 定义统一的 Item（包含 source, title, url, score, hot_score, crawl_time 等）
│   ├── middlewares.py           # 随机 UA、代理、重试等中间件
│   ├── pipelines.py             # 去重、存入 MongoDB、更新 Redis 排行榜等
│   ├── settings.py              # Scrapy 配置，必须配置 scrapy-redis 相关选项
│   └── spiders/
│       ├── __init__.py
│       ├── github_spider.py     # GitHub Trending 爬虫
│       ├── hackernews_spider.py # Hacker News 爬虫
│       ├── arxiv_spider.py      # arXiv 最新论文爬虫
│       └── reddit_spider.py     # Reddit 热门帖子爬虫
├── requirements.txt
└── start_spiders.sh             # 可选的启动脚本，同时启动多个爬虫进程
```

## 三、各爬虫详细要求

### 1. GitHub Trending Spider (`github_spider.py`)

- **目标 URL**：
  - 全语言：`https://github.com/trending?since=daily`
  - 可选语言：`python`, `javascript`, `rust`, `go`, `java`（可根据需要添加）
- **解析内容**：
  - 仓库名称 (`name`: "owner/repo")
  - 仓库描述 (`description`)
  - 编程语言 (`language`)
  - 今日 / 本周新增星数 (`stars_since`)：注意页面中的 `✨ X stars today` 或 `X stars this week`
  - 总星数 (`stars_total`)
  - 今日 / 本周新增 fork 数（如果有）
  - URL
- **热度分数计算**（存入 Redis ZSET）：
  - `hot_score = stars_since * 10 + forks_since * 5`（可调）
- **去重依据**：`repo_name`（owner/repo）
- **爬取频率**：由调度器控制（建议每 6 小时抓取一次），但爬虫本身只负责执行任务。

### 2. Hacker News Spider (`hackernews_spider.py`)

- **目标 URL**：`https://news.ycombinator.com/news?p=1`（首页前 2~3 页，每页 30 条）
- **解析内容**：
  - 标题 (`title`)
  - 链接 (`url`)：可能是站内链接或外部链接
  - 分数 (`score`)
  - 评论数 (`comments`)
  - 发布时间（相对时间，如 "2 hours ago"，可解析为 UTC 时间戳）
- **热度分数**：`hot_score = score + comments * 2`
- **去重依据**：`post_id`（从 URL 或 ID 属性获取）
- **爬取频率**：每 15 分钟一次。

### 3. arXiv Latest Papers Spider (`arxiv_spider.py`)

- **目标 URL**：
  - `https://arxiv.org/list/cs.AI/recent`
  - `https://arxiv.org/list/cs.LG/recent`
  - `https://arxiv.org/list/cs.CL/recent`
  - 每页最多 50 篇，只抓取最近 3 天发布的论文（页面默认按时间倒序）。
- **解析内容**：
  - 论文 ID（如 `2101.12345`）
  - 标题
  - 作者列表（可存储为分号分隔字符串）
  - 摘要（可选，只取前 200 字符或完整）
  - 提交时间（页面顶部标注的日期）
- **热度分数**：默认为 0（暂不参与实时排行榜，但可存储供日后分析）
- **去重依据**：`paper_id`
- **爬取频率**：每天两次（凌晨 3 点，下午 3 点）。

### 4. Reddit Hot Posts Spider (`reddit_spider.py`)

- **目标 URL**：`https://www.reddit.com/r/MachineLearning/hot.json?limit=50`（使用 JSON API，这仍属于爬虫，因为发送 HTTP GET 请求）
- **请求头**：必须设置 `User-Agent`，否则会被拒绝。`Accept: application/json`
- **解析内容**（从 JSON 响应中提取）：
  - 帖子标题 (`title`)
  - 分数 (`score`)
  - 评论数 (`num_comments`)
  - 发布时间 (`created_utc`)
  - URL (`url`)
- **热度分数**：`hot_score = score + comments`
- **去重依据**：`post_id` (即 `name` 字段，如 `t3_xxxxx`)
- **爬取频率**：每 30 分钟一次。

## 四、Redis 的角色与数据设计

在 `settings.py` 中配置：

```python
# 使用 scrapy-redis 的调度器和去重类
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
SCHEDULER_PERSIST = True          # 爬虫停止时保留队列

# Redis 连接信息（环境变量或硬编码测试）
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PARAMS = {'decode_responses': True}
```

**Redis 中存储的数据结构**（手动管理，不依赖 scrapy-redis 自动键）：

| 用途 | 数据结构 | Key 示例 | 操作 |
|------|----------|----------|------|
| 任务队列 | List | `github:start_urls` | Spider 的 `redis_key = "github:start_urls"` |
| 全局去重 | Set | `seen:repo`、`seen:hn`、`seen:arxiv`、`seen:reddit` | 在 Pipeline 中 `SADD` |
| 实时热度排行榜 | Sorted Set | `hotspot:all` | score = hot_score, member = 唯一标识（如 `github:owner/repo`） |
| 按类别排行榜 | Sorted Set | `hotspot:github`、`hotspot:hn`、`hotspot:reddit` | 同上 |
| 缓存最近抓取的 Item 元数据 | Hash | `item:github:owner/repo` | 存储 JSON 串，供 Web 展示 |

> 注意：scrapy-redis 自动生成 `dupefilter` 的 Redis Key（如 `dupefilter:<spider_name>`），但你需要为 Pipeline 中的自定义去重单独维护 Set。

## 五、Pipeline 处理流程

1. **去重 Pipeline**：
   - 检查 Item 的唯一标识是否已存在对应的 Redis Set。
   - 若不存在，则 `SADD` 并继续；否则 `DropItem`。

2. **热度分数写入 Pipeline**：
   - 计算 hot_score（如果 Item 中未计算）。
   - 将 Item 的标识和 score 写入 Redis Sorted Set：`ZADD hotspot:all <score> <item_id>`。
   - 同时按来源写入 `hotspot:<source>`。

3. **MongoDB 存储 Pipeline**：
   - 存储完整的 Item 到 MongoDB 集合，集合名按日期分片（如 `hotspot_2025_03_27`）。
   - 配置 `MONGODB_URI` 和 `MONGODB_DATABASE`。

## 六、中间件要求

- **RandomUserAgentMiddleware**：从 `fake_useragent` 或内置列表随机选择 UA。
- **RetryMiddleware**：对 500、502、429、403 等状态码重试 3 次，延迟递增。
- **ProxyMiddleware（可选）**：支持从 Redis Set 或配置文件读取代理列表，随机选择。可作为反爬选做。

## 七、配置参数示例（settings.py 关键部分）

```python
BOT_NAME = 'scrapy_hotspot'
SPIDER_MODULES = ['scrapy_hotspot.spiders']
NEWSPIDER_MODULE = 'scrapy_hotspot.spiders'

ROBOTSTXT_OBEY = False   # 对 GitHub trending 需要禁用（已在文档中说明）

DOWNLOAD_DELAY = 3
CONCURRENT_REQUESTS_PER_DOMAIN = 1
RANDOMIZE_DOWNLOAD_DELAY = True

# 自动限速
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 10

# 中间件
DOWNLOADER_MIDDLEWARES = {
    'scrapy_hotspot.middlewares.RandomUserAgentMiddleware': 400,
    'scrapy_hotspot.middlewares.ProxyMiddleware': 750,
}

ITEM_PIPELINES = {
    'scrapy_hotspot.pipelines.DeduplicationPipeline': 100,
    'scrapy_hotspot.pipelines.RedisHotScorePipeline': 200,
    'scrapy_hotspot.pipelines.MongoDBPipeline': 300,
}

# MongoDB
MONGODB_URI = 'mongodb://localhost:27017'
MONGODB_DATABASE = 'tech_hotspot'

# scrapy-redis 配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
SCHEDULER = 'scrapy_redis.scheduler.Scheduler'
DUPEFILTER_CLASS = 'scrapy_redis.dupefilter.RFPDupeFilter'
SCHEDULER_PERSIST = True
```

## 八、运行方式

1. 确保 Redis 服务已启动。
2. 手动将起始 URL 推入 Redis List（或在 Spider 中硬编码 `start_urls` 并重写 `setup_redis`，但推荐外部推入）：
   ```bash
   redis-cli lpush github:start_urls "https://github.com/trending?since=daily"
   redis-cli lpush hn:start_urls "https://news.ycombinator.com/news?p=1"
   redis-cli lpush hn:start_urls "https://news.ycombinator.com/news?p=2"
   redis-cli lpush arxiv:start_urls "https://arxiv.org/list/cs.AI/recent"
   redis-cli lpush arxiv:start_urls "https://arxiv.org/list/cs.LG/recent"
   redis-cli lpush reddit:start_urls "https://www.reddit.com/r/MachineLearning/hot.json?limit=50"
   ```
3. 启动爬虫（每个 Spider 可开多个进程）：
   ```bash
   scrapy crawl github_trending
   scrapy crawl hackernews
   scrapy crawl arxiv
   scrapy crawl reddit
   ```

## 九、额外要求（为满足课程选做）

- **反爬虫示例**：在 GitHubSpider 中针对 `429 Too Many Requests` 实现动态退避（增加延迟并重试）。
- **分布式锁**：在 Pipeline 更新排行榜时，如果多个 worker 同时更新同一个 key，可能产生竞态？无需担心，Redis 的 `ZADD` 是原子的。
- **支持断点续爬**：由于 `SCHEDULER_PERSIST = True`，停止爬虫后重新启动会从队列中断处继续。

## 十、输出交付

请提供以下文件的完整代码：

- `scrapy_hotspot/items.py`
- `scrapy_hotspot/settings.py`
- `scrapy_hotspot/middlewares.py`
- `scrapy_hotspot/pipelines.py`
- `scrapy_hotspot/spiders/github_spider.py`
- `scrapy_hotspot/spiders/hackernews_spider.py`
- `scrapy_hotspot/spiders/arxiv_spider.py`
- `scrapy_hotspot/spiders/reddit_spider.py`
- `requirements.txt`
- `start_spiders.sh`（可选）

所有代码必须能够直接运行（需提前安装依赖和 Redis、MongoDB）。请在代码中添加必要的注释，特别是 scrapy-redis 相关部分和热度分计算逻辑。

