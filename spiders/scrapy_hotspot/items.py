import scrapy


class HotspotItem(scrapy.Item):
    """统一 Item：四个数据源共用字段。"""

    source = scrapy.Field()          # "github" | "hn" | "arxiv" | "reddit"
    unique_id = scrapy.Field()       # 去重依据（repo_name / post_id / paper_id）
    title = scrapy.Field()
    url = scrapy.Field()
    description = scrapy.Field()
    author = scrapy.Field()          # 作者 / 组织名
    language = scrapy.Field()        # 编程语言（GitHub）
    score = scrapy.Field()           # 原始分数（HN score / Reddit score）
    comments = scrapy.Field()        # 评论数
    stars = scrapy.Field()           # GitHub total stars
    stars_since = scrapy.Field()     # GitHub 周期新增星数
    forks = scrapy.Field()           # GitHub forks
    topics = scrapy.Field()          # GitHub topics（List[str]）
    hot_score = scrapy.Field()       # 热度分（写入 Redis ZSET）
    range = scrapy.Field()           # 时间范围（daily / weekly / monthly）
    published_at = scrapy.Field()    # 发布时间
    crawl_time = scrapy.Field()      # 抓取时间
    extra = scrapy.Field()           # 扩展数据（dict）
