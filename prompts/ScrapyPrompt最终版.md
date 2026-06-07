# ScrapyPrompt 最终版 — GitHub Trending 多源热点爬虫 + AI 深度分析系统

## 项目概述

本项目是一套完整的技术热点追踪与 AI 深度分析系统，包含以下核心能力：

1. **多源数据采集**：基于 Scrapy + Redis 的分布式爬虫，覆盖 GitHub Trending、Hacker News、arXiv、Reddit 四大数据源
2. **实时数据处理**：Redis 去重 + 实时热度排行榜 + MongoDB 持久化
3. **可视化展示**：Streamlit 看板 + ECharts 仪表盘双前端
4. **AI 深度分析**：DeepSeek 大模型驱动，自动生成趋势洞察、项目推荐、学习路径和信号挖掘
5. **统一 API 服务**：Flask RESTful API 提供数据查询接口

---

## 一、系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        数据采集层                                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │
│  │ GitHub       │ │ Hacker News  │ │ arXiv        │ │ Reddit     │ │
│  │ Trending     │ │ Front Page   │ │ cs.AI/LG/CL  │ │ r/ML       │ │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └─────┬──────┘ │
│         │                │                │               │        │
│         └────────────────┴────────────────┴───────────────┘        │
│                                    │                                │
│                         Scrapy + scrapy-redis                       │
│                                    │                                │
├────────────────────────────────────┼────────────────────────────────┤
│                        数据处理层                                    │
│         ┌──────────────────────────┼──────────────────────┐         │
│         │                          │                      │         │
│  ┌──────▼──────┐  ┌───────────────▼──────────────┐  ┌────▼────┐   │
│  │ Redis       │  │ MongoDB                      │  │ CSV     │   │
│  │ 去重+排行榜  │  │ 持久化存储（hotspot_YYYY_MM_DD）│  │ 备份    │   │
│  └─────────────┘  └──────────────────────────────┘  └─────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                        服务层                                        │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐    │
│  │ Flask API        │  │ AI分析/                               │    │
│  │ port 5000        │  │ DeepSeek AI 深度分析（独立模块）        │    │
│  │ 数据查询接口      │  │ port 无（独立运行）                    │    │
│  └──────────────────┘  └──────────────────────────────────────┘    │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                        展示层                                        │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐    │
│  │ Streamlit 看板   │  │ ECharts 仪表盘                       │    │
│  │ port 8501        │  │ port 3000                            │    │
│  └──────────────────┘  └──────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、项目目录结构

