import re
from datetime import datetime, timezone

import scrapy

from github_trending.items import GitHubTrendingItem

# 默认抓取的主流编程语言
DEFAULT_LANGUAGES = [
    "python", "javascript", "typescript", "rust", "go",
    "java", "c++", "c", "shell", "swift", "kotlin",
    "ruby", "c%23", "php",
]


def parse_number(text: str | None) -> int | None:
    """从文本中提取数字，处理 'k'/'K' 缩写。"""
    if not text:
        return None
    text = text.strip().lower().replace(",", "")
    match = re.search(r"([\d.]+)\s*(k)?", text)
    if not match:
        return None
    num = float(match.group(1))
    if match.group(2) == "k":
        num = int(num * 1000)
    else:
        num = int(num)
    return num


class GitHubTrendingSpider(scrapy.Spider):
    """
    抓取 GitHub Trending 热门项目，覆盖主流编程语言。

    参数:
        since     - 榜单周期: daily / weekly / monthly（默认 daily）
        languages - 逗号分隔的编程语言列表（默认覆盖主流语言）
    """

    name = "github_trending_ai"
    allowed_domains = ["github.com"]

    def __init__(self, since="daily", languages=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.since = since if since in ("daily", "weekly", "monthly") else "daily"

        if languages:
            self.languages = [l.strip() for l in languages.split(",") if l.strip()]
        else:
            self.languages = DEFAULT_LANGUAGES

        self._url_seen = set()
        self.logger.info(
            f"Spider initialized: since={self.since}, "
            f"languages={len(self.languages)} ({', '.join(self.languages[:5])}...)"
        )

    def start_requests(self):
        # 主 Trending 页（全语言）
        yield scrapy.Request(
            f"https://github.com/trending?since={self.since}",
            callback=self.parse,
            meta={"language": None},
            dont_filter=True,
        )
        # 各语言分页
        for lang in self.languages:
            yield scrapy.Request(
                f"https://github.com/trending/{lang}?since={self.since}",
                callback=self.parse,
                meta={"language": lang},
                dont_filter=True,
            )

    async def start(self):
        # async 版本，与 start_requests 保持一致
        yield scrapy.Request(
            f"https://github.com/trending?since={self.since}",
            callback=self.parse,
            meta={"language": None},
            dont_filter=True,
        )
        for lang in self.languages:
            yield scrapy.Request(
                f"https://github.com/trending/{lang}?since={self.since}",
                callback=self.parse,
                meta={"language": lang},
                dont_filter=True,
            )

    def parse(self, response, **kwargs):
        lang = response.meta.get("language")
        lang_label = lang or "all"
        self.logger.info(f"Parsing trending/{lang_label} — {response.url}")

        articles = response.css("article.Box-row")
        if not articles:
            self.logger.warning(
                f"No articles found on trending/{lang_label}. "
                f"GitHub may require JS rendering or the page structure has changed."
            )
            return

        self.logger.info(f"Found {len(articles)} articles on trending/{lang_label}")

        items_on_page = 0
        for idx, article in enumerate(articles):
            try:
                item = self._parse_article(article, idx, len(articles), lang_label)
                if item is None:
                    continue
                items_on_page += 1
                yield item

            except Exception as exc:
                self.logger.error(
                    f"Unexpected error parsing article #{idx + 1} on trending/{lang_label}: {exc}",
                    exc_info=True,
                )

        self.logger.info(
            f"trending/{lang_label} done: {items_on_page} items yielded out of {len(articles)} total"
        )

    def _parse_article(self, article, idx: int, total: int, page: str) -> GitHubTrendingItem | None:
        """解析单个 article 节点，返回 Item 或 None（重复项返回 None）。"""
        # ---- 提取 owner/repo ----
        h2_link = article.css("h2 a")
        if not h2_link:
            self.logger.warning(f"Skipping article #{idx + 1}: no h2 a link found")
            return None

        href = h2_link.attrib.get("href", "").strip()
        path_parts = [p for p in href.split("/") if p]
        if len(path_parts) < 2:
            self.logger.warning(f"Skipping article #{idx + 1}: invalid href '{href}'")
            return None
        owner = path_parts[0]
        repo = path_parts[1]
        name = f"{owner}/{repo}"

        # 跨语言去重
        if name in self._url_seen:
            self.logger.debug(f"Skipping duplicate: {name}")
            return None
        self._url_seen.add(name)

        # ---- 提取描述 ----
        desc_p = article.css("p")
        description = desc_p.css("::text").get()
        if description:
            description = description.strip()

        # ---- 提取编程语言 ----
        lang_span = article.css("span[itemprop='programmingLanguage']::text").get()
        if not lang_span:
            lang_spans = article.xpath(
                ".//span[contains(@class, 'd-inline-block') and contains(@class, 'ml-0')]/span[2]/text()"
            ).getall()
            lang_span = lang_spans[0].strip() if lang_spans else None
        language = lang_span.strip() if lang_span else None

        # ---- 提取 Stars / Forks / 新增星数 ----
        f6_text = " ".join(article.css("div.f6 ::text").getall())
        nums = re.findall(r"[\d,]+", f6_text)
        stars = parse_number(nums[0]) if len(nums) > 0 else None
        forks = parse_number(nums[1]) if len(nums) > 1 else None
        stars_since = parse_number(nums[2]) if len(nums) > 2 else None

        # ---- 提取 Topics ----
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

        # ---- 构建 Item ----
        url = f"https://github.com/{name}"
        crawl_time = datetime.now(timezone.utc).isoformat()

        item = GitHubTrendingItem(
            rank=idx + 1,          # 该语言页内的排名
            name=name,
            owner=owner,
            description=description,
            language=language,
            stars=stars,
            stars_since=stars_since,
            forks=forks,
            topics=topics,
            url=url,
            crawl_time=crawl_time,
            since=self.since,
            page=page,              # 来源语言（all / python / rust …）
        )

        self.logger.info(f"#{idx + 1} {name} | stars={stars} | since_stars={stars_since}")
        return item
