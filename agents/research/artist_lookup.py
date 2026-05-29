from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search
from tools.artworks import search_artworks
from tools.auctions import artist_auction_history

SPEC = AGENTS_BY_SLUG["artist_lookup"]
TOOLS = [web_search, search_artworks, artist_auction_history]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
