import logging
import sqlite3
from scrapy.exceptions import DropItem

logger = logging.getLogger(__name__)


class DedupPipeline:
    """基于 url 字段的去重 Pipeline。"""

    def __init__(self, use_sqlite=False, sqlite_path="dedup.db"):
        self.use_sqlite = use_sqlite
        self.sqlite_path = sqlite_path
        self._memory_set = set()
        self._conn = None
        self.crawler = None

    @classmethod
    def from_crawler(cls, crawler):
        use_sqlite = crawler.settings.getbool("DEDUP_USE_SQLITE", False)
        sqlite_path = crawler.settings.get("DEDUP_SQLITE_PATH", "dedup.db")
        pipe = cls(use_sqlite=use_sqlite, sqlite_path=sqlite_path)
        pipe.crawler = crawler
        return pipe

    @property
    def _spider(self):
        return self.crawler.spider if self.crawler else None

    def open_spider(self):
        spider = self._spider
        if self.use_sqlite:
            self._conn = sqlite3.connect(self.sqlite_path)
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS seen_urls (url TEXT PRIMARY KEY)"
            )
            self._conn.commit()
            cursor = self._conn.execute("SELECT url FROM seen_urls")
            count = 0
            for row in cursor:
                self._memory_set.add(row[0])
                count += 1
            if spider:
                spider.logger.info(
                    f"DedupPipeline (SQLite): loaded {count} existing URLs from {self.sqlite_path}"
                )
        else:
            if spider:
                spider.logger.info("DedupPipeline (memory): initialized")

    def close_spider(self):
        if self._conn:
            self._conn.close()
            spider = self._spider
            if spider:
                spider.logger.info("DedupPipeline: SQLite connection closed")

    def process_item(self, item):
        spider = self._spider
        url = item.get("url")
        if url is None:
            if spider:
                spider.logger.warning("DedupPipeline: item missing 'url' field, dropping")
            raise DropItem("Missing url field")

        if url in self._memory_set:
            if spider:
                spider.logger.info(f"DedupPipeline: duplicate url '{url}', dropping")
            raise DropItem(f"Duplicate url: {url}")

        self._memory_set.add(url)
        if self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO seen_urls (url) VALUES (?)", (url,)
            )
            self._conn.commit()

        return item
