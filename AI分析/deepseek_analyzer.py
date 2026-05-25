"""
GitHub Trending 项目 DeepSeek AI 深度分析
从MongoDB读取数据，使用DeepSeek API进行深度分析，挖掘流行项目趋势和洞察
输出格式：趋势识别、值得关注的项目、学习路径、信号挖掘
"""
import os
import json
import logging
from datetime import datetime, timezone
from pymongo import MongoClient
import requests
import time
import re

# ===================== 配置 =====================
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "tech_hotspot"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-v4-pro"

LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, "insight_analysis.log")

# 创建日志记录器
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("insight_analyzer")


class MongoDBConnector:
    """MongoDB连接器"""

    def __init__(self, uri=MONGO_URI, db_name=DB_NAME):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        logger.info(f"MongoDB连接成功: {uri}/{db_name}")

    def get_collections(self):
        """获取所有hotspot集合"""
        colls = [c for c in self.db.list_collection_names() if c.startswith("hotspot_")]
        colls.sort(reverse=True)
        return colls

    def get_latest_collection(self):
        """获取最新的hotspot集合"""
        colls = self.get_collections()
        return colls[0] if colls else None

    def fetch_github_trending(self, collection_name=None, limit=100, source="github"):
        """
        从MongoDB获取GitHub trending数据

        Args:
            collection_name: 集合名称，默认最新
            limit: 返回条数
            source: 数据源，默认github

        Returns:
            list: 项目列表
        """
        if not collection_name:
            collection_name = self.get_latest_collection()

        if not collection_name:
            logger.warning("没有找到hotspot集合")
            return []

        logger.info(f"从集合 {collection_name} 获取 {source} 数据，限制 {limit} 条")

        cursor = self.db[collection_name].find(
            {"source": source}
        ).sort("stars_since", -1).limit(limit)

        projects = []
        for doc in cursor:
            projects.append({
                "name": doc.get("unique_id", ""),
                "owner": doc.get("author", ""),
                "description": doc.get("description", ""),
                "language": doc.get("language", ""),
                "stars": doc.get("stars", 0),
                "stars_since": doc.get("stars_since", 0),
                "forks": doc.get("forks", 0),
                "topics": doc.get("topics", []),
                "url": doc.get("url", ""),
                "hot_score": doc.get("hot_score", 0),
                "published_at": doc.get("published_at"),
                "crawl_time": doc.get("crawl_time"),
            })

        logger.info(f"获取到 {len(projects)} 条数据")
        return projects

    def save_insight(self, insight_data):
        """
        保存洞察结果到MongoDB insights集合

        Args:
            insight_data: 洞察数据字典

        Returns:
            ObjectId: 插入的文档ID
        """
        result = insight_data.copy()
        result["created_at"] = datetime.now(timezone.utc)

        insert_result = self.db["insights"].insert_one(result)
        logger.info(f"洞察已保存到insights集合，ID: {insert_result.inserted_id}")
        return insert_result.inserted_id

    def close(self):
        """关闭连接"""
        self.client.close()
        logger.info("MongoDB连接已关闭")


class DeepSeekAnalyzer:
    """DeepSeek API 分析器"""

    def __init__(self, api_key=DEEPSEEK_API_KEY, model=DEEPSEEK_MODEL):
        self.api_key = api_key
        self.model = model
        self.api_url = DEEPSEEK_API_URL

        if not self.api_key:
            logger.warning("未设置DEEPSEEK_API_KEY环境变量")

    def analyze_projects(self, projects, max_retries=3):
        """
        使用DeepSeek API分析项目列表

        Args:
            projects: 项目列表
            max_retries: 最大重试次数

        Returns:
            dict: 分析结果，包含趋势识别、值得关注的项目、学习路径、信号挖掘
        """
        if not self.api_key:
            logger.error("DeepSeek API密钥未设置")
            return None

        prompt = self._build_analysis_prompt(projects)

        for attempt in range(max_retries):
            try:
                logger.info(f"调用DeepSeek API (尝试 {attempt + 1}/{max_retries})...")

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }

                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": """你是一位专业的技术趋势分析师，专注于开源项目和AI技术领域。
