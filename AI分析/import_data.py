"""
CSV数据导入MongoDB程序
从data目录读取CSV文件，按照爬虫数据格式写入MongoDB
"""
import os
import csv
import logging
from datetime import datetime, timezone
from pymongo import MongoClient
import re

# ===================== 配置 =====================
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "tech_hotspot"

# CSV文件目录
PUBLIC_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data"
)

LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, "import_data.log")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("import_data")


def parse_number(text):
    """从文本中提取数字，处理 'k'/'K' 缩写"""
    if not text:
        return None
    text = text.strip().lower().replace(",", "")
    m = re.search(r"([\d.]+)\s*(k)?", text)
    if not m:
        return None
    num = float(m.group(1))
    if m.group(2) == "k":
        return int(num * 1000)
    return int(num)


def parse_topics(topics_str):
    """解析topics字段，支持逗号分隔或JSON格式"""
    if not topics_str or topics_str.strip() == "":
        return []

    import json
    try:
        topics = json.loads(topics_str)
        if isinstance(topics, list):
            return [t.strip() for t in topics if t.strip()]
    except:
        pass

    return [t.strip() for t in topics_str.split(",") if t.strip()]


class CSVToMongoImporter:
    """CSV到MongoDB导入器"""

    def __init__(self, mongo_uri=MONGO_URI, db_name=DB_NAME):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        logger.info(f"MongoDB连接成功: {mongo_uri}/{db_name}")

    def get_collection_name(self, date=None):
        """获取集合名称，格式为 hotspot_YYYY_MM_DD"""
        if not date:
            date = datetime.now(timezone.utc)
        return f"hotspot_{date.strftime('%Y_%m_%d')}"

    def import_csv_file(self, csv_path, collection_name=None, override_date=None):
        """
        导入单个CSV文件

        Args:
            csv_path: CSV文件路径
            collection_name: 目标集合名称（可选）
            override_date: 覆盖日期（可选，用于构造集合名）

        Returns:
            int: 导入的项目数量
        """
        if not os.path.exists(csv_path):
            logger.error(f"文件不存在: {csv_path}")
            return 0

        if not collection_name:
            if override_date:
                collection_name = self.get_collection_name(override_date)
            else:
                collection_name = self.get_collection_name()

        logger.info(f"开始导入: {csv_path} -> {collection_name}")

        # 判断文件类型（daily/weekly/monthly）
        filename = os.path.basename(csv_path)
        if "daily" in filename.lower():
            range_val = "daily"
        elif "weekly" in filename.lower():
            range_val = "weekly"
        elif "monthly" in filename.lower():
            range_val = "monthly"
        else:
            range_val = "daily"

        items = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    item = self._convert_row_to_item(row, range_val)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.error(f"解析行出错: {e}")

        if items:
            result = self.db[collection_name].insert_many(items)
            logger.info(f"成功插入 {len(result.inserted_ids)} 条记录到 {collection_name}")
            return len(result.inserted_ids)
        else:
            logger.warning("没有有效数据可导入")
            return 0

    def _convert_row_to_item(self, row, range_val="daily"):
        """
        将CSV行转换为与爬虫一致的HotspotItem格式

        Args:
            row: CSV行数据（dict）
            range_val: 时间范围（daily/weekly/monthly）

        Returns:
            dict: 转换后的项目
        """
        name = row.get("name", "")
        owner = row.get("owner", "")

        # 生成unique_id
        if "/" in name:
            unique_id = name
        else:
            unique_id = f"{owner}/{name}"

        # 解析数字
        stars = parse_number(str(row.get("stars", "0"))) or 0
        stars_since = parse_number(str(row.get("stars_since", "0"))) or 0
        forks = parse_number(str(row.get("forks", "0"))) or 0

        # 解析topics
        topics = parse_topics(row.get("topics", ""))

        # 计算hot_score（与爬虫保持一致: stars_since * 10 + forks * 5）
        hot_score = stars_since * 10 + forks * 5

        # 处理crawl_time
        crawl_time = row.get("crawl_time", "")
        if not crawl_time:
            crawl_time = datetime.now(timezone.utc).isoformat()

        # 处理published_at（如果有的话）
        published_at = row.get("published_at", None)

        # 构建与爬虫一致的item格式
        item = {
            "source": "github",
            "unique_id": unique_id,
            "title": unique_id,
            "url": row.get("url", f"https://github.com/{unique_id}"),
            "description": row.get("description", ""),
            "author": owner,
            "language": row.get("language", ""),
            "score": stars_since,
            "comments": 0,
            "stars": stars,
            "stars_since": stars_since,
            "forks": forks,
            "topics": topics,
            "hot_score": hot_score,
            "range": range_val,
            "published_at": published_at,
            "crawl_time": crawl_time,
            "extra": {
                "rank": row.get("rank", ""),
                "page": row.get("page", "all")
            }
        }

        return item

    def import_all_csv_files(self, public_dir=PUBLIC_DATA_DIR, collection_name=None):
        """
        导入public目录下所有CSV文件

        Args:
            public_dir: CSV文件目录
            collection_name: 目标集合名称（可选）

        Returns:
            dict: 各文件导入数量统计
        """
        if not os.path.exists(public_dir):
            logger.error(f"目录不存在: {public_dir}")
            return {}

        csv_files = [
            f for f in os.listdir(public_dir)
            if f.endswith(".csv") and "github_trending" in f
        ]

        if not csv_files:
            logger.warning(f"未找到CSV文件: {public_dir}")
            return {}

        logger.info(f"找到 {len(csv_files)} 个CSV文件")

        stats = {}
        for csv_file in csv_files:
            csv_path = os.path.join(public_dir, csv_file)
            count = self.import_csv_file(csv_path, collection_name)
            stats[csv_file] = count

        return stats

    def get_collection_names(self):
        """获取所有hotspot集合"""
        colls = [c for c in self.db.list_collection_names() if c.startswith("hotspot_")]
        colls.sort(reverse=True)
        return colls

    def close(self):
        """关闭连接"""
        self.client.close()
        logger.info("MongoDB连接已关闭")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("CSV数据导入MongoDB程序启动")
    logger.info("=" * 60)

    importer = CSVToMongoImporter()

    try:
        logger.info(f"数据目录: {PUBLIC_DATA_DIR}")
        if not os.path.exists(PUBLIC_DATA_DIR):
            logger.error(f"目录不存在: {PUBLIC_DATA_DIR}")
            return

        stats = importer.import_all_csv_files()

        logger.info("=" * 60)
        logger.info("导入完成!")
        for filename, count in stats.items():
            logger.info(f"  {filename}: {count} 条")
        total = sum(stats.values())
        logger.info(f"总计: {total} 条")

        collections = importer.get_collection_names()
        if collections:
            logger.info(f"现有集合: {', '.join(collections)}")

    except Exception as e:
        logger.error(f"导入过程出错: {e}")
        raise
    finally:
        importer.close()


if __name__ == "__main__":
    main()
