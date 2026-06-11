from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.artworks import search_artworks, get_artwork
from tools.auctions import artist_auction_history
from tools.charts import treemap_chart, price_trend_chart
from tools.sql_query import art_market_query
from tools.performance import market_performance, performance_chart

SPEC = AGENTS_BY_SLUG["portfolio_analyst"]
TOOLS = [art_market_query, search_artworks, get_artwork, artist_auction_history,
         market_performance, performance_chart, treemap_chart, price_trend_chart]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