你的职责是对GitHub热门项目进行深度分析，挖掘技术趋势和洞察。
你必须严格按照指定的JSON格式输出分析结果，用中文回答。"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4000
                }

                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=120
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    logger.info("DeepSeek API调用成功")
                    return self._parse_analysis_result(content, projects)
                elif response.status_code == 429:
                    logger.warning("API限流，等待60秒后重试...")
                    time.sleep(60)
                else:
                    logger.error(f"API调用失败: {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(10)

            except requests.exceptions.Timeout:
                logger.warning("API请求超时")
                if attempt < max_retries - 1:
                    time.sleep(10)
            except Exception as e:
                logger.error(f"分析过程出错: {e}")
                if attempt < max_retries - 1:
                    time.sleep(10)

        logger.error("DeepSeek API调用失败")
        return None

    def _build_analysis_prompt(self, projects):
        """构建分析prompt"""
        top_projects = sorted(projects, key=lambda x: x.get("stars_since", 0), reverse=True)[:30]

        projects_summary = []
        for i, p in enumerate(top_projects, 1):
            desc = p.get("description", "")[:200]
            topics = ", ".join(p.get("topics", [])[:5]) if p.get("topics") else "无"
            projects_summary.append(
                f"{i}. {p['name']} (stars: {p['stars']:,} | +{p['stars_since']:,} this week)\n"
                f"   Language: {p.get('language', 'Unknown')} | Forks: {p.get('forks', 0):,}\n"
                f"   Description: {desc}\n"
                f"   Topics: {topics}"
            )

        projects_text = "\n\n".join(projects_summary)

        prompt = f"""## GitHub Trending Projects Analysis Task

### Data Overview
- Total projects analyzed: {len(projects)}
- Data timestamp: {projects[0].get('crawl_time', 'Unknown') if projects else 'Unknown'}

### Top 30 Trending Projects
{projects_text}

### Analysis Requirements
Please analyze the above projects and output results in the following JSON format:

```json
{{
  "趋势识别": [
    "Rust渗透进AI工具链，本周3个新项目涉及Rust+LLM推理",
    "AI Agent开发框架持续升温，多款新工具涌现"
  ],
  "值得关注的项目": [
    "openhuman本周+4000 star，定位个人AI助手，建议试用",
    "CLI-Anything将所有软件Agent化，创新性强"
  ],
  "学习路径": [
    "AI Agent方向持续火热，入行建议关注LangChain/LlamaIndex生态",
    "Rust在AI推理领域崛起，建议学习candle/llama.cpp"
  ],
  "信号挖掘": [
    "GPU推理优化赛道活跃度上升，过去一周新增12个相关仓库",
    "隐私优先的本地AI方案需求增长明显"
  ]
}}
```

### Output Guidelines:
1. **趋势识别**: Identify 2-4 major technology trends from the projects. Each trend should be concise (one sentence), describing the trend direction and supporting data.

2. **值得关注的项目**: Recommend 3-5 projects worth following. Each recommendation should include: project name, growth data, core positioning, and why it's worth attention.

3. **学习路径**: Provide 2-4 learning path recommendations for developers. Each should include: direction description, recommended tech stack/ecosystem.

4. **信号挖掘**: Discover 2-4 hidden signals from the data. Each signal should include: signal description and supporting data.

Please ensure:
- Output valid JSON format only
- Use Chinese for all content
- Be specific and data-driven
- Focus on actionable insights"""

        return prompt

    def _parse_analysis_result(self, content, projects):
        """
        解析DeepSeek返回的分析结果，提取四个核心字段

        Args:
            content: API返回的原始内容
            projects: 原始项目列表（用于补充统计信息）

        Returns:
            dict: 结构化的分析结果
        """
        result = {
            "趋势识别": [],
            "值得关注的项目": [],
            "学习路径": [],
            "信号挖掘": [],
            "metadata": {
                "projects_count": len(projects),
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
        }

        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)

                for key in ["趋势识别", "值得关注的项目", "学习路径", "信号挖掘"]:
                    if key in parsed and isinstance(parsed[key], list):
                        result[key] = parsed[key]

                logger.info("成功解析JSON格式分析结果")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败: {e}，尝试文本提取")

        for key in ["趋势识别", "值得关注的项目", "学习路径", "信号挖掘"]:
            pattern = rf'["\']?{key}["\']?\s*[:：]\s*\[(.*?)\]'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                items_text = match.group(1)
                items = re.findall(r'["\']([^"\']+)["\']', items_text)
                result[key] = items

        if not any(result.values()):
            result["趋势识别"] = ["无法解析API返回结果，请查看原始分析"]
            result["raw_content"] = content

        return result


def save_to_json(result, filename=None):
    """保存结果到JSON文件"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(LOG_DIR, "output")
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"insight_{timestamp}.json")

    serializable_result = {}
    for key, value in result.items():
        if hasattr(value, "__str__") and "ObjectId" in str(type(value)):
            serializable_result[key] = str(value)
        elif isinstance(value, datetime):
            serializable_result[key] = value.isoformat()
        elif isinstance(value, list):
            serializable_result[key] = [
                str(v) if hasattr(v, "__str__") and "ObjectId" in str(type(v)) else v
                for v in value
            ]
        else:
            serializable_result[key] = value

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(serializable_result, f, ensure_ascii=False, indent=2)

    logger.info(f"JSON文件已保存: {filename}")
    return filename


def run_analysis():
    """运行完整分析流程"""
    logger.info("=" * 60)
    logger.info("所有组件初始化成功")
    logger.info("开始运行分析...")
    logger.info("=" * 60)

    mongo = MongoDBConnector()
    analyzer = DeepSeekAnalyzer()

    try:
        logger.info("步骤1: 获取数据...")
        projects = mongo.fetch_github_trending(limit=100)

        if not projects:
            logger.warning("没有获取到任何数据")
            return

        logger.info(f"获取到 {len(projects)} 条数据")

        logger.info("步骤2: 构建分析prompt...")
        logger.info("步骤3: 调用DeepSeek API进行深度分析...")
        insight_result = analyzer.analyze_projects(projects)

        if not insight_result:
            logger.error("分析失败")
            return

        logger.info("步骤4: 添加元数据...")
        insight_result["metadata"]["collection"] = mongo.get_latest_collection()
        insight_result["metadata"]["model"] = DEEPSEEK_MODEL

        logger.info("步骤5: 保存分析结果到MongoDB...")
        mongo.save_insight(insight_result)

        save_to_json(insight_result)

        logger.info("=" * 60)
        logger.info("分析完成!")
        logger.info("=" * 60)

        print("\n[分析结果预览]")
        print("-" * 40)
        for key in ["趋势识别", "值得关注的项目", "学习路径", "信号挖掘"]:
            print(f"\n[{key}]")
            items = insight_result.get(key, [])
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item}")

        return insight_result

    except Exception as e:
        logger.error(f"分析过程出错: {e}")
        raise
    finally:
        mongo.close()
        logger.info("资源已清理")


if __name__ == "__main__":
    run_analysis()
