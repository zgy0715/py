import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSV_DIR = os.path.join(PROJECT_ROOT, "data")
CSV_FILES = {
    "daily": os.path.join(CSV_DIR, "github_trending_daily.csv"),
    "weekly": os.path.join(CSV_DIR, "github_trending_weekly.csv"),
    "monthly": os.path.join(CSV_DIR, "github_trending_monthly.csv"),
}

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "tech_hotspot")

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
HOTSPOT_ZSET_KEY = "hotspot:all"
HOTSPOT_ITEM_PREFIX = "item:"

PAGE_TITLE = "Tech Hotspot · 技术热点可视化"
PAGE_ICON = "\U0001f4ca"
LAYOUT = "wide"

# Dark glass theme colors
COLOR_MAP = {
    "github": "#00D4FF",
    "hn": "#F59E0B",
    "arxiv": "#EF4444",
    "reddit": "#FF4500",
    "daily": "#00D4FF",
    "weekly": "#A855F7",
    "monthly": "#F59E0B",
}

LANGUAGE_COLORS = [
    "#00D4FF", "#A855F7", "#F59E0B", "#EC4899",
    "#10B981", "#F43F5E", "#8B5CF6", "#06B6D4",
    "#F97316", "#6366F1", "#84CC16", "#D946EF",
    "#14B8A6", "#3B82F6",
]

DEFAULT_SINCE = "daily"
DEFAULT_MIN_STARS = 0
TOP_N = 20

# Dark Plotly template
PLOTLY_DARK_TEMPLATE = "plotly_dark"
PLOTLY_LIGHT_TEMPLATE = "plotly_white"

# Theme names
THEME_DARK = "dark"
THEME_LIGHT = "light"
