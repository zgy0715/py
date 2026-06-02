# Tech Hotspot · 技术热点数据平台

多源技术热点数据采集、存储、分析与可视化平台。自动爬取 GitHub Trending、Hacker News、arXiv、Reddit 等多平台的热点项目/文章，通过统一 API 提供数据服务，并在 Streamlit 看板和 ECharts 仪表盘中进行可视化分析。集成 DeepSeek AI 深度分析引擎，自动挖掘技术趋势、推荐值得关注的项目、生成学习路径和信号洞察。

---

## 架构概览

```
推送 URL 到 Redis 队列
       │
       ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│  GitHub     │    │  HackerNews  │    │  arXiv      │    │  Reddit     │
│  Trending   │    │  Front Page  │    │  CS Papers  │    │  r/ML       │
│  Spider     │    │  Spider      │    │  Spider     │    │  Spider     │
└──────┬──────┘    └──────┬───────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                   │                   │
       ▼                  ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Pipeline 链 (3 级)                               │
│  1. DeduplicationPipeline  —  Redis Set 去重                          │
│  2. RedisHotScorePipeline  —  实时排行榜 + 缓存                        │
│  3. MongoDBPipeline        —  持久化存储                               │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                      ┌────────▼────────┐
                      │    MongoDB      │
                      │  tech_hotspot   │
                      │  hotspot_* 集合  │
                      └────────┬────────┘
                               │
                  ┌────────────┼────────────┐
                  │            │            │
        ┌─────────▼─────────┐  │  ┌────────▼─────────┐
        │   Flask API       │  │  │  DeepSeek AI     │
        │  (server.py)      │  │  │  分析引擎         │
        │   port 5000       │  │  │  (deepseek_       │
        └─────────┬─────────┘  │  │   analyzer.py)   │
                  │            │  └────────┬─────────┘
                  │            │           │
                  │     ┌──────▼──────┐   │
                  │     │ insights    │◄──┘
                  │     │ 集合(MongoDB)│
                  │     └─────────────┘
                  │
        ┌─────────▼──────────────┐
        │  Streamlit  │  Vite +  │
        │  交互看板    │  ECharts │
        │  port 8501  │  port 3000│
        └────────────────────────┘
```

---

## 项目结构

```
├── api/                              # Flask RESTful API 服务
│   ├── server.py                     #   核心接口
│   └── requirements.txt              #   Python 依赖
│
├── dashboard/                        # Streamlit 可视化看板
│   ├── app.py                        #   入口（数据加载与页面路由）
│   ├── config.py                     #   配置（CSV 路径、颜色映射、主题常量）
│   ├── requirements.txt              #   Python 依赖
│   ├── data/                         # 数据加载层
│   │   ├── loader.py                 #   CSV/MongoDB/Redis 直接加载
│   │   ├── api_loader.py             #   通过 Flask API 加载（跨集合来源聚合）
│   │   └── source_detector.py        #   数据源可用性检测
│   ├── views/                        # 页面视图
│   │   ├── overview.py               #   总览页
│   │   ├── github_trending.py        #   GitHub 排行页
│   │   ├── multi_source.py           #   多源对比页（全源配对重叠分析）
│   │   ├── trends.py                 #   趋势页
│   │   └── export.py                 #   导出页
│   ├── components/                   # 可复用组件
│   │   ├── charts.py                 #   Plotly 图表（深色/浅色自适应）
│   │   ├── filters.py                #   筛选器组件
│   │   └── metrics.py                #   KPI 指标卡
│   └── utils/                        # 工具
│       └── clients.py                #   MongoDB/Redis 客户端
│
├── spiders/                          # Scrapy 爬虫系统
│   ├── run_hotspot.py                #   第二代分布式爬虫启动脚本
│   ├── run_spider.py                 #   第一代爬虫启动脚本
│   ├── export_csv.py                 #   MongoDB → CSV 导出
│   ├── scrapy.cfg                    #   Scrapy 配置
│   ├── requirements.txt              #   Python 依赖
│   ├── github_trending/              # 第一代：GitHub 单源爬虫
│   └── scrapy_hotspot/               # 第二代：多源分布式爬虫
│
├── tools/                            # 辅助工具
│   └── github_sentiment_analyzer.py  #   GitHub Issue 情感分析
│
├── AI分析/                           # DeepSeek AI 深度分析（独立模块）
│   ├── deepseek_analyzer.py          #   AI 分析主程序（MongoDBConnector + DeepSeekAnalyzer）
│   ├── import_data.py                #   CSV 数据导入工具
│   ├── requirements.txt              #   Python 依赖
│   ├── output/                       #   分析结果输出（JSON 格式）
│   ├── insight_analysis.log          #   AI 分析日志（自动生成）
│   ├── import_data.log               #   数据导入日志（自动生成）
│   └── README.md                     #   模块说明文档
│
├── visualization-platform/           # ECharts 前端仪表盘
│   ├── index.html                    #   单页应用（多源跨集合数据聚合）
│   ├── vite.config.ts                #   Vite 配置
│   └── package.json                  #   前端依赖
│
├── data/                             # 数据文件
│   ├── github_trending_daily.csv
│   ├── github_trending_weekly.csv
│   ├── github_trending_monthly.csv
│   ├── hotspot_*.csv                 #   MongoDB 导出的 CSV
│   └── *_comments_analysis.json      #   情感分析结果
│
├── prompts/                          # 设计文档
├── AIprompt/                         # 设计文档（Obsidian）
├── .gitignore
├── README.md                         # 本文件
└── useme.md                          # 使用指南
```

