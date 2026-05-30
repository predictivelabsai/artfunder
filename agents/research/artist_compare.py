from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search
from tools.auctions import artist_auction_history, search_auction_lots
from tools.sql_query import art_market_query

SPEC = AGENTS_BY_SLUG["artist_compare"]
TOOLS = [art_market_query, artist_auction_history, search_auction_lots, web_search]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
