from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search
from tools.auctions import search_auction_lots, artist_auction_history
from tools.artworks import search_artworks

SPEC = AGENTS_BY_SLUG["valuator"]
TOOLS = [web_search, search_auction_lots, artist_auction_history, search_artworks]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
