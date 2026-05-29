from functools import lru_cache

from agents.base import build_agent
from agents.registry import AGENTS_BY_SLUG
from tools.search import web_search
from tools.artworks import search_artworks, get_artwork

SPEC = AGENTS_BY_SLUG["provenance_checker"]
TOOLS = [web_search, search_artworks, get_artwork]


@lru_cache(maxsize=1)
def build():
    return build_agent(SPEC, TOOLS)
