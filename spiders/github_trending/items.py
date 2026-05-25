import scrapy


class GitHubTrendingItem(scrapy.Item):
    """GitHub Trending AI project item."""
    rank = scrapy.Field()
    name = scrapy.Field()
    owner = scrapy.Field()
    description = scrapy.Field()
    language = scrapy.Field()
    stars = scrapy.Field()
    stars_since = scrapy.Field()
    forks = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    crawl_time = scrapy.Field()
    since = scrapy.Field()
    page = scrapy.Field()