---

## 技术栈

| 层 | 技术 | 用途 |
|----|------|------|
| 爬虫框架 | Scrapy 2.15 + scrapy-redis | 网页数据抓取 + 分布式调度 |
| 消息队列 | Redis | URL 队列、去重、实时排行榜 |
| 持久存储 | MongoDB | 数据持久化 |
| API 层 | Flask 3.x | RESTful 接口 |
| 看板 | Streamlit + Plotly | 交互式可视化 |
| 前端 | Vite + ECharts 5 (CDN) | 可视化仪表盘 |
| 分析 | TextBlob + GitHub API | 情感分析 |
| AI 分析 | DeepSeek API (deepseek-chat) | 趋势洞察与智能分析 |

---

## DeepSeek AI 深度分析

### 功能特性

DeepSeek AI 分析引擎基于 DeepSeek 大语言模型对采集的技术热点数据进行深度挖掘和智能分析，提供四大核心能力：

| 能力维度 | 说明 | 输出示例 |
| -------- | ---- | -------- |
| 趋势识别 | 从海量项目中识别 2-4 条技术趋势方向，结合增长数据提供量化支撑 | "Rust渗透进AI工具链，本周3个新项目涉及Rust+LLM推理" |
| 值得关注的项目 | 精选 3-5 个高增长项目，包含项目名、增长数据、定位与推荐理由 | "rtk-ai/rtk (本周+21,036星): Rust实现的CLI代理，降低LLM令牌消耗90%" |
| 学习路径 | 为开发者提供 2-4 条方向性学习建议，附推荐技术栈 | "Rust在AI推理领域崛起，建议学习candle/llama.cpp" |
| 信号挖掘 | 发现 2-4 条隐藏信号，揭示潜在市场机会或技术转向 | "免费/低成本AI编码工具需求强烈，相关项目本周共获超3万星" |

### 技术架构

DeepSeek 分析模块采用**数据读取 → Prompt 组装 → API 调用 → 结果解析 → 持久化**的流水线架构：

```
┌──────────────────────────────────────────────────────────────────┐
│                    DeepSeek 分析流水线                            │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐ │
│  │ MongoDB  │──▶│ Prompt   │──▶│ DeepSeek │──▶│ 结果解析与    │ │
│  │ 数据读取 │   │ 动态组装 │   │ API 调用 │   │ 持久化存储   │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────────┘ │
│       │              │              │               │            │
│  hotspot_*      Top30 项目     deepseek-chat    insights 集合   │
│  集合查询       摘要构建       Chat Completions  + JSON 文件     │
└──────────────────────────────────────────────────────────────────┘
```

**核心组件：**

| 组件 | 文件 | 职责 |
| ---- | ---- | ---- |
| `MongoDBConnector` | `AI分析/deepseek_analyzer.py` | MongoDB 连接管理、hotspot 数据读取、insights 结果写入 |
| `DeepSeekAnalyzer` | `AI分析/deepseek_analyzer.py` | Prompt 构建、API 调用（含重试/限流处理）、结果解析 |

**容错与重试机制：**

- 最多 3 次重试，每次间隔 10 秒
- HTTP 429（限流）自动等待 60 秒后重试
- 请求超时 120 秒，超时后重试
- JSON 解析失败时降级为正则表达式提取关键内容
- 解析完全失败时返回兜底结果，避免流程中断

### 使用场景