```
hot-open-project-zgy/
│
├── AI分析/                           # DeepSeek AI 深度分析（独立模块）
│   ├── deepseek_analyzer.py          #   AI 分析主程序
│   ├── import_data.py                #   CSV 数据导入工具
│   ├── export_report.py              #   导出 AI 分析报告为 TXT
│   ├── requirements.txt              #   Python 依赖
│   ├── output/                       #   分析结果输出（JSON/TXT 格式）
│   ├── insight_analysis.log          #   AI 分析日志（自动生成）
│   ├── import_data.log               #   数据导入日志（自动生成）
│   └── README.md                     #   模块说明文档
│
├── api/                              # Flask RESTful API 服务
│   ├── server.py                     #   核心接口
│   └── requirements.txt              #   Python 依赖
│
├── dashboard/                        # Streamlit 可视化看板
│   ├── app.py                        #   入口（5 页面导航）
│   ├── config.py                     #   配置文件
│   ├── requirements.txt              #   Python 依赖
│   ├── data/                         #   数据加载层
│   │   ├── loader.py                 #     直接从 CSV/MongoDB/Redis 加载
│   │   ├── api_loader.py             #     通过 Flask API 加载
│   │   └── source_detector.py        #     数据源可用性检测
│   ├── views/                        #   页面视图
│   │   ├── overview.py               #     总览页
│   │   ├── github_trending.py        #     GitHub 排行页
│   │   ├── multi_source.py           #     多源对比页
│   │   ├── trends.py                 #     趋势页
│   │   └── export.py                 #     导出页
│   ├── components/                   #   可复用组件
│   │   ├── charts.py                 #     Plotly 图表组件
│   │   ├── filters.py                #     筛选器组件
│   │   └── metrics.py                #     KPI 指标卡组件
│   └── utils/                        #   工具
│       └── clients.py                #     MongoDB/Redis 客户端封装
│
├── spiders/                          # Scrapy 爬虫系统
│   ├── run_hotspot.py                #   第二代多源爬虫启动脚本
│   ├── run_spider.py                 #   第一代 GitHub 单源爬虫启动脚本
│   ├── export_csv.py                 #   MongoDB 数据导出为 CSV
│   ├── scrapy.cfg                    #   Scrapy 配置
│   ├── requirements.txt              #   Python 依赖
│   ├── github_trending/              #   第一代爬虫（GitHub 单源）
│   │   ├── spiders/
│   │   │   └── github_trending_spider.py
│   │   ├── items.py
│   │   ├── pipelines.py
│   │   ├── middlewares.py
│   │   └── settings.py
│   └── scrapy_hotspot/               #   第二代爬虫（多源分布式）
│       ├── spiders/
│       │   ├── base_spider.py        #     爬虫基类
│       │   ├── github_spider.py      #     GitHub Trending
│       │   ├── hackernews_spider.py  #     Hacker News
│       │   ├── arxiv_spider.py       #     arXiv 论文
│       │   └── reddit_spider.py      #     Reddit
│       ├── items.py                  #   统一数据项
│       ├── pipelines.py              #   3 级 Pipeline
│       └── settings.py               #   分布式爬虫配置
│
├── tools/                            # 辅助工具
│   └── github_sentiment_analyzer.py  #   GitHub Issue 情感分析
│
├── visualization-platform/           # ECharts 前端仪表盘
│   ├── index.html                    #   单页应用
│   ├── vite.config.ts                #   Vite 构建配置
│   ├── package.json                  #   前端依赖
│   └── tsconfig.json                 #   TypeScript 配置
│
├── data/                             # 数据文件
│   ├── github_trending_daily.csv
│   ├── github_trending_weekly.csv
│   ├── github_trending_monthly.csv
│   └── hotspot_*.csv
│
├── prompts/                          # 设计文档
│   ├── ScrapyPrompt01.md             #   第一代爬虫设计
│   └── ScarpyPrompt02.md             #   第二代爬虫设计
│
├── README.md                         # 项目说明文档
├── useme.md                          # 使用指南
└── .gitignore                        # Git 忽略配置
```

---

## 三、技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 爬虫框架 | Scrapy 2.11+ / scrapy-redis | 分布式调度、去重 |
| 数据存储 | MongoDB 7.0 | 持久化存储（hotspot_* + insights 集合） |
| 缓存/队列 | Redis 7.0 | 去重 + 实时排行榜 + 任务队列 |
| 后端 API | Flask + flask-cors | RESTful 数据接口 |
| AI 分析 | DeepSeek API (deepseek-v4-pro) | 趋势洞察与智能分析 |
| 前端看板 | Streamlit | 5 页面交互式看板 |
| 前端仪表盘 | ECharts + Vite | 多页面数据可视化 |
| 语言 | Python 3.9+ / TypeScript | - |

---

## 四、爬虫系统详细设计

### 4.1 第一代爬虫：GitHub 单源（github_trending/）

**设计目标**：从 GitHub Trending 页面抓取 AI 相关热门项目。

**核心特性**：
- 爬虫名称：`github_trending_ai`
- 继承 `scrapy.Spider`（非分布式）
- 支持 daily/weekly/monthly 三种榜单周期
- 覆盖 14 种主流编程语言
- AI 关键词过滤（topics + description + name 匹配）
- 跨语言去重
- 输出为 CSV 文件

