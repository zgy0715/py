# AI分析 - DeepSeek 深度分析模块

本目录包含 GitHub Trending 项目的 DeepSeek AI 深度分析工具，独立于其他模块运行。

## 环境要求

**必须先启动以下服务：**

```bash
# 启动 MongoDB
mongod --dbpath /path/to/data
```

> 注：Redis 仅在运行爬虫时需要，AI 分析模块不需要 Redis。

## 目录结构

```
AI分析/
├── deepseek_analyzer.py   # DeepSeek AI 分析主程序
├── import_data.py         # CSV 数据导入工具（不使用爬虫时）
├── requirements.txt       # Python 依赖
├── output/                # 分析结果输出目录（自动创建）
│   └── insight_*.json     # JSON 格式分析结果
├── insight_analysis.log   # AI 分析日志（自动生成）
├── import_data.log        # 数据导入日志（自动生成）
└── README.md              # 本文件
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用说明

### 1. 数据准备

#### 方式一：运行爬虫（推荐）
```bash
cd ../spiders
scrapy crawl github_trending
```

#### 方式二：使用 import_data（不使用爬虫时）
将 CSV 文件放入 `data/` 目录，然后运行：
```bash
python import_data.py
```
这会将 CSV 数据导入 MongoDB，格式与爬虫一致。

### 2. 执行分析

```bash
# 设置 DeepSeek API Key（Windows PowerShell）
$env:DEEPSEEK_API_KEY="your-api-key"

# 或 Linux/Mac
export DEEPSEEK_API_KEY="your-api-key"

# 运行单次分析
python deepseek_analyzer.py
```

### 3. 定时任务（每12小时自动分析）

使用系统定时任务：

```bash
# Windows 任务计划程序
schtasks /create /sc hourly /mo 12 /tn "DeepSeek分析" /tr "python D:\path\to\AI分析\deepseek_analyzer.py"

# Linux crontab
0 */12 * * * cd /path/to/AI分析 && python deepseek_analyzer.py
```

## 分析结果

分析完成后，结果会：
1. 保存到 MongoDB `tech_hotspot.insights` 集合
2. 输出 JSON 文件到 `output/` 目录

### 输出格式

```json
{
  "趋势识别": [
    "Rust渗透进AI工具链，本周3个新项目涉及Rust+LLM推理",
    "AI Agent开发框架持续升温"
  ],
  "值得关注的项目": [
    "openhuman本周+4000 star，定位个人AI助手，建议试用"
  ],
  "学习路径": [
    "AI Agent方向持续火热，入行建议关注LangChain/LlamaIndex生态"
  ],
  "信号挖掘": [
    "GPU推理优化赛道活跃度上升，过去一周新增12个相关仓库"
  ],
  "metadata": {
    "projects_count": 100,
    "analyzed_at": "2026-05-25T...",
    "collection": "hotspot_2026_05_25",
    "model": "deepseek-v4-pro"
  }
}
```

## 日志文件

| 日志文件 | 记录器名称 | 说明 |
|----------|------------|------|
| `insight_analysis.log` | `insight_analyzer` | AI 分析主日志，记录完整分析流程 |
| `import_data.log` | `import_data` | 数据导入日志 |

**日志输出示例：**
```
2026-05-25 14:16:27,791 - insight_analyzer - INFO - 所有组件初始化成功
2026-05-25 14:16:27,791 - insight_analyzer - INFO - 开始运行分析...
2026-05-25 14:16:27,818 - insight_analyzer - INFO - 获取到 17 条数据
2026-05-25 14:16:27,818 - insight_analyzer - INFO - 步骤2: 构建分析prompt...
2026-05-25 14:16:42,072 - insight_analyzer - INFO - 洞察已保存，ID: 6a1297ca7440d878b47c7711
2026-05-25 14:16:42,172 - insight_analyzer - INFO - 分析完成!
2026-05-25 14:16:42,179 - insight_analyzer - INFO - 资源已清理
```

## API 服务（可选）

如果需要通过 HTTP API 调用分析功能，可以启动 Flask 服务：

```bash
cd ../api
python server.py
```

然后调用：
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"limit": 50, "save": true}'
```

## 配置文件

| 文件 | 说明 |
|------|------|
| `deepseek_analyzer.py` | MongoDB URI、DeepSeek API 配置在文件头部 |
| `import_data.py` | MongoDB 连接配置在文件头部 |

## 容错与重试机制

- 最多 3 次重试，每次间隔 10 秒
- HTTP 429（限流）自动等待 60 秒后重试
- 请求超时 120 秒，超时后重试
- JSON 解析失败时降级为正则表达式提取关键内容

## 注意事项

1. **必须启动 MongoDB** 才能运行分析程序
2. `import_data.py` 仅在**不使用爬虫时**用于手动导入 CSV 数据
3. 定时任务通过系统定时工具实现（crontab / schtasks）
4. API Key 通过环境变量 `DEEPSEEK_API_KEY` 管理，避免硬编码
