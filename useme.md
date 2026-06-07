# 使用方法

## 环境要求

- Python 3.7+
- MongoDB（默认 `localhost:27017`）
- Redis（默认 `localhost:6379`）
- GitHub 账户（可选，用于API认证）
- DeepSeek API Key（AI 分析功能，[获取地址](https://platform.deepseek.com/)）

## 安装依赖

```bash
# API 依赖（含 DeepSeek 分析所需）
pip install -r api/requirements.txt

# AI 分析依赖
pip install -r AI分析/requirements.txt

# 情感分析依赖
pip install requests textblob
```

> 💡 **提示**: TextBlob 是可选的，但推荐安装。它能提供更准确的英文情感分析。如果不安装，程序会自动使用关键词匹配法。

---

## 一、DeepSeek AI 深度分析

### 1.1 功能概述

DeepSeek AI 分析引擎基于 DeepSeek 大语言模型，对 GitHub Trending 等技术热点数据进行智能分析，自动输出四大维度的洞察：

| 维度 | 说明 |
| ---- | ---- |
| 趋势识别 | 识别 2-4 条技术趋势方向，结合增长数据提供量化支撑 |
| 值得关注的项目 | 精选 3-5 个高增长项目，含项目名、增长数据、定位与推荐理由 |
| 学习路径 | 提供 2-4 条方向性学习建议，附推荐技术栈 |
| 信号挖掘 | 发现 2-4 条隐藏信号，揭示潜在市场机会或技术转向 |

### 1.2 前置条件

**必须先启动 MongoDB：**

```bash
# Windows
mongod --dbpath C:\data\db

# Linux/Mac
mongod --dbpath /path/to/data
```

**确保 MongoDB 中已有数据（通过爬虫或导入工具写入）：**

```bash
# 方式一：运行爬虫采集数据
cd spiders
python run_hotspot.py

# 方式二：从 CSV 导入已有数据
cd AI分析 && python import_data.py
```

### 1.3 配置 DeepSeek API Key

通过环境变量设置 API Key（推荐）：

**Windows PowerShell:**
```powershell
$env:DEEPSEEK_API_KEY="sk-your-api-key"
```

**Linux/Mac:**
```bash
export DEEPSEEK_API_KEY="sk-your-api-key"
```

> ⚠️ **安全提示**：建议通过环境变量管理 API Key，避免硬编码在代码中。

### 1.4 运行方式

#### 方式一：AI分析 独立模块（推荐）

```bash
cd AI分析

# 安装依赖
pip install -r requirements.txt

# 设置 API Key（Windows PowerShell）
$env:DEEPSEEK_API_KEY="sk-your-api-key"

# 运行分析
python deepseek_analyzer.py

# 或导入 CSV 数据
python import_data.py
```

**执行流程：**
1. 连接 MongoDB，获取最新 hotspot 集合数据
2. 筛选 Top30 项目，构建分析 Prompt
3. 调用 DeepSeek API 进行分析
4. 解析返回结果，保存到 MongoDB insights 集合
5. 同时输出 JSON 文件到 `AI分析/output/` 目录
6. 日志自动记录到 `AI分析/insight_analysis.log`

**输出示例：**
```
============================================================
所有组件初始化成功
开始运行分析...
============================================================
步骤1: 获取数据...
获取到 100 条数据
步骤2: 构建分析prompt...
步骤3: 调用DeepSeek API进行深度分析...
DeepSeek API调用成功
步骤4: 添加元数据...
步骤5: 保存分析结果到MongoDB...
洞察已保存到insights集合
============================================================
分析完成!
============================================================
资源已清理

📊 分析结果预览:
----------------------------------------

【趋势识别】
  1. AI编码代理的"技能(Skills)"生态系统爆发
  2. Claude Code成为中心枢纽，带动周边工具井喷

【值得关注的项目】
  1. obra/superpowers (本周+38,379星): agentic技能框架
  2. rtk-ai/rtk (本周+21,036星): Rust CLI代理，降低LLM令牌消耗90%

【学习路径】
  1. AI Agent方向持续火热，建议深入学习LangChain、AutoGen、CrewAI
  2. Rust在AI推理领域崛起，推荐学习candle、llama.cpp

【信号挖掘】
  1. 免费/低成本AI编码工具需求强烈，相关项目本周共获超3万星
  2. 视频与演示文稿AI生成迎来爆发
```

#### 方式二：定时自动分析（每12小时）

在 `AI分析/` 目录下创建 `scheduler.py` 或使用系统定时任务：

```bash
# Windows 任务计划程序
schtasks /create /sc hourly /mo 12 /tn "DeepSeek分析" /tr "python D:\path\to\AI分析\deepseek_analyzer.py"

# Linux crontab
0 */12 * * * cd /path/to/AI分析 && python deepseek_analyzer.py
```

### 1.5 分析结果格式

```json
{
  "趋势识别": [
    "AI编码代理的"技能(Skills)"生态系统爆发",
    "Claude Code成为中心枢纽，带动周边工具井喷"
  ],
  "值得关注的项目": [
    "obra/superpowers (本周+38,379星，总195k): agentic技能框架与软件开发方法论",
    "rtk-ai/rtk (本周+21,036星，总49k): Rust实现的CLI代理，降低LLM令牌消耗90%"
  ],
  "学习路径": [
    "AI Agent方向持续火热，建议深入学习LangChain、AutoGen、CrewAI等多代理框架",
    "Rust在AI推理和工具链中崛起，推荐学习candle、tokenizers、llama.cpp绑定"
  ],
  "信号挖掘": [
    "免费/低成本AI编码工具需求强烈：相关项目本周共获超3万星",
    "视频与演示文稿AI生成迎来爆发，预示内容生产工具的下一个风口"
  ],
  "metadata": {
    "projects_count": 100,
    "analyzed_at": "2026-05-24T14:20:18.456014+00:00",
    "collection": "hotspot_2026_05_24",
    "model": "deepseek-v4-pro"
  }
}
```

### 1.6 性能参考

| 指标 | 数值 | 说明 |
| ---- | ---- | ---- |
| 单次分析项目数 | 50-100 | Prompt 注入 Top30 项目详情，其余仅统计 |
| API 响应时间 | 30-60s | 取决于 DeepSeek API 负载和输出长度 |
| Token 消耗 | ~4000 tokens/次 | max_tokens 设为 4000 |
| 重试上限 | 3 次 | 超过后返回错误 |
| 限流等待 | 60 秒 | HTTP 429 时自动等待 |

### 1.7 常见问题

#### Q1: DeepSeek API 调用失败怎么办？
**解决方案：**
1. 检查 API Key 是否正确设置（环境变量 `DEEPSEEK_API_KEY`）
2. 检查网络连接（API 地址：`https://api.deepseek.com`）
3. 查看日志文件 `AI分析/insight_analysis.log` 获取详细错误信息
4. 程序会自动重试 3 次，如仍失败请稍后再试

#### Q2: 分析结果为空或解析失败？
**解决方案：**
1. 检查 MongoDB 中是否有数据（`hotspot_*` 集合）
2. 可先用 `python AI分析/import_data.py` 导入 CSV 数据
3. JSON 解析失败时程序会自动降级为正则提取

#### Q3: API 限流（429 错误）？
**解决方案：**
1. 程序会自动等待 60 秒后重试
2. 减少调用频率，避免短时间内多次触发分析
3. 考虑升级 DeepSeek API 套餐

#### Q4: 定时任务如何调整分析频率？
**解决方案：**
修改系统定时任务的执行间隔，或在 `AI分析/` 目录下自行创建 `scheduler.py` 脚本。

---

## 二、GitHub 情感分析

### 2.1 配置 GitHub API（可选但推荐）

#### 为什么要配置？
- 未认证：每小时只能请求 60 次
- 已认证：每小时可以请求 5000 次
- 配置后分析速度更快，数据更完整

#### 配置步骤

##### 方法1：使用环境变量（推荐）

**Windows PowerShell:**
```powershell
$env:GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

**Linux/Mac:**
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

##### 方法2：在代码中添加

修改 `github_sentiment_analyzer.py` 文件，在以下函数中添加 headers 参数：

```python
def get_github_issues(owner, repo, max_pages=3):
    headers = {'Authorization': 'token YOUR_TOKEN_HERE'}  # 添加这一行

    for page in range(1, max_pages + 1):
        response = requests.get(f"{url}?page={page}&per_page=30",
                              headers=headers,  # 添加这个参数
                              timeout=15)

def get_issue_comments(owner, repo, issue_number):
    headers = {'Authorization': 'token YOUR_TOKEN_HERE'}  # 添加这一行

    response = requests.get(url, headers=headers, timeout=15)  # 添加这个参数

def get_user_info(username):
    headers = {'Authorization': 'token YOUR_TOKEN_HERE'}  # 添加这一行

    response = requests.get(url, headers=headers, timeout=15)  # 添加这个参数
```

### 2.2 运行程序

#### 1. 分析热门项目描述情感

```bash
python tools/github_sentiment_analyzer.py
```

**功能说明：**
- 读取 `github_trending_daily.csv`、`github_trending_weekly.csv`、`github_trending_monthly.csv`
- 分析每个项目的描述文本
- 将结果保存到 `sentiment_analysis_report.json`

**输出示例：**
```
GitHub Trending 舆情分析
============================================================
情感分析引擎: textblob

正在分析 github_trending_daily.csv...
  daily - 正面: 63 (26.9%), 中性: 165 (70.5%), 负面: 6 (2.6%)
```

#### 2. 分析仓库评论和用户信息

```bash
python tools/github_sentiment_analyzer.py
```

**功能说明：**
- 自动从 CSV 文件中读取项目 URL
- 获取每个仓库的 Issues 和评论
- 收集评论者的详细信息
- 跳过无公开评论的项目
- 生成详细的 JSON 分析报告

**输出示例：**
```
GitHub 仓库评论情感分析 (智能跳过无issues项目)
============================================================
情感分析引擎: textblob

============================================================
📊 分析 github_trending_daily.csv
============================================================

正在从 github_trending_daily.csv 寻找 3 个有公开issues的项目...
  🔍 尝试 #1: oven-sh/bun...
正在分析仓库: oven-sh/bun
  ✅ 成功 #1: oven-sh/bun (10 issues, 16 评论)

📄 报告已保存: github_trending_daily.csv_comments_analysis.json
```

### 2.3 查看分析结果

#### JSON 文件结构

运行后会生成以下文件：

| 文件名 | 内容 |
|--------|------|
| `sentiment_analysis_report.json` | 项目描述情感分析报告 |
| `github_trending_daily.csv_comments_analysis.json` | 日榜仓库评论分析 |
| `github_trending_weekly.csv_comments_analysis.json` | 周榜仓库评论分析 |
| `github_trending_monthly.csv_comments_analysis.json` | 月榜仓库评论分析 |

#### 查看特定仓库分析

在 JSON 文件中搜索仓库名，例如搜索 `oven-sh/bun`：

```json
{
  "repo": "oven-sh/bun",
  "issues_count": 10,
  "comments_count": 16,
  "issue_sentiments": [
    {
      "title": "Docs suggest HMR isn't supported",
      "sentiment": "positive",
      "score": 0.12,
      "user": "jakeg"
    }
  ],
  "comment_sentiments": [...],
  "users": {
    "jakeg": {
      "login": "jakeg",
      "name": "Jake Gordon",
      "company": null,
      "location": "Cambridge, UK",
      "followers": 51,
      "public_repos": 30
    }
  }
}
```

### 2.4 自定义配置

#### 修改分析项目数量

在 `github_sentiment_analyzer.py` 中修改：

```python
# 找到这行代码
target_count = 3

# 修改为想要的数量，例如分析前10个有评论的项目
target_count = 10
```

#### 自定义情感词典

在 `github_sentiment_analyzer.py` 中修改关键词：

```python
# 增加积极词汇
POSITIVE_WORDS_EN = {
    'great', 'excellent', 'awesome', 'amazing',
    'fantastic', 'wonderful', 'brilliant',
    # 添加你自己的词汇...
}

# 增加消极词汇
NEGATIVE_WORDS_EN = {
    'bad', 'terrible', 'awful', 'horrible',
    'worse', 'worst', 'problem', 'issue',
    # 添加你自己的词汇...
}
```

#### 修改分析的时间范围

如果想分析更多历史 Issues：

```python
# 找到这个函数，修改 max_pages 参数
def get_github_issues(owner, repo, max_pages=3):
    # 默认分析前 90 条 Issues
    # 如果想分析更多，改为更大的数字
    max_pages = 10  # 分析前 300 条
```

### 2.5 常见问题

#### Q1: 程序运行很慢怎么办？
**解决方案：**
1. 配置 GitHub Token 增加 API 配额
2. 减少要分析的项目数量（`target_count` 改小）

#### Q2: 很多项目被跳过，显示"无公开issues"？
**这是正常的。**
- 新项目可能还没有用户反馈
- 部分项目只有 PR，没有 Issues
- 程序会自动寻找下一个有评论的项目

#### Q3: TextBlob 分析结果不准确？
**解决方案：**
1. TextBlob 对技术文档和代码评论效果较差
2. 可以手动调整关键词词典
3. 对于中文评论，TextBlob 无法处理，程序会自动使用关键词匹配

#### Q4: 遇到 API 限流错误？
**解决方案：**
```python
# 在 requests 请求之间添加更长延迟
time.sleep(3)  # 原来是 1 秒，现在改为 3 秒
```

---

## 三、数据导入工具

### 3.1 CSV 数据导入 MongoDB

当不使用爬虫时，可通过 `import_data.py` 将 CSV 文件导入 MongoDB：

```bash
cd AI分析 && python import_data.py
```

**功能说明：**
- 自动读取 `data/` 目录下的 `github_trending_*.csv` 文件
- 将数据转换为与爬虫一致的 HotspotItem 格式
- 按 `hotspot_YYYY_MM_DD` 格式创建 MongoDB 集合
- 支持 daily/weekly/monthly 三种时间范围

---

## 四、完整工作流

### 推荐的日常使用流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 启动基础设施                                             │
│    ├── MongoDB: mongod --dbpath /path/to/data              │
│    └── Redis: redis-server                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 采集数据（二选一）                                        │
│    ├── 运行爬虫: python spiders/run_hotspot.py             │
│    └── 导入 CSV: python AI分析/import_data.py                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 启动核心服务                                             │
│    ├── Flask API: python api/server.py (port 5000)         │
│    ├── Streamlit: streamlit run dashboard/app.py (8501)    │
│    └── ECharts: cd visualization-platform && npx vite (3000)│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. 执行 AI 分析（按需选择）                                   │
│    ├── 手动单次: cd AI分析 && python deepseek_analyzer.py   │
│    └── 定时任务: 系统定时任务（如 crontab / 任务计划程序）    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. 查看结果                                                 │
│    ├── JSON 文件: AI分析/output/*.json                      │
│    ├── TXT 报告: AI分析/output/                              │
│    ├── Streamlit 看板: http://localhost:8501              │
│    └── ECharts 仪表盘: http://localhost:3000              │
└─────────────────────────────────────────────────────────────┘
```

### 启动脚本示例

**Windows PowerShell（一次性启动所有服务）：**

```powershell
# 启动 MongoDB（假设已安装并配置好环境变量）
Start-Process mongod -ArgumentList "--dbpath C:\data\db"

# 等待 MongoDB 启动
Start-Sleep -Seconds 3

# 启动 Flask API
Start-Process python -ArgumentList "api/server.py" -WorkingDirectory "d:\download\666666666\hot-open-project-zgy"

# 启动 Streamlit
Start-Process streamlit -ArgumentList "run dashboard/app.py --server.port=8501" -WorkingDirectory "d:\download\666666666\hot-open-project-zgy"

# 启动前端仪表盘
Start-Process npm -ArgumentList "run dev" -WorkingDirectory "d:\download\666666666\hot-open-project-zgy\visualization-platform"

Write-Host "所有服务已启动！"
Write-Host "API: http://localhost:5000"
Write-Host "Streamlit: http://localhost:8501"
Write-Host "ECharts: http://localhost:3000"
```

**Linux/Mac（使用 tmux 或 screen）：**

```bash
# 启动 MongoDB
mongod --dbpath /path/to/data &

# 等待启动
sleep 3

# 启动 Flask API
python api/server.py &

# 启动 Streamlit
streamlit run dashboard/app.py --server.port=8501 &

# 启动前端仪表盘
cd visualization-platform && npm run dev &

echo "所有服务已启动！"
echo "API: http://localhost:5000"
echo "Streamlit: http://localhost:8501"
echo "ECharts: http://localhost:3000"
```

---

## 最佳实践

### 开发环境配置

1. **环境变量管理**：建议使用 `.env` 文件管理敏感信息（API Key、数据库连接字符串等）
   ```bash
   # .env 文件示例
   DEEPSEEK_API_KEY=sk-your-api-key
   GITHUB_TOKEN=ghp-your-token
   MONGO_URI=mongodb://localhost:27017
   REDIS_URI=redis://localhost:6379
   ```

2. **虚拟环境**：使用 Python 虚拟环境隔离依赖
   ```bash
   python -m venv venv
   # Windows: venv\Scripts\activate
   # Linux/Mac: source venv/bin/activate
   ```

### 生产环境建议

3. **进程管理**：使用 `systemd`（Linux）或 `nssm`（Windows）管理服务进程
4. **日志管理**：配置日志轮转，避免日志文件过大
5. **安全设置**：
   - 不在代码中硬编码 API Key
   - 使用环境变量或密钥管理服务
   - 限制 API 端口的访问权限

### AI 分析优化

6. **分析频率**：建议每 12 小时分析一次，避免不必要的 API 调用
7. **性能优化**：
   - 减少 `limit` 参数可降低 Token 消耗和响应时间
   - 对于大规模数据分析，考虑分批处理
8. **结果缓存**：分析结果已自动保存到 MongoDB，避免重复分析相同数据

### 数据管理

9. **定期备份**：定期备份 MongoDB 数据和分析报告
10. **数据清理**：定期清理过期的热点数据集合（如保留最近 30 天）
11. **数据验证**：定期检查数据源的完整性和准确性

---

## 故障排除

### 常见问题及解决方案

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| API 返回 500 错误 | MongoDB 连接失败 | 检查 MongoDB 服务是否运行 |
| Streamlit 页面空白 | API 服务未启动 | 确保 Flask API 在端口 5000 运行 |
| AI 分析失败 | API Key 无效或过期 | 检查环境变量 `DEEPSEEK_API_KEY` |
| 爬虫无法运行 | Redis 连接失败 | 检查 Redis 服务是否运行 |
| 前端无法加载数据 | CORS 问题 | 确保 Flask API 的 CORS 配置正确 |

### 日志文件位置

- **DeepSeek 分析日志**：`AI分析/insight_analysis.log`
- **API 服务日志**：控制台输出（运行 `python api/server.py` 时）
- **爬虫日志**：`spiders/scrapy_hotspot/logs/`
- **分析结果**：`AI分析/output/`（JSON 和 TXT 格式）

### 调试命令

```bash
# 检查 MongoDB 连接
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017'); print('MongoDB 连接成功')"

# 检查 Redis 连接
python -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('Redis 连接成功')"

# 检查 API 服务状态
curl http://localhost:5000/api/system/status

# 检查可用的热点数据集合
curl http://localhost:5000/api/collections
```

---

## 技术支持

如果遇到问题：
1. 检查 Python 版本（需要 3.10+）
2. 确认已安装所有依赖（`pip install -r api/requirements.txt`）
3. 查看控制台输出的错误信息
4. 查看日志文件（`AI分析/insight_analysis.log`）
5. 确认 MongoDB 和 Redis 服务正常运行
6. 确认 DeepSeek API Key 有效（环境变量 `DEEPSEEK_API_KEY`）

---

💡 **提示**：建议先运行一次完整的分析，观察输出结果，再根据需要进行调整。如需获取最新的 AI 分析报告，运行 `cd AI分析 && python deepseek_analyzer.py` 即可。