| 场景 | 触发方式 | 说明 |
| ---- | -------- | ---- |
| 手动单次分析 | `cd AI分析 && python deepseek_analyzer.py` | 立即对最新数据执行一次完整分析 |
| 定时自动分析 | 系统定时任务（crontab / schtasks） | 每12小时自动分析 |
| CSV 数据导入 | `cd AI分析 && python import_data.py` | 从 CSV 文件导入数据到 MongoDB |

### 性能评估

| 指标 | 数值 | 说明 |
| ---- | ---- | ---- |
| 单次分析项目数 | 50-100 | Prompt 中注入 Top30 项目详情，其余仅统计 |
| API 响应时间 | 30-60s | 取决于 DeepSeek API 负载和输出长度 |
| Token 消耗 | ~4000 tokens/次 | max_tokens 设为 4000，实际消耗视输出长度 |
| 重试上限 | 3 次 | 超过后返回错误，避免无限等待 |
| 结果持久化 | MongoDB + JSON | 双重存储：insights 集合 + output/ 目录文件 |

---

## 快速开始

### 服务端口汇总

| 服务 | 端口 | 启动命令 | 访问地址 |
|------|------|----------|----------|
| Flask API | 5000 | `python api/server.py` | http://localhost:5000 |
| Streamlit 看板 | 8501 | `streamlit run dashboard/app.py --server.port=8501` | http://localhost:8501 |
| ECharts 仪表盘 | 3000 | `npx vite --port 3000 --host` | http://localhost:3000 |
| MongoDB | 27017 | 需预先启动 | - |
| Redis | 6379 | 需预先启动 | - |

### 前置条件

