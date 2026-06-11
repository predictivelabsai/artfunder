from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search
from tools.artworks import search_artworks
from tools.auctions import search_auction_lots, artist_auction_history
from tools.charts import treemap_chart
from tools.sql_query import art_market_query
from tools.performance import market_performance, performance_chart

SPEC = AGENTS_BY_SLUG["acquisition_advisor"]
TOOLS = [art_market_query, search_artworks, search_auction_lots, artist_auction_history,
         market_performance, performance_chart, treemap_chart, web_search]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
