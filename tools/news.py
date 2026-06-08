"""Art news feed — fetches from Estonian art media via RSS + Exa fallback.

Results are cached server-side for NEWS_INTERVAL_SECONDS (default 1800 = 30 min).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import httpx
from utils.config import settings, get_news_interval

log = logging.getLogger(__name__)

_cache: dict = {"items": [], "ts": 0}

ART_SOURCES = [
    {"name": "Sirp", "domain": "sirp.ee", "rss_url": "https://sirp.ee/feed/", "lang": "et"},
    {"name": "ERR Kultuur", "domain": "err.ee", "rss_url": "https://www.err.ee/rss/kultuur", "lang": "et"},
    {"name": "Postimees Kultuur", "domain": "postimees.ee", "rss_url": "https://www.postimees.ee/rss/kultuur", "lang": "et"},
    {"name": "Delfi Kultuur", "domain": "delfi.ee", "rss_url": "https://www.delfi.ee/rss/kultuur", "lang": "et"},
]

EXA_ART_QUERIES = [
    "Estonian art auction news",
    "Baltic contemporary art exhibitions",
    "Estonian gallery openings art market",
    "Nordic art market trends",
    "Eesti kunstioksjon",
    "contemporary art prices Europe",
    "Estonian artists international exhibitions",
    "Baltic art collecting investment",
]


def _fetch_rss(source: dict, max_items: int = 5) -> list[dict]:
    """Fetch and parse an RSS feed."""
    try:
        import feedparser
        feed = feedparser.parse(source["rss_url"])
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "snippet": (entry.get("summary") or entry.get("description") or "")[:200],
                "source": source["name"],
                "published": entry.get("published", ""),
            })
        return items
    except Exception as e:
        log.debug("RSS fetch failed for %s: %s", source["name"], e)
        return []


def _fetch_exa_news(max_items: int = 8) -> list[dict]:
    """Fetch art news via Exa search.

    Rotates through queries daily so the digest doesn't repeat the same results.
    """
    key = settings().exa_api_key
    if not key:
        return []

    day_offset = datetime.utcnow().timetuple().tm_yday
    n = len(EXA_ART_QUERIES)
    queries = [EXA_ART_QUERIES[(day_offset + i) % n] for i in range(3)]

    items = []
    for query in queries:
        try:
            payload = {
                "query": query,
                "numResults": max_items,
                "type": "auto",
                "contents": {"text": {"maxCharacters": 300}},
                "startPublishedDate": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            }
            headers = {"x-api-key": key, "content-type": "application/json"}
            r = httpx.post("https://api.exa.ai/search", json=payload, headers=headers, timeout=15.0)
            r.raise_for_status()
            data = r.json()
            for h in (data.get("results") or []):
                items.append({
                    "title": h.get("title", ""),
                    "url": h.get("url", ""),
                    "snippet": (h.get("text") or "")[:200],
                    "source": "Exa",
                    "published": h.get("publishedDate", ""),
                })
        except Exception as e:
            log.debug("Exa news fetch failed: %s", e)

    return items[:max_items]


def _fetch_fresh(max_items: int = 12) -> list[dict]:
    """Fetch art news from RSS feeds first, Exa as supplement."""
    all_items = []

    try:
        import feedparser  # noqa: F401
        for source in ART_SOURCES:
            all_items.extend(_fetch_rss(source, max_items=3))
    except ImportError:
        log.debug("feedparser not installed, skipping RSS")

    if len(all_items) < max_items:
        exa_items = _fetch_exa_news(max_items=max_items - len(all_items))
        all_items.extend(exa_items)

    seen = set()
    unique = []
    for item in all_items:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(item)

    return unique[:max_items]


def fetch_art_news(max_items: int = 12) -> list[dict]:
    """Return cached news, refreshing when the interval expires."""
    interval = get_news_interval()
    now = time.time()
    if _cache["items"] and (now - _cache["ts"]) < interval:
        return _cache["items"][:max_items]

    items = _fetch_fresh(max_items)
    _cache["items"] = items
    _cache["ts"] = now
    log.info("News cache refreshed (%d items, interval=%ds)", len(items), interval)
    return items[:max_items]
