from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.auctions import search_auction_lots, artist_auction_history
from tools.charts import price_trend_chart
from tools.sql_query import art_market_query

SPEC = AGENTS_BY_SLUG["auction_tracker"]
TOOLS = [art_market_query, search_auction_lots, artist_auction_history, price_trend_chart]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
