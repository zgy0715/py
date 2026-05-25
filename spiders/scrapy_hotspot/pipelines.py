import json
import logging
from datetime import datetime, timezone

import redis
from pymongo import MongoClient
from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)

# 各数据源的去重 Redis Set 键名
DEDUP_KEYS = {
    "github": "seen:github",
    "hn":     "seen:hn",
    "arxiv":  "seen:arxiv",
    "reddit": "seen:reddit",
}


class DeduplicationPipeline:
    """基于 Redis Set 的去重 Pipeline。

    每个数据源独立一个 Set（seen:<source>），以 unique_id 为成员。
    若 unique_id 已存在则 DropItem，否则 SADD 后放行。
    """

    def __init__(self, redis_host, redis_port):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self._r = None

    @classmethod
    def from_crawler(cls, crawler):
        host = crawler.settings.get("REDIS_HOST", "localhost")
        port = crawler.settings.getint("REDIS_PORT", 6379)
        return cls(host, port)

    def open_spider(self, spider):
        self._r = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True,
        )
        spider.logger.info("DeduplicationPipeline connected to Redis")

    def close_spider(self, spider):
        if self._r:
            self._r.close()

    def process_item(self, item, spider):
        source = item.get("source")
        unique_id = item.get("unique_id")
        if not source or not unique_id:
            spider.logger.warning("DeduplicationPipeline: missing source or unique_id, dropping")
            raise DropItem("Missing source or unique_id")

        # 有 range 字段时，去重 key 包含 range，确保 daily/weekly/monthly 独立
        base_key = DEDUP_KEYS.get(source, f"seen:{source}")
        range_val = item.get("range", "")
        key = f"{base_key}:{range_val}" if range_val else base_key
        added = self._r.sadd(key, unique_id)
        if not added:
            spider.logger.info(f"Dup skip [{source}:{range_val}] {unique_id}")
            raise DropItem(f"Duplicate {source}:{range_val}:{unique_id}")

        return item


class RedisHotScorePipeline:
    """将 Item 的热度分写入 Redis Sorted Set，维护实时排行榜。

    写入两个 ZSET:
      - hotspot:all         全局排行榜
      - hotspot:<source>    按来源分榜

    同时将 Item JSON 缓存到 Hash：item:<source>:<unique_id>
    """

    def __init__(self, redis_host, redis_port, zset_key, zset_ttl, item_prefix):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.zset_key = zset_key
        self.zset_ttl = zset_ttl
        self.item_prefix = item_prefix
        self._r = None

    @classmethod
    def from_crawler(cls, crawler):
        host = crawler.settings.get("REDIS_HOST", "localhost")
        port = crawler.settings.getint("REDIS_PORT", 6379)
        zset_key = crawler.settings.get("HOTSPOT_ZSET_KEY", "hotspot:all")
        zset_ttl = crawler.settings.getint("HOTSPOT_ZSET_TTL", 86400 * 7)
        item_prefix = crawler.settings.get("HOTSPOT_ITEM_PREFIX", "item:")
        return cls(host, port, zset_key, zset_ttl, item_prefix)

    def open_spider(self, spider):
        self._r = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True,
        )
        spider.logger.info("RedisHotScorePipeline connected to Redis")

    def close_spider(self, spider):
        if self._r:
            self._r.close()

    def process_item(self, item, spider):
        source = item.get("source", "unknown")
        unique_id = item.get("unique_id")
        hot_score = item.get("hot_score", 0)

        if not unique_id:
            spider.logger.warning("RedisHotScorePipeline: missing unique_id, skip")
            return item

        member = f"{source}:{unique_id}"
        source_zset = f"hotspot:{source}"

        # ZADD 是原子操作，多 worker 并发安全
        self._r.zadd(self.zset_key, {member: hot_score})
        self._r.zadd(source_zset, {member: hot_score})

        # 缓存 Item JSON
        item_hash_key = f"{self.item_prefix}{source}:{unique_id}"
        item_dict = dict(item)
        item_dict["crawl_time"] = datetime.now(timezone.utc).isoformat()
        self._r.hset(item_hash_key, mapping={"data": json.dumps(item_dict, ensure_ascii=False)})
        self._r.expire(item_hash_key, self.zset_ttl)

        spider.logger.debug(f"HotScore [{source}] {unique_id} -> {hot_score}")
        return item


class MongoDBPipeline:
    """将 Item 存入 MongoDB，集合按日期分片（如 hotspot_2026_05_17）。"""

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self._client = None
        self._db = None

    @classmethod
    def from_crawler(cls, crawler):
        uri = crawler.settings.get("MONGODB_URI", "mongodb://localhost:27017")
        db = crawler.settings.get("MONGODB_DATABASE", "tech_hotspot")
        return cls(uri, db)

    def open_spider(self, spider):
        self._client = MongoClient(self.mongo_uri)
        self._db = self._client[self.mongo_db]
        spider.logger.info(f"MongoDBPipeline connected to {self.mongo_uri} / {self.mongo_db}")

    def close_spider(self, spider):
        if self._client:
            self._client.close()

    def process_item(self, item, spider):
        collection_name = f"hotspot_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}"
        doc = dict(item)
        doc["crawl_time"] = datetime.now(timezone.utc).isoformat()
        self._db[collection_name].insert_one(doc)
        spider.logger.debug(f"MongoDB insert -> {collection_name}: {item.get('unique_id')}")
        return item
