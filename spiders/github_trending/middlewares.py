import random
import logging
from scrapy import signals

logger = logging.getLogger(__name__)

try:
    from fake_useragent import UserAgent
    _ua_factory = UserAgent(
        browsers=["chrome", "firefox", "edge", "safari"],
        platforms=["desktop"],
    )
    def _random_ua_fake() -> str:
        return _ua_factory.random
    _UA_SOURCE = "fake-useragent"
except ImportError:
    _ua_factory = None
    _UA_SOURCE = "fallback"

FALLBACK_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7; rv:132.0) Gecko/20100101 Firefox/132.0",
]


class RandomUserAgentMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        o = cls()
        logger.info(f"UserAgent middleware using: {_UA_SOURCE}")
        return o

    def process_request(self, request):
        if _ua_factory is not None:
            try:
                ua = _random_ua_fake()
            except Exception:
                ua = random.choice(FALLBACK_USER_AGENTS)
        else:
            ua = random.choice(FALLBACK_USER_AGENTS)
        request.headers.setdefault("User-Agent", ua)


class ProxyMiddleware:

    def __init__(self, proxy_pool=None):
        self.proxy_pool = proxy_pool or []

    @classmethod
    def from_crawler(cls, crawler):
        proxy_pool = crawler.settings.getlist("PROXY_POOL")
        return cls(proxy_pool)

    def process_request(self, request):
        if self.proxy_pool:
            proxy = random.choice(self.proxy_pool)
            request.meta["proxy"] = proxy
            logger.debug(f"Using proxy: {proxy}")


class GitHubTrendingSpiderMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def spider_opened(self, spider):
        spider.logger.info(f"Spider opened: {spider.name}")

    def process_spider_input(self, response):
        return None

    def process_spider_output(self, response, result):
        for item in result:
            yield item

    async def process_spider_output_async(self, response, result):
        async for item in result:
            yield item

    def process_spider_exception(self, response, exception):
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    async def process_start(self, start):
        async for r in start:
            yield r