**提取字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `rank` | int | 全局排名（跨页累加） |
| `name` | str | 项目全名（owner/repo） |
| `owner` | str | 作者/组织名 |
| `description` | str | 项目描述 |
| `language` | str | 主要编程语言 |
| `stars` | int | 总星数 |
| `stars_since` | int | 本周期新增星数 |
| `forks` | int | Fork 数 |
| `topics` | List[str] | 话题标签列表 |
| `url` | str | 项目链接 |
| `crawl_time` | str | 抓取时间戳（ISO 8601） |
| `since` | str | 榜单周期 |
| `page` | str | 来源页码 |

**反爬策略**：
- `ROBOTSTXT_OBEY = True`
- AutoThrottle：下载延迟 3~6 秒
- User-Agent 轮换（scrapy-fake-useragent）
- 重试 3 次（500/502/503/504/408）
- `Accept-Language: en-US,en;q=0.9`

**运行方式**：
```bash
cd spiders
python run_spider.py --since daily --pages 3 --filter_keywords ai,llm,ml
```

---

### 4.2 第二代爬虫：多源分布式（scrapy_hotspot/）

**设计目标**：基于 Scrapy + Redis 的多源分布式爬虫，覆盖 4 个数据源。

**核心特性**：
- 所有爬虫继承 `scrapy_redis.spiders.RedisSpider`
- Redis 作为调度器和去重过滤器
- 支持多实例并行，共享任务队列和去重指纹
- 3 级 Pipeline：Redis 去重 → 实时排行榜 → MongoDB 持久化
- 按日期分片存储（`hotspot_YYYY_MM_DD`）

**统一数据项（HotspotItem）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `source` | str | 数据源标识（github/hackernews/arxiv/reddit） |
| `unique_id` | str | 唯一标识（如 owner/repo、post_id、paper_id） |
| `title` | str | 标题 |
| `url` | str | 链接 |
| `description` | str | 描述/摘要 |
| `author` | str | 作者 |
| `language` | str | 编程语言（仅 GitHub） |
| `score` | int | 原始分数 |
| `comments` | int | 评论数 |
| `stars` | int | 总星数（仅 GitHub） |
| `stars_since` | int | 本周期新增星数（仅 GitHub） |
| `forks` | int | Fork 数（仅 GitHub） |
| `topics` | List[str] | 话题标签（仅 GitHub） |
| `hot_score` | int | 热度分数（统一计算） |
| `range` | str | 时间范围（daily/weekly/monthly） |
| `published_at` | str | 发布时间 |
| `crawl_time` | str | 抓取时间戳 |
| `extra` | dict | 额外信息 |

**4 个爬虫详细设计**：

#### 4.2.1 GitHub Trending Spider

| 配置项 | 值 |
|--------|------|
| 爬虫名称 | `github_trending` |
| 目标 URL | `https://github.com/trending?since=daily` |
| 热度公式 | `hot_score = stars_since * 10 + forks * 5` |
| 去重依据 | `unique_id`（owner/repo） |
| 建议频率 | 每 6 小时 |

#### 4.2.2 Hacker News Spider

| 配置项 | 值 |
|--------|------|
| 爬虫名称 | `hackernews` |
| 目标 URL | `https://news.ycombinator.com/news?p=1~3` |
| 热度公式 | `hot_score = score + comments * 2` |
| 去重依据 | `post_id` |
| 建议频率 | 每 15 分钟 |

#### 4.2.3 arXiv Spider

| 配置项 | 值 |
|--------|------|
| 爬虫名称 | `arxiv` |
| 目标 URL | `https://arxiv.org/list/cs.AI/recent` + cs.LG + cs.CL |
| 热度公式 | `hot_score = 0`（暂不参与排行榜） |
| 去重依据 | `paper_id` |
| 建议频率 | 每天 2 次 |

#### 4.2.4 Reddit Spider

| 配置项 | 值 |
|--------|------|
| 爬虫名称 | `reddit` |
| 目标 URL | `https://www.reddit.com/r/MachineLearning/hot.json?limit=50` |
| 热度公式 | `hot_score = score + num_comments` |
| 去重依据 | `post_id`（name 字段，如 t3_xxxxx） |
| 建议频率 | 每 30 分钟 |

