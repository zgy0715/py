import json
from datetime import datetime, timezone

import scrapy

from scrapy_hotspot.items import HotspotItem
from scrapy_hotspot.spiders.base_spider import BaseHotspotSpider


class RedditSpider(BaseHotspotSpider):
    """抓取 Reddit r/MachineLearning 热门帖子（JSON API），支持翻页。hot_score = score + comments"""

    name = "reddit"
    redis_key = "reddit:start_urls"
    item_source = "reddit"
    request_headers = {"Accept": "application/json"}
    max_pages = 3  # 最多翻 3 页，每页约 50 条

    def parse(self, response):
        try:
            body = json.loads(response.text)
        except json.JSONDecodeError as exc:
            self.logger.error(f"JSON decode failed for {response.url}: {exc}")
            return

        data = body.get("data", {})
        children = data.get("children", [])
        after = data.get("after")

        self.logger.info(f"Parsing {response.url} — {len(children)} posts, after={after}")

        for child in children:
            try:
                post = child.get("data", {})
                item = self._parse_post(post)
                if item:
                    yield item
            except Exception as exc:
                self.logger.error(f"Error parsing Reddit post: {exc}")

        # 翻页：如果有 after token 且未达到最大页数，继续抓下一页
        page = response.meta.get("page", 1)
        if after and page < self.max_pages:
            next_url = f"https://www.reddit.com/r/MachineLearning/hot.json?limit=50&after={after}"
            yield scrapy.Request(
                next_url,
                callback=self.parse,
                dont_filter=True,
                headers=self.request_headers,
                meta={"page": page + 1},
            )

    def _parse_post(self, post: dict) -> HotspotItem | None:
        post_id = post.get("name")
        title = post.get("title")
        if not post_id or not title:
            return None

        score = post.get("score", 0)
        num_comments = post.get("num_comments", 0)
        created_utc = post.get("created_utc")
        published_at = None
        if created_utc:
            published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()

        return self.make_item(
            unique_id=post_id,
            title=title,
            url=post.get("url", ""),
            description=(post.get("selftext", "") or "")[:200] or None,
            author=post.get("author"),
            score=score,
            comments=num_comments,
            hot_score=score + num_comments,
            published_at=published_at,
            extra={"subreddit": post.get("subreddit"), "post_id": post_id},
        )
