"""Art news feed — fetches from Estonian art media via RSS + Exa fallback.

Results are cached server-side for NEWS_INTERVAL_SECONDS (default 1800 = 30 min).
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Optional

import httpx
from utils.config import settings, get_news_interval

log = logging.getLogger(__name__)

_cache: dict = {"items": [], "ts": 0}

_TAG_RE = re.compile(r"<[^>]+>")
_ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _clean_text(raw: str, limit: int = 200) -> str:
    """Strip HTML tags + entities from RSS/Exa summaries and collapse whitespace.

    RSS summaries (e.g. Sirp) embed <p>/<br> markup that, injected via innerHTML,
    breaks out of the styled snippet element and renders with the browser default
    font. Returning plain text keeps every source's snippet visually consistent.
    """
    if not raw:
        return ""
    txt = _TAG_RE.sub(" ", raw)
    txt = unescape(txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:limit]


def _iso_date(date_str: str = "", struct=None) -> str:
    """Normalise a publish date to 'YYYY-MM-DD' so all sources format consistently.

    RSS gives RFC-822 ('Thu, 11 Jun 2026 04:00:00 +0000'); Exa gives ISO. Without
    this the frontend's slice(0,10) mangles RFC-822 into 'Thu, 11 Ju'.
    """
    if struct:
        try:
            return time.strftime("%Y-%m-%d", struct)
        except Exception:
            pass
    s = (date_str or "").strip()
    if not s:
        return ""
    if _ISO_RE.match(s):
        return s[:10]
    try:
        return parsedate_to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return s[:10]

ART_SOURCES = [
    {"name": "Sirp", "domain": "sirp.ee", "rss_url": "https://sirp.ee/feed/", "lang": "et"},
    {"name": "ERR Kultuur", "domain": "err.ee", "rss_url": "https://kultuur.err.ee/rss", "lang": "et"},
    {"name": "Postimees Kultuur", "domain": "postimees.ee", "rss_url": "https://kultuur.postimees.ee/rss", "lang": "et"},
    {"name": "Eesti Muuseumid", "domain": "muuseum.ee", "rss_url": "https://www.muuseum.ee/feed/", "lang": "et"},
]

# Some feeds reject requests without a browser-like User-Agent.
_RSS_USER_AGENT = "Mozilla/5.0 (compatible; KanvasBot/1.0; +https://kanvas.ai)"

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
        feed = feedparser.parse(source["rss_url"], agent=_RSS_USER_AGENT)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": _clean_text(entry.get("title", ""), limit=300),
                "url": entry.get("link", ""),
                "snippet": _clean_text(entry.get("summary") or entry.get("description") or ""),
                "source": source["name"],
                "published": _iso_date(entry.get("published", ""), entry.get("published_parsed")),
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
                    "title": _clean_text(h.get("title", ""), limit=300),
                    "url": h.get("url", ""),
                    "snippet": _clean_text(h.get("text") or ""),
                    "source": "Exa",
                    "published": _iso_date(h.get("publishedDate", "")),
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