**Pipeline 处理流程**：

```
Item 产出
  │
  ▼
DeduplicationPipeline（优先级 100）
  │  检查 Redis Set 是否已存在
  │  不存在 → SADD → 继续
  │  已存在 → DropItem
  ▼
RedisHotScorePipeline（优先级 200）
  │  计算 hot_score
  │  ZADD hotspot:all <score> <item_id>
  │  ZADD hotspot:<source> <score> <item_id>
  ▼
MongoDBPipeline（优先级 300）
  │  存储完整 Item 到 MongoDB
  │  集合名：hotspot_YYYY_MM_DD
  ▼
完成
```

**Redis 数据结构**：

| 用途 | 数据结构 | Key 示例 |
|------|----------|----------|
| 任务队列 | List | `github:start_urls` |
| 全局去重 | Set | `seen:repo`、`seen:hn`、`seen:arxiv`、`seen:reddit` |
| 实时热度排行榜 | Sorted Set | `hotspot:all` |
| 按类别排行榜 | Sorted Set | `hotspot:github`、`hotspot:hn`、`hotspot:reddit` |
| Item 元数据缓存 | Hash | `item:github:owner/repo` |

**运行方式**：
```bash
# 1. 启动 Redis
redis-server

# 2. 推入起始 URL
redis-cli lpush github:start_urls "https://github.com/trending?since=daily"
redis-cli lpush hn:start_urls "https://news.ycombinator.com/news?p=1"
redis-cli lpush arxiv:start_urls "https://arxiv.org/list/cs.AI/recent"
redis-cli lpush reddit:start_urls "https://www.reddit.com/r/MachineLearning/hot.json?limit=50"

# 3. 启动爬虫
cd spiders
python run_hotspot.py
```

---

## 五、AI 深度分析模块设计

### 5.1 模块概述

`AI分析/` 是一个完全独立的 DeepSeek AI 分析模块，从 MongoDB 读取热点数据，调用 DeepSeek API 生成深度洞察。

### 5.2 核心类

#### MongoDBConnector

| 方法 | 功能 |
|------|------|
| `get_collections()` | 获取所有 hotspot_* 集合 |
| `get_latest_collection()` | 获取最新集合名 |
| `fetch_github_trending(collection, limit, source)` | 从 MongoDB 获取热点数据 |
| `save_insight(insight_data)` | 保存分析结果到 insights 集合 |

#### DeepSeekAnalyzer

| 方法 | 功能 |
|------|------|
| `analyze_projects(projects, max_retries)` | 调用 DeepSeek API 分析项目 |
| `_build_analysis_prompt(projects)` | 构建分析 Prompt（Top30 项目详情） |
| `_parse_analysis_result(content, projects)` | 解析 API 返回结果 |

### 5.3 四大分析维度

| 维度 | 输出数量 | 说明 |
|------|----------|------|
| 趋势识别 | 2-4 条 | 识别技术趋势方向，附量化支撑数据 |
| 值得关注的项目 | 3-5 个 | 精选高增长项目，含增长数据和推荐理由 |
| 学习路径 | 2-4 条 | 为开发者提供方向性学习建议 |
| 信号挖掘 | 2-4 条 | 发现隐藏信号，揭示潜在市场机会 |

### 5.4 Prompt 工程策略

- **System 角色**：设定为"专业技术趋势分析师，专注开源项目和AI技术领域"
- **User 角色**：包含 Top30 项目详情（名称、星数、增长、语言、描述、Topics）
- **输出约束**：严格 JSON 格式，中文输出，数据驱动
- **温度参数**：`temperature=0.7`（平衡创造性和准确性）
- **最大 Token**：`max_tokens=4000`

### 5.5 容错与重试机制

