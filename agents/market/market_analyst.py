from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search
from tools.auctions import search_auction_lots, artist_auction_history
from tools.charts import treemap_chart, price_trend_chart

SPEC = AGENTS_BY_SLUG["market_analyst"]
TOOLS = [web_search, search_auction_lots, artist_auction_history, treemap_chart, price_trend_chart]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
