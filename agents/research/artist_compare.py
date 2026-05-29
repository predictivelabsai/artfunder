from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search
from tools.auctions import artist_auction_history, search_auction_lots

SPEC = AGENTS_BY_SLUG["artist_compare"]
TOOLS = [web_search, artist_auction_history, search_auction_lots]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