| 场景 | 策略 |
|------|------|
| HTTP 429（限流） | 等待 60 秒后重试 |
| 请求超时 | 120 秒超时，重试最多 3 次，间隔 10 秒 |
| JSON 解析失败 | 降级为正则表达式提取关键内容 |
| API Key 未设置 | 提前警告，不发送请求 |

### 5.6 运行方式

```bash
cd AI分析

# 设置 API Key
$env:DEEPSEEK_API_KEY="sk-your-api-key"

# 运行分析
python deepseek_analyzer.py

# 导入 CSV 数据（不使用爬虫时）
python import_data.py

# 定时任务（系统级）
# Windows: schtasks /create /sc hourly /mo 12 /tn "DeepSeek分析" /tr "python AI分析\deepseek_analyzer.py"
# Linux:   0 */12 * * * cd AI分析 && python deepseek_analyzer.py
```

### 5.7 输出格式

```json
{
  "趋势识别": ["...", "..."],
  "值得关注的项目": ["...", "..."],
  "学习路径": ["...", "..."],
  "信号挖掘": ["...", "..."],
  "metadata": {
    "projects_count": 100,
    "analyzed_at": "2026-05-25T14:20:18Z",
    "collection": "hotspot_2026_05_25",
    "model": "deepseek-v4-pro"
  }
}
```

---

## 六、API 服务设计

### 6.1 Flask API 端点

| 端点 | 方法 | 功能 | 关键参数 |
|------|------|------|----------|
| `/api/collections` | GET | 列出 MongoDB 集合 | — |
| `/api/sources` | GET | 数据源统计 | `collection` |
| `/api/hotspot` | GET | 热点数据查询 | `collection`, `source`, `page_size`, `page`, `sort`, `use_csv` |
| `/api/hotspot/stats` | GET | 聚合统计 | `collection`, `source` |
| `/api/hotspot/top` | GET | Top-N 排名 | `collection`, `source`, `metric`, `limit` |
| `/api/system/status` | GET | 系统健康检查 | — |
| `/api/system/overview` | GET | 全局概览 | `collection` |
| `/api/system/periods` | GET | 时间维度统计 | — |
| `/api/system/history` | GET | 爬虫历史 | — |
| `/api/ai-analysis/latest` | GET | 获取最新 AI 分析结果 | — |
| `/api/ai-analysis/list` | GET | 列出所有 AI 分析文件元信息 | — |

### 6.2 数据源优先级

```
1. MongoDB（实时数据，爬虫写入）
2. CSV 文件（use_csv=true 参数，735 条完整数据）
3. Redis（实时排行榜）
```

---

## 七、可视化系统设计

### 7.1 Streamlit 看板（port 8501）

| 页面 | 功能 |
|------|------|
| Overview | KPI 指标卡、语言分布、Top 项目 |
| GitHub Trending | 项目列表、筛选、排序 |
| Multi-Source | GitHub/HN/arXiv/Reddit 配对重叠分析 |
| Trends | 时间维度对比、增长趋势图 |
| Export | 数据导出为 CSV/JSON |

**特性**：深色/浅色主题切换、Plotly 交互式图表、多数据源加载

### 7.2 ECharts 仪表盘（port 3000）

| 页面 | 功能 |
|------|------|
| 数据概览 | 星数分布、语言占比、增长趋势、6种图表切换 |
| 趋势分析 | Stars/Forks/增长趋势、语言分布 |
| 数据对比 | 日榜vs周榜、周榜vs月榜、日榜vs月榜 |
| 多源对比 | GitHub/HN/arXiv/Reddit 交叉分析 |
| 洞察报告 | 关键发现、热度分析、语言热度分析 |
| AI分析 | DeepSeek AI 分析结果可视化、情感倾向分析 |

**特性**：Vite + TypeScript 构建、响应式布局、暗色主题、搜索功能、侧边栏筛选

---

## 八、数据流

