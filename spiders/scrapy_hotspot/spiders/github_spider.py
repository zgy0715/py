import re
from datetime import datetime, timezone

from scrapy_hotspot.items import HotspotItem
from scrapy_hotspot.spiders.base_spider import BaseHotspotSpider


def _parse_number(text: str | None) -> int | None:
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


class GitHubTrendingSpider(BaseHotspotSpider):
    """抓取 GitHub Trending 每日排行榜。hot_score = stars_since * 10 + forks_since * 5"""

    name = "github_trending"
    redis_key = "github:start_urls"
    item_source = "github"

    def parse(self, response):
        range_val = "daily"
        import urllib.parse as up
        qs = up.urlparse(response.url).query
        params = up.parse_qs(qs)
        if "since" in params:
            range_val = params["since"][0]

        articles = response.css("article.Box-row")
        self.logger.info(f"Parsing {response.url} — {len(articles)} articles — range={range_val}")

        for article in articles:
            try:
                item = self._parse_article(article, range_val)
                if item:
                    yield item
            except Exception as exc:
                self.logger.error(f"Error parsing article: {exc}")

    def _parse_article(self, article, range_val="daily") -> HotspotItem | None:
        h2_link = article.css("h2 a")
        if not h2_link:
            return None

        href = h2_link.attrib.get("href", "").strip()
        parts = [p for p in href.split("/") if p]
        if len(parts) < 2:
            return None
        owner, repo = parts[0], parts[1]
        name = f"{owner}/{repo}"

        description = None
        desc_p = article.css("p")
        if desc_p:
            description = desc_p.css("::text").get()
            if description:
                description = description.strip()

        lang_span = article.css("span[itemprop='programmingLanguage']::text").get()
        language = lang_span.strip() if lang_span else None

        f6_text = " ".join(article.css("div.f6 ::text").getall())
        nums = re.findall(r"[\d,]+", f6_text)
        stars = _parse_number(nums[0]) if len(nums) > 0 else None
        forks = _parse_number(nums[1]) if len(nums) > 1 else None
        stars_since = _parse_number(nums[2]) if len(nums) > 2 else None
        forks_since = _parse_number(nums[3]) if len(nums) > 3 else None

        topics = article.css("a.topic-tag::text").getall()
        if not topics:
            topics = article.css("a.topic-tag link-gray::text").getall()
        if not topics:
            topics = article.css('[data-octo-click="topic_click"]::text').getall()
        if not topics:
            topic_anchors = article.xpath(
                ".//a[contains(@href, '/topics/')]/text()"
            ).getall()
            topics = topic_anchors
        topics = [t.strip() for t in topics if t.strip()]

        s_stars = stars_since or 0
        s_forks = forks_since or 0
        hot_score = s_stars * 10 + s_forks * 5

        return self.make_item(
            unique_id=name,
            title=name,
            url=f"https://github.com/{name}",
            description=description,
            author=owner,
            language=language,
            stars=stars,
            stars_since=stars_since,
            forks=forks,
            topics=topics,
            score=s_stars,
            hot_score=hot_score,
            range=range_val,
            extra={"forks_since": forks_since},
        )
