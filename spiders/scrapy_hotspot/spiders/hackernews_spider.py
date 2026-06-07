import re

import scrapy

from scrapy_hotspot.items import HotspotItem
from scrapy_hotspot.spiders.base_spider import BaseHotspotSpider


class HackerNewsSpider(BaseHotspotSpider):
    """抓取 Hacker News 首页前 3 页。hot_score = score + comments * 2"""

    name = "hackernews"
    redis_key = "hn:start_urls"
    item_source = "hn"

    def parse(self, response):
        rows = response.css("tr.athing")
        self.logger.info(f"Parsing {response.url} — {len(rows)} stories")

        for row in rows:
            try:
                item = self._parse_row(row)
                if item:
                    yield item
            except Exception as exc:
                self.logger.error(f"Error parsing HN row: {exc}")

    def _parse_row(self, row) -> HotspotItem | None:
        post_id = row.xpath("@id").get()
        if not post_id:
            return None

        title_sel = row.css("span.titleline a")
        title = title_sel.css("::text").get()
        link = title_sel.attrib.get("href", "") if title_sel else ""

        if not title:
            return None

        subtext = row.xpath("following-sibling::tr[1]/td[@class='subtext']")
        score_text = subtext.css("span.score::text").get()
        score = 0
        if score_text:
            m = re.search(r"(\d+)", score_text)
            if m:
                score = int(m.group(1))

        comments = 0
        comment_link = subtext.css("a:contains('comment')::text").get()
        if comment_link:
            m = re.search(r"(\d+)", comment_link)
            if m:
                comments = int(m.group(1))

        hot_score = score + comments * 2

        url = link or ""
        if url.startswith("item?"):
            url = f"https://news.ycombinator.com/{url}"

        return self.make_item(
            unique_id=post_id,
            title=title.strip(),
            url=url,
            score=score,
            comments=comments,
            hot_score=hot_score,
            extra={"post_id": post_id},
        )
