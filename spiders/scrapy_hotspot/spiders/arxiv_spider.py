import re
from datetime import datetime, timezone, timedelta

from scrapy_hotspot.items import HotspotItem
from scrapy_hotspot.spiders.base_spider import BaseHotspotSpider


class ArxivSpider(BaseHotspotSpider):
    """抓取 arXiv 最新论文（cs.AI / cs.LG / cs.CL），只保留 3 天内。hot_score=0"""

    name = "arxiv"
    redis_key = "arxiv:start_urls"
    item_source = "arxiv"

    def parse(self, response):
        dl = response.css("div#dlpage dl")
        if not dl:
            self.logger.warning(f"No dl#dlpage on {response.url}")
            return

        cutoff = datetime.now(timezone.utc) - timedelta(days=3)
        current_date = None
        dt_elements = dl.css("dt")

        self.logger.info(f"Parsing {response.url} — {len(dt_elements)} papers")

        for dt in dt_elements:
            try:
                prev_h3 = dt.xpath("preceding-sibling::h3[1]/text()").get()
                if prev_h3:
                    date_match = re.search(r"(\w+,\s+\d+\s+\w+\s+\d{4})", prev_h3)
                    if date_match:
                        try:
                            current_date = datetime.strptime(
                                date_match.group(1), "%a, %d %b %Y"
                            ).replace(tzinfo=timezone.utc)
                        except ValueError:
                            pass

                if current_date and current_date < cutoff:
                    continue

                item = self._parse_paper(dt, current_date)
                if item:
                    yield item
            except Exception as exc:
                self.logger.error(f"Error parsing arXiv paper: {exc}")

    def _parse_paper(self, dt, paper_date: datetime | None) -> HotspotItem | None:
        paper_id = None
        for a in dt.css("a"):
            href = a.attrib.get("href", "")
            m = re.search(r"/abs/(\d+\.\d+)", href)
            if m:
                paper_id = m.group(1)
                break
        if not paper_id:
            return None

        dd = dt.xpath("following-sibling::dd[1]")
        if not dd:
            return None

        title_div = dd.css("div.list-title")
        title = None
        if title_div:
            full_title = " ".join(title_div.css("::text").getall()).strip()
            title = re.sub(r"^Title:\s*", "", full_title)

        authors_div = dd.css("div.list-authors")
        author = None
        if authors_div:
            author_texts = authors_div.css("a::text").getall()
            author = "; ".join(author_texts) if author_texts else None

        abstract_p = dd.css("p.mathjax::text").get()
        abstract = abstract_p.strip()[:200] if abstract_p else None

        return self.make_item(
            unique_id=paper_id,
            title=title or paper_id,
            url=f"https://arxiv.org/abs/{paper_id}",
            description=abstract,
            author=author,
            hot_score=0,
            published_at=paper_date.isoformat() if paper_date else None,
            extra={"paper_id": paper_id},
        )