```
1. 爬虫采集    spiders/ → Redis（去重+排行榜）→ MongoDB（hotspot_* 集合）
2. CSV 导入    data/*.csv → AI分析/import_data.py → MongoDB
3. 数据查询    MongoDB/CSV/Redis → api/server.py → 前端
4. 可视化展示   api/server.py → dashboard/（Streamlit）+ visualization-platform/（ECharts）
5. AI 分析     MongoDB → AI分析/deepseek_analyzer.py → DeepSeek API → MongoDB（insights 集合）+ JSON 文件
6. 报告导出    MongoDB（insights）→ AI分析/export_report.py → AI分析/output/*.txt
```

---

## 九、服务端口汇总

| 服务 | 端口 | 启动命令 |
|------|------|----------|
| MongoDB | 27017 | `mongod --dbpath /path/to/data` |
| Redis | 6379 | `redis-server` |
| Flask API | 5000 | `cd api && python server.py` |
| Streamlit | 8501 | `streamlit run dashboard/app.py --server.port=8501` |
| ECharts | 3000 | `cd visualization-platform && npx vite --port=3000 --host` |

---

## 十、环境与依赖

### 10.1 系统依赖

- Python 3.9+
- Node.js 18+（ECharts 仪表盘）
- MongoDB 7.0
- Redis 7.0

### 10.2 Python 依赖

```bash
# API 服务
pip install -r api/requirements.txt          # flask, flask-cors, pymongo

# 爬虫系统
pip install -r spiders/requirements.txt      # scrapy, scrapy-redis, pymongo, redis

# Streamlit 看板
pip install -r dashboard/requirements.txt    # streamlit, plotly, pandas

# AI 分析（独立模块）
pip install -r AI分析/requirements.txt       # pymongo, requests
```

### 10.3 前端依赖

```bash
cd visualization-platform && npm install && cd ..
```

### 10.4 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | AI 分析必需 |
| `GITHUB_TOKEN` | GitHub Personal Access Token | 情感分析可选 |

---

## 十一、安全设计

| 安全项 | 措施 |
|--------|------|
| API Key 管理 | 全部通过环境变量，不硬编码到源码 |
| 数据库连接 | 默认 localhost，生产环境应配置认证 |
| 爬虫合规 | `ROBOTSTXT_OBEY`、AutoThrottle、下载延迟 |
| 日志安全 | 敏感信息不记录到日志文件 |
| API 跨域 | flask-cors 配置，生产环境应限制来源 |

---

## 十二、更新日志

### 第一次更新
- 第一代 GitHub 单源爬虫（github_trending/）

### 第二次更新
- 第二代多源分布式爬虫（scrapy_hotspot/）
- Redis 去重 + 实时排行榜 + MongoDB 持久化

### 第三次更新
- Flask API 统一数据层
- Streamlit 看板

### 第四次更新
- ECharts 前端仪表盘
- 多源对比分析

### 第五次更新（2026-05-25）
- DeepSeek AI 深度分析功能集成
- 独立模块 `AI分析/`
- CSV 数据导入工具
- AI 分析报告导出

### 第六次更新（2026-05-25）
- 项目结构优化：AI 分析模块独立化
- 清理重复文件（tools/deepseek_analyzer.py、api/scheduler.py、api/import_csv.py）
- 清理 api/server.py 中 DeepSeek 相关代码
- 修复 Windows GBK 编码错误
- 修复 import_data.py CSV 路径（visualization-platform/public → data）
- 修复 github_sentiment_analyzer.py 硬编码 Token
- 修复 export_report.py 输出路径（tools/output → AI分析/output）
- 全面修正 README.md 和 useme.md 中的旧路径引用

### 第七次更新（2026-05-26）
- ECharts 仪表盘新增"AI分析"视图（第6个页面）
- 新增 Flask API 端点：`/api/ai-analysis/latest` 和 `/api/ai-analysis/list`
- AI 分析界面包含：KPI 卡片、趋势识别、值得关注的项目、学习路径、信号挖掘、情感倾向分析饼图
- 情感倾向分析基于中文关键词匹配，将 AI 分析文本分为正面/中性/负面三类
- 项目目录结构修正：移除根目录下不存在的 `export_report.py`