- Python 3.10+
- MongoDB（默认 `localhost:27017`）
- Redis（默认 `localhost:6379`）
- Node.js 16+（前端开发）
- DeepSeek API Key（AI 分析功能，[获取地址](https://platform.deepseek.com/)）

### 安装依赖

```bash
# 一次性安装所有 Python 依赖
pip install -r api/requirements.txt -r dashboard/requirements.txt -r spiders/requirements.txt

# AI 分析依赖（独立安装）
pip install -r AI分析/requirements.txt

# 前端依赖
cd visualization-platform && npm install && cd ..
```

### 启动服务（推荐顺序）

```bash
# 1. 确保 MongoDB 和 Redis 已运行
#    Windows: mongod --dbpath C:\data\db
#    Linux/Mac: mongod --dbpath /path/to/data

# 2. 启动 Flask API（必须先启动，其他服务依赖此接口）
python api/server.py
# → http://localhost:5000

# 3. 启动 Streamlit 看板（新开终端）
streamlit run dashboard/app.py --server.port=8501
# → http://localhost:8501

# 4. 启动前端仪表盘（新开终端）
cd visualization-platform && npx vite --port 3000 --host
# → http://localhost:3000

# 5. 配置 AI 分析定时任务（可选）
# Linux/Mac (crontab):
#   0 */12 * * * cd /path/to/AI分析 && python deepseek_analyzer.py
# Windows (schtasks):
#   schtasks /create /tn "DeepSeek分析" /tr "python D:\path\to\AI分析\deepseek_analyzer.py" /sc hourly /mo 12
```

### 启动状态检查

```bash
# 检查 API 是否正常运行
curl http://localhost:5000/api/system/status

# 检查 Streamlit 是否正常运行
curl -s http://localhost:8501 | head -5

# 检查前端仪表盘是否正常运行
curl -s http://localhost:3000 | head -5
```

### 启动 DeepSeek AI 分析

**配置 API Key：**

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-your-api-key"

# Linux/Mac
export DEEPSEEK_API_KEY="sk-your-api-key"
```

**手动单次分析：**

```bash
cd AI分析 && python deepseek_analyzer.py
```

**定时自动分析（每12小时）：**

```bash
# Linux/Mac (crontab)
0 */12 * * * cd /path/to/AI分析 && python deepseek_analyzer.py

# Windows (schtasks)
schtasks /create /tn "DeepSeek分析" /tr "python D:\path\to\AI分析\deepseek_analyzer.py" /sc hourly /mo 12
```

### 运行爬虫（可选）

```bash
cd spiders

# 完整运行（推送 URL + 启动全部爬虫）
python run_hotspot.py

# 单独运行某个爬虫
SCRAPY_SETTINGS_MODULE=scrapy_hotspot.settings scrapy crawl github_trending
SCRAPY_SETTINGS_MODULE=scrapy_hotspot.settings scrapy crawl hackernews
SCRAPY_SETTINGS_MODULE=scrapy_hotspot.settings scrapy crawl arxiv
SCRAPY_SETTINGS_MODULE=scrapy_hotspot.settings scrapy crawl reddit
```

---

## 功能展示

### Streamlit 看板（5 个页面）

| 页面 | 功能 |
|------|------|
| **Overview 总览** | KPI 指标卡、Top N 排行、语言分布饼图、Stars vs Forks 散点图、每日趋势 |
| **GitHub Trending** | 日/周/月切换、项目详情表格、Stars vs Forks 散点分析 |
| **Multi-Source 多源对比** | 跨源 KPI 对比、全局 Top 20、全源配对重叠分析、热度分布 |
| **Trends 趋势** | 时段项目数对比、平均日增长、语言×时段热力图、分时段散点 |
| **Export 导出** | CSV/JSON 一键导出、按源/时段筛选 |

### ECharts 前端仪表盘（3 个页面）

| 页面 | 功能 |
|------|------|
| **GitHub 总览** | 6 种图表切换（柱状/折线/饼图/散点/雷达/热力）、日/周/月切换、4 种指标 |
| **时段对比** | 日/周/月 KPI 对比、Top 10 对比图、详细排行表 |
| **多源对比** | 各源分布饼图、热度对比、语言分布、全局 Top 20、各源详情 Tab |

### DeepSeek AI 分析

| 功能 | 说明 |
|------|------|
| **趋势识别** | 识别 2-4 条技术趋势方向，结合增长数据提供量化支撑 |
| **值得关注的项目** | 精选 3-5 个高增长项目，含项目名、增长数据、定位与推荐理由 |
| **学习路径** | 提供 2-4 条方向性学习建议，附推荐技术栈 |
| **信号挖掘** | 发现 2-4 条隐藏信号，揭示潜在市场机会或技术转向 |

### 导出功能

- **CSV 导出**：UTF-8 BOM 编码，Excel 直接打开无乱码
- **JSON 导出**：格式化缩进，便于程序处理

---

## API 接口

| 端点 | 方法 | 说明 | 参数 |
|------|------|------|------|
| `GET /api/system/status` | GET | 系统状态（Tier、数据源、集合信息） | — |
| `GET /api/system/overview` | GET | 数据概览（总项目数、各源数量） | — |
| `GET /api/system/periods` | GET | 各时段统计（Top 10、总量、平均增长） | — |
| `GET /api/collections` | GET | 列出可用日期集合 | — |
| `GET /api/sources` | GET | 各数据源在各集合中的数量 | — |
| `GET /api/hotspot` | GET | 热点数据查询 | `collection`, `source`, `range`, `sort_by`, `order`, `limit`, `offset`, `use_csv` |
| `GET /api/hotspot/stats` | GET | 聚合统计 | `collection`, `source` |
| `GET /api/hotspot/top` | GET | Top-N 排名 | `collection`, `source`, `metric`, `limit` |

> `use_csv=true` 参数：从 CSV 文件加载 GitHub 数据（735 条完整数据），不传则从 MongoDB 加载。

---

## 爬虫数据源

### GitHub Trending

- 爬取 14 种编程语言的 Trending 页面
- 三种时间范围：daily / weekly / monthly
- 热度分公式：`stars_since × 10 + forks_since × 5`
- Topics 采集：4 级 CSS 选择器回退，确保兼容页面结构变化

### Hacker News

- 爬取首页前 3 页
- 热度分公式：`score + comments × 2`

### arXiv

- 爬取 cs.AI / cs.LG / cs.CL 三个板块的 recent 论文
- 过滤 3 天内发布的新论文

### Reddit

- 爬取 r/MachineLearning 的 hot 帖子
- 热度分公式：`score + comments`

---

## 数据流

1. **推送阶段** — `run_hotspot.py` 将起始 URL 推送到 Redis 队列
2. **爬取阶段** — Scrapy 从 Redis 队列消费 URL，各 spider 解析网页/API
3. **处理阶段** — Pipeline 链依次执行：去重 → 实时排行榜 → MongoDB 持久化
4. **服务阶段** — Flask API 从 MongoDB/CSV 读取数据，提供 RESTful 接口
5. **AI 分析阶段** — `AI分析/` 模块读取 MongoDB 数据，调用 DeepSeek API 生成趋势洞察并写入 insights 集合
6. **展示阶段** — Streamlit 看板和 ECharts 仪表盘从 API 获取数据渲染可视化

---

## 数据源概览

| 数据源 | 存储位置 | hot_score 公式 |
|--------|---------|---------------|
| GitHub Trending | CSV + MongoDB | `stars_since × 10 + forks_since × 5` |
| Hacker News | MongoDB | `score + comments × 2` |
| arXiv | MongoDB | 固定为 0 |
| Reddit | MongoDB | `score + comments` |
| Redis 排行榜 | Redis | — |

---

## 情感分析

项目包含 GitHub Issue 情感分析工具 `tools/github_sentiment_analyzer.py`，详细使用说明见 [useme.md](useme.md)。

```bash
# 安装依赖
pip install requests textblob

# 运行分析
python tools/github_sentiment_analyzer.py
```

---

## License

MIT

---

## 更新

### 第一次更新（2026-05-19）

**项目结构重组**
- 删除根目录重复的 `github_trending/`、`scrapy_hotspot/`、`run_spider.py`、`run_hotspot.py`、`export_csv.py`、`scrapy.cfg`（保留 `spiders/` 中的完善版本，包含 `base_spider.py` 和 range 感知去重）
- 移除根目录重复 CSV、`web/` 备用看板、`trending_sample.html`、`new add README.md`、空文件 `run.py`
- 移除 `visualization-platform/public/` 和 `dist/` 中的冗余 CSV 副本
- 移动 `requirements-dashboard.txt` → `dashboard/requirements.txt`

**多源对比修复**
- `api_loader.py`：改用 `/api/sources` 跨所有 MongoDB 集合聚合来源，每个来源从数据最多的集合拉取数据
- `index.html`：同样改为跨集合发现最佳数据源
- `multi_source.py`：重叠分析从固定的 GitHub+HN 改为自动检测所有来源对，支持任意来源组合的 URL/名称重叠分析

**API 容错增强**
- `_get_collections()`、`/api/sources`、`/api/system/overview` 添加 MongoDB 断连时的 try/except 保护
- 不再因 MongoDB 不可用导致 API 500 错误

### 第二次更新（2026-05-19）

**多源页 UI 清理**
- Streamlit 多源对比页：移除无意义的 "No overlapping URLs" 提示信息，只有当来源间确有重叠内容时才展示分析
- index.html 多源详情 Tab：按来源类型动态显示字段（GitHub 显示 Stars，其余显示 Score）
- index.html 全局 Top 20 表：同理按源类型显示对应指标字段，避免非 GitHub 项目错误显示 Stars: 0

**数据流验证**
- 确认 Streamlit 和 index.html 均通过 Flask API 从 MongoDB 获取多源数据
- 确认 4 个来源数据齐全（GitHub 735 条、HN 50 条、arXiv 300 条、Reddit 50 条）

**文档更新**
- 删除 `运行步骤.md`，内容整合至 README
- 重写 README.md，修正目录结构、更新功能描述

### 第三次更新（2026-05-20）

**功能增强**
- 新增**暗色主题**支持，点击头部月亮图标切换
- 新增**搜索功能**，支持按项目名、描述、语言、作者实时搜索
- 新增**右侧 KPI 面板**，展示关键指标卡片、统计摘要、数据来源信息
- 新增**侧边栏**，包含数据源选择、时间范围、图表类型网格（5种）
- 新增**数据范围选择器**（前10/前25/前50），优化图表密度

**多源对比优化**
- 修复"各源平均热度分"数据：过滤无有效热度分的数据源（arXiv），确保统计准确性
- 移除热力图组件（视觉效果不佳），保留柱状/折线/饼图/散点/雷达 5 种图表

**API 集成**
- 集成 Flask API 服务器（http://localhost:5000）
- 支持 MongoDB/CSV/Redis 三级数据源降级
- 完整支持多源数据对比（GitHub、Hacker News、arXiv、Reddit）

**UI 改进**
- 现代化卡片设计（圆角、阴影、悬停效果）
- 渐变色柱状图和面积图
- 导出下拉菜单（CSV/JSON）
- 响应式布局优化，移动端适配

**Bug 修复**
- 修复图表数据过多导致的标签重叠问题
- 修复热力图视觉呈现不佳的问题

### 第四次更新（2026-05-20）

**新增功能模块**
- 新增**趋势分析**视图：Stars 趋势、Forks 趋势、增长趋势、语言分布四个子标签，支持前10/前50/全部数据范围
- 新增**数据对比**视图：日榜 vs 周榜、周榜 vs 月榜、日榜 vs 月榜三种对比模式，左右双栏对比+汇总对比图
- 新增**洞察报告**视图：关键发现（Top Stars/增长最快/最高热度）、热度分析、动态趋势洞察卡片、语言热度分析图表

**导航优化**
- 日榜/周榜/月榜仅保留在左侧边栏，移除概览页顶部重复的榜单导航
- 顶部导航栏扩展为5个视图：数据概览 | 趋势分析 | 数据对比 | 多源对比 | 洞察报告

**图表优化**
- 重新添加"全部"数据维度，完整展示所有数据不截断
- 选择"全部"时图表高度自动扩展至600px，X轴标签旋转60°确保文字完整显示
- 柱状图/折线图在"全部"模式下自动缩小柱宽和数据点大小，避免视觉密集
- 移除热力图组件（视觉效果不佳）

**快速操作功能**
- "刷新数据"按钮：触发数据重新加载，显示加载中/成功/失败状态反馈
- "重置视图"按钮：重置所有筛选条件和图表状态至默认值，显示操作成功反馈

**数据来源**
- 所有功能模块数据均从 Flask API（MongoDB/CSV/Redis）获取，确保实时更新

### 第五次更新（2026-05-25）

**DeepSeek AI 深度分析集成**

本更新将 DeepSeek 大语言模型深度分析功能全面整合到项目中，实现了从数据采集到智能洞察的完整闭环。

#### 📁 新增文件

| 文件 | 路径 | 功能说明 |
|------|------|----------|
| `deepseek_analyzer.py` | `AI分析/deepseek_analyzer.py` | DeepSeek AI 分析主程序，包含 `MongoDBConnector`（MongoDB 连接管理、数据读取、结果写入）和 `DeepSeekAnalyzer`（Prompt 构建、API 调用、结果解析）两个核心类，支持独立运行和日志记录 |
| `import_data.py` | `AI分析/import_data.py` | CSV 数据导入工具，包含 `CSVToMongoImporter` 类，支持自动检测数据目录、动态集合名、批量导入 |
| `requirements.txt` | `AI分析/requirements.txt` | Python 依赖（pymongo>=4.6, requests>=2.28） |
| `README.md` | `AI分析/README.md` | 模块独立说明文档 |

#### 📂 AI分析 独立模块

`AI分析/` 目录是一个完全独立的 DeepSeek AI 分析模块，与源项目 `D:\download\hot-open-project-AI\第二次api接入分析` 结构一致：

```
AI分析/
├── deepseek_analyzer.py   # AI 分析主程序（MongoDBConnector + DeepSeekAnalyzer）
├── import_data.py         # CSV 数据导入工具（CSVToMongoImporter）
├── requirements.txt       # Python 依赖
├── output/                # 分析结果输出（JSON 格式，自动创建）
├── insight_analysis.log   # AI 分析日志（自动生成）
├── import_data.log        # 数据导入日志（自动生成）
└── README.md              # 模块说明文档
```

**运行方式：**
```bash
cd AI分析

# 安装依赖
pip install -r requirements.txt

# 设置 API Key
$env:DEEPSEEK_API_KEY="your-api-key"

# 运行分析
python deepseek_analyzer.py

# 或导入数据
python import_data.py
```

#### 🚀 核心功能

**四大分析维度：**
- **趋势识别**：从海量项目中识别 2-4 条技术趋势方向，结合增长数据提供量化支撑
- **值得关注的项目**：精选 3-5 个高增长项目，包含项目名、增长数据、定位与推荐理由
- **学习路径**：为开发者提供 2-4 条方向性学习建议，附推荐技术栈
- **信号挖掘**：发现 2-4 条隐藏信号，揭示潜在市场机会或技术转向

**三种运行方式：**
1. **手动单次分析**：`cd AI分析 && python deepseek_analyzer.py`
2. **定时自动分析**：系统定时任务（crontab / schtasks）
3. **CSV 数据导入**：`cd AI分析 && python import_data.py`

**容错与重试机制：**
- 最多 3 次重试，每次间隔 10 秒
- HTTP 429（限流）自动等待 60 秒后重试
- 请求超时 120 秒，超时后重试
- JSON 解析失败时降级为正则表达式提取关键内容

#### 🔒 安全特性

- API Key 通过环境变量 `DEEPSEEK_API_KEY` 管理，避免硬编码
- 所有敏感信息不记录到日志文件
- API 调用支持超时和错误处理，防止信息泄露

#### 📊 输出格式

分析结果以 JSON 格式输出，包含四大分析维度和元数据：

```json
{
  "趋势识别": ["...", "..."],
  "值得关注的项目": ["...", "..."],
  "学习路径": ["...", "..."],
  "信号挖掘": ["...", "..."],
  "metadata": {
    "projects_count": 100,
    "analyzed_at": "2026-05-25T07:46:55Z",
    "collection": "hotspot_2026_05_25",
    "model": "deepseek-v4-pro"
  }
}
```

#### 📝 日志配置

| 日志文件 | 记录器名称 | 路径 | 说明 |
|----------|------------|------|------|
| `insight_analysis.log` | `insight_analyzer` | `AI分析/insight_analysis.log` | AI 分析主日志，记录完整分析流程 |
| `import_data.log` | `import_data` | `AI分析/import_data.log` | 数据导入日志 |

**日志输出示例：**
```
2026-05-25 14:16:27,791 - insight_analyzer - INFO - 所有组件初始化成功
2026-05-25 14:16:27,791 - insight_analyzer - INFO - 开始运行分析...
2026-05-25 14:16:27,818 - insight_analyzer - INFO - 获取到 17 条数据
2026-05-25 14:16:27,818 - insight_analyzer - INFO - 步骤2: 构建分析prompt...
2026-05-25 14:16:42,072 - insight_analyzer - INFO - 洞察已保存，ID: 6a1297ca7440d878b47c7711
2026-05-25 14:16:42,172 - insight_analyzer - INFO - 分析完成!
```

#### 🔗 与原有功能的集成

- 分析数据从 MongoDB `hotspot_*` 集合读取，与爬虫系统无缝对接
- 分析结果保存到 MongoDB `insights` 集合，可通过 API 查询
- 支持与 Streamlit 看板和 ECharts 仪表盘集成展示
- 分析报告自动保存到 `AI分析/output/` 目录（JSON 格式）
- 运行分析时自动生成日志文件到 `AI分析/` 目录

### 第六次更新（2026-05-25）

**项目结构优化：AI 分析模块独立化**

将 DeepSeek AI 分析功能从分散在多个目录中整合为独立模块 `AI分析/`，消除重复代码，简化项目结构。

#### 🗑️ 删除的重复文件

| 文件 | 原路径 | 删除原因 |
|------|--------|----------|
| `deepseek_analyzer.py` | `tools/deepseek_analyzer.py` | 与 `AI分析/deepseek_analyzer.py` 重复 |
| `ai_analysis_report_2026-05-25.txt` | `tools/output/` | 与 `AI分析/output/` 重复 |
| `scheduler.py` | `api/scheduler.py` | 新加的定时任务，`AI分析/` 独立模块不需要 |
| `import_csv.py` | `api/import_csv.py` | 与 `AI分析/import_data.py` 重复 |

#### 🔧 清理的文件

| 文件 | 清理内容 |
|------|----------|
| `api/server.py` | 移除 DeepSeek API 配置（`DEEPSEEK_API_KEY`、`DEEPSEEK_API_URL`、`DEEPSEEK_MODEL`）；移除 `requests`、`re`、`time`、`datetime` 等仅为 AI 分析引入的依赖；移除 4 个辅助函数（`_fetch_github_trending`、`_build_prompt`、`_call_deepseek`、`_parse_result`）；移除 3 个 AI 分析端点（`POST /api/analyze`、`GET /api/insights`、`GET /api/insights/<id>`）；移除启动时的 DeepSeek API Key 检查 |
| `api/requirements.txt` | 移除 `requests>=2.28`（仅为 DeepSeek API 调用添加的依赖） |

#### 🐛 修复的问题

| 问题 | 修复内容 |
|------|----------|
| Windows GBK 编码错误 | `AI分析/deepseek_analyzer.py` 中 `print` 输出包含 emoji 字符（📊、【】），在 Windows GBK 终端下报 `UnicodeEncodeError`，已替换为 ASCII 兼容字符 |

#### 📂 优化后的项目结构

**优化前（AI 分析代码分散在 3 个目录）：**
```
tools/deepseek_analyzer.py     # 分析主程序
tools/output/                  # 分析结果
api/server.py                  # 含 AI 分析端点
api/scheduler.py               # 定时任务
api/import_csv.py              # CSV 导入
api/requirements.txt           # 含 requests 依赖
```

**优化后（AI 分析代码集中在 1 个目录）：**
```
AI分析/
├── deepseek_analyzer.py       # 分析主程序
├── import_data.py             # CSV 导入
├── requirements.txt           # 独立依赖
├── output/                    # 分析结果
├── insight_analysis.log       # 分析日志
├── import_data.log            # 导入日志
└── README.md                  # 模块文档
```

#### 📝 文档更新

| 文件 | 更新内容 |
|------|----------|
| `README.md` | 项目结构移除已删除文件；API 接口表移除 3 个 AI 端点；使用场景表更新为 `AI分析/` 路径；安装依赖新增 `AI分析/requirements.txt`；日志路径更新为 `AI分析/` 目录 |
| `useme.md` | 运行方式更新为 `cd AI分析 && python deepseek_analyzer.py`；定时任务改为系统定时任务（crontab / schtasks）；常见问题移除对已删除文件的引用 |

### 第七次更新（2026-05-26）

**ECharts 仪表盘 AI 分析界面集成**

#### 📊 新增功能

在 `visualization-platform/index.html` 中新增 **AI分析** 视图，将 DeepSeek AI 分析结果可视化展示：

| 功能模块 | 说明 |
|----------|------|
| **KPI 卡片** | 展示分析模型、分析时间、项目数量、洞察总数四个关键指标 |
| **趋势识别** | 展示 AI 识别的技术趋势方向（蓝色主题） |
| **值得关注的项目** | 展示高增长项目推荐（绿色主题） |
| **学习路径** | 展示开发者学习建议（紫色主题） |
| **信号挖掘** | 展示隐藏信号和潜在机会（橙色主题） |
| **情感倾向分析** | 环形饼图展示正面/中性/负面情感分布 |

#### 🔌 新增 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `GET /api/ai-analysis/latest` | GET | 读取 `AI分析/output/` 目录下最新的 `insight_*.json` 文件 |
| `GET /api/ai-analysis/list` | GET | 列出所有分析文件的元信息（时间、模型、项目数等） |

#### 📁 修改的文件

| 文件 | 修改内容 |
|------|----------|
| `visualization-platform/index.html` | 新增"AI分析"导航标签；添加 AI 分析视图容器；实现情感分析函数；添加 ECharts 饼图渲染 |
| `api/server.py` | 新增 `/api/ai-analysis/latest` 和 `/api/ai-analysis/list` 端点 |

#### 🎨 界面布局

AI 分析界面采用与其他视图一致的设计风格：
- 顶部 4 个 KPI 卡片（带彩色顶部色条）
- 中间双列布局展示四大分析维度（趋势识别、值得关注的项目、学习路径、信号挖掘）
- 底部情感倾向分析环形饼图
- 支持暗色主题自动适配

#### 🚀 使用方式

1. 确保 Flask API 运行：`python api/server.py`
2. 确保 Vite 运行：`cd visualization-platform && npx vite --port 3000`
3. 打开 http://localhost:3000，点击顶部"AI分析"标签

### 第八次更新（2026-05-26）

**Streamlit 多源对比页优化 & 删除 Overlap 区块

#### 🐛 修复的问题

| 问题 | 修复内容 |
|------|----------|
| 多源对比页显示"需要 MongoDB 多源数据但实际有数据？ | [api_loader.py](file:///d:/download/8888888888888/hot-open-project-zgy/dashboard/data/api_loader.py#L80-L91) 改数据加载逻辑：从总是取最新集合改为取数据源最多的集合（如 `hotspot_2026_05_18` 有 github + arxiv + reddit + hn 4个源） |

#### 🗑️ 删除的内容

| 内容 | 说明 |
|------|----------|
| GitHub + Hacker News Overlap 区块 | [multi_source.py](file:///d:/download/8888888888888/hot-open-project-zgy/dashboard/views/multi_source.py#L90-L156) 中删除该区块，其他功能保留（KPI、全球 Top20、分布饼图、分布直方图、分布箱图 |

### 第九次更新（2026-05-27）

**ECharts 仪表盘功能修复 & AI 分析一键触发**

#### 🐛 Bug 修复

| 问题 | 修复内容 |
|------|----------|
| 洞察报告·语言热度分析图表数据错误 | `visualization-platform/index.html` 中 `renderInsightChart()` 原来聚合日/周/月三个周期的 `stars_since` 数据，改为只使用当前选中的时间范围；图表类型从水平柱状图改为饼图，与概览页语言分布保持一致 |

#### ✨ 新增功能

| 功能 | 说明 |
|------|------|
| AI分析"一键AI分析"按钮 | 在 `visualization-platform/index.html` AI分析视图标题旁新增按钮，点击后触发 `deepseek_analyzer.py` 分析并展示结果 |

#### 🔌 新增 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `POST /api/ai-analysis/run` | POST | 在 Flask 进程内直接导入并运行 `AI分析/deepseek_analyzer.py` 的 `run_analysis()` 函数，返回最新分析结果。需设置环境变量 `DEEPSEEK_API_KEY` |

#### 📁 修改的文件

| 文件 | 修改内容 |
|------|----------|
| `visualization-platform/index.html` | 洞察报告图表修复；新增"一键AI分析"按钮及 `setupAIRunButton()` 函数 |
| `api/server.py` | 新增 `POST /api/ai-analysis/run` 端点；启动参数添加 `use_reloader=False` 防止环境变量丢失 |
