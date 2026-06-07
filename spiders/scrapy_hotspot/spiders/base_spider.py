"""所有热点爬虫的基类，消除 make_request_from_data 重复代码。"""

from datetime import datetime, timezone

import scrapy
from scrapy_redis.spiders import RedisSpider

from scrapy_hotspot.items import HotspotItem


class BaseHotspotSpider(RedisSpider):
    """统一处理 Redis 数据读取，子类只需实现 parse 和定义 redis_key / name / item_source。"""

    # 子类必须覆盖
    item_source: str = ""
    # 可选：子类可覆盖，加入自定义请求头
    request_headers: dict | None = None

    def make_request_from_data(self, data):
        if isinstance(data, bytes):
            url = data.decode("utf-8")
        elif isinstance(data, str):
            url = data
        else:
            self.logger.error(f"Unexpected data type: {type(data)}")
            return None
        url = url.strip()
        if not url:
            self.logger.warning("make_request_from_data: empty URL, returning None")
            return None
        kwargs = {"callback": self.parse, "dont_filter": True}
        if self.request_headers:
            kwargs["headers"] = self.request_headers
        return scrapy.Request(url, **kwargs)

    def make_item(self, **kwargs) -> HotspotItem:
        """创建 Item，自动填入 source 和 crawl_time。"""
        kwargs.setdefault("source", self.item_source)
        kwargs.setdefault("crawl_time", datetime.now(timezone.utc).isoformat())
        return HotspotItem(**kwargs)
