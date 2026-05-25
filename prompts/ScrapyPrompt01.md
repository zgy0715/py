我需要你为我生成一个基于 Scrapy 框架的爬虫项目，用于实时抓取 GitHub 上 AI 相关的热门开源项目信息。请严格按照以下要求生成完整的、可直接运行的代码。

## 项目目标
构建一个 Scrapy 爬虫，从 GitHub Trending 页面 (https://github.com/trending) 定时抓取热门项目数据，自动筛选出与人工智能/机器学习密切相关的项目，为趋势分析提供原始数据。要求抓取日榜、周榜、月榜，支持分页和去重，最终输出结构化 CSV 文件。

## 详细需求

### 1. 抓取源与规则
- **数据源**：`https://github.com/trending`，通过 URL 参数 `since` 切换榜单周期：`daily`, `weekly`, `monthly`。
- **分页**：Trending 页面有分页，需要抓取前 N 页（可通过参数 `pages` 配置，默认抓取前 3 页）。每页约 25 个项目。
- **过滤逻辑**：只保留 AI 相关项目，满足以下任一条件即视为 AI 项目：
  - 项目的话题标签 (`topics`) 中包含关键词列表中的任意一个（不区分大小写），默认关键词列表：`['ai', 'machine-learning', 'deep-learning', 'artificial-intelligence', 'llm', 'gpt', 'generative-ai', 'neural-network', 'transformer', 'pytorch', 'tensorflow', 'nlp', 'computer-vision', 'reinforcement-learning', 'ml', 'data-science', 'chatgpt', 'langchain', 'stable-diffusion']`。
  - 如果 topics 为空或未匹配，则进一步检查项目描述和名称，是否包含上述关键词或 `'AI', 'ML', 'machine learning', 'deep learning', 'LLM'` 等扩展词（不区分大小写）。
  - 关键词列表需在 settings.py 或 Spider 类变量中集中管理，并支持通过命令行 `-a filter_keywords` 参数动态覆盖。
- **提取字段** (对应 Scrapy Item)：
  - `rank`：趋势排名（全局序号，从 1 开始跨页累加）
  - `name`：项目全名 (格式 "owner/repo")
  - `owner`：作者/组织名
  - `description`：项目描述
  - `language`：主要编程语言
  - `stars`：总星数 (整数)
  - `stars_since`：本周期新增星数 (日榜为 today，周榜为 this week，月榜为 this month)
  - `forks`：Fork 数 (整数)
  - `topics`：话题标签列表 (List[str])
  - `url`：项目链接 (https://github.com/owner/repo)
  - `crawl_time`：抓取时间戳 (ISO 8601 格式)
  - `since`：榜单周期 (daily/weekly/monthly)
  - `page`：来源页码

### 2. 技术实现要求
- **框架**：Scrapy 2.11+，Python 3.9+
- **爬虫类**：继承 `scrapy.Spider`，名称为 `github_trending_ai`
- **请求与解析**：
  - 起始 URL 根据参数构造：`https://github.com/trending?since={since}`
  - 使用 XPath 或 CSS 选择器解析列表页的 `<article class="Box-row">` 节点。
  - 排名利用循环索引 + 页码偏移计算。
  - 提取 owner/repo：从 `h2 a` 的 `href` 属性中分离。
  - 提取描述：`p` 元素的文本（注意可能缺失）。
  - 提取语言：`span[itemprop="programmingLanguage"]` 或带有语言样式的 span。
  - 提取 stars/forks：定位 `a[href*='/stargazers']` 和 `a[href*='/forks']` 中的数字文本，处理带 "k" 的缩写（如 1.2k 转为 1200）。
  - 提取周期新增星数：包含 "stars today" 或类似文本的 `span`，用正则提取数字。
  - 提取 topics：当前项目下所有 `a.topic-tag` 的文本。
  - 生成完整 URL。
  - **过滤**：在解析每个项目时立即应用过滤条件，不符合则跳过，不产出 Item。
- **反爬与合规**：
  - `ROBOTSTXT_OBEY = True`
  - 开启 `AutoThrottle`，目标下载延迟 3~6 秒，根据响应时间自动调节。
  - User-Agent 轮换：使用 `scrapy-fake-useragent` 中间件，或自定义中间件随机选择常用桌面浏览器 UA。
  - 设置默认请求头 `Accept-Language: en-US,en;q=0.9`，模拟真实浏览。
  - 重试中间件：`RETRY_TIMES = 3`，重试 500/502/503/504/408 状态码。
  - 代理支持（非强制）：通过 `HTTP_PROXY` 环境变量或 settings 中的 `PROXY_POOL` 可配置，预留中间件接口。
- **数据处理与存储**：
  - 每轮运行生成一个 CSV 文件，命名格式：`github_trending_ai_YYYYMMDD_HHMMSS.csv`，使用 Scrapy 的 CsvItemExporter 或 Feed 导出。
  - **去重 Pipeline**：基于 `url` 字段去重。同一轮运行内如果出现重复 url（极少数情况），只保留第一条。去重集可使用内存 Set，或使用 sqlite 数据库文件持久化，避免程序重启导致重复。Pipeline 中需确保处理后的 Item 才进入导出。
  - 提供可选 MongoDB/JSON Lines Pipeline（代码中以注释形式保留），方便扩展。
- **异常处理**：解析过程中如任何字段缺失或转换失败，记录 Warning 日志并赋予 None，不得中断整个爬虫。

### 3. 项目代码结构
请生成标准 Scrapy 项目，包含以下文件并附详细注释（英文或中文均可）：
scrapy.cfg  
github_trending/  
├── **init**.py  
├── items.py  
├── middlewares.py  
├── pipelines.py  
├── settings.py  
└── spiders/  
├── **init**.py  
└── github_trending_spider.py  
run_spider.py # 独立运行脚本，便于直接执行和传参  
requirements.txt # 依赖列表  
README.md # 使用说明

- **Spider 参数**：支持 `-a since=daily -a pages=3 -a filter_keywords=ai,llm,ml` 形式传入。
- **run_spider.py**：使用 `scrapy crawl` 命令封装，可从命令行接收参数或直接运行，并打印运行命令示例。
- **README.md**：包含环境安装步骤、依赖安装命令、运行示例、输出文件说明。

### 4. 关键代码规范
- 所有数字字段使用正则提取数字部分，处理 "k"/"K" 缩写。
- 使用 `datetime.now(timezone.utc).isoformat()` 生成 `crawl_time`。
- 过滤关键词匹配使用 `any(keyword in text.lower() for keyword in keywords)` 方式。
- 日志记录：解析跳过时用 `self.logger.info`，错误用 `self.logger.error`。
- 确保导出 CSV 时字段顺序与 Item 定义一致，使用 `FEED_EXPORT_FIELDS` 显式指定。

### 5. 输出示例
请在 README 中提供一段预期的 CSV 输出示例（表头 + 2 行数据），例如：
rank,name,owner,description,language,stars,stars_since,forks,topics,url,crawl_time,since,page  
1,openai/gpt-4,openai,"GPT-4 code interpreter...",Python,34500,1200,4500,"['ai','llm']",[https://github.com/openai/gpt-4,2026-05-16T08:30:00+00:00,daily,1](https://github.com/openai/gpt-4,2026-05-16T08:30:00+00:00,daily,1)

请确保所有代码可以直接复制运行，并针对选择器的稳定性和反爬策略给出最佳实践。生成完整的代码解决方案。