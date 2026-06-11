"""3-tier agent routing: prefix match -> keyword heuristics -> LLM fallback."""

from __future__ import annotations

import logging
import re

from agents.registry import AGENTS, AGENTS_BY_SLUG, AgentSpec

log = logging.getLogger(__name__)

_PREFIX_MAP: dict[str, str] = {a.prefix.rstrip(":"): a.slug for a in AGENTS if a.prefix}

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "research": ["artist", "biography", "exhibition", "gallery", "who is", "tell me about",
                  "career", "retrospective", "museum", "represented by"],
    "market": ["market", "trend", "auction", "sales", "price", "overbid", "sold",
               "trading", "volume", "sector", "category", "analytics", "chart"],
    "advisory": ["advise", "recommend", "buy", "acquire", "budget", "collection",
                 "portfolio", "diversif", "invest", "strategy", "rebalance"],
    "valuation": ["value", "valuation", "worth", "estimate", "apprais", "provenance",
                  "authenticity", "ownership", "exhibition history", "condition"],
}

_SLUG_KEYWORDS: dict[str, list[str]] = {
    "artist_lookup": ["artist", "biography", "who is", "tell me about", "career"],
    "artist_compare": ["compare", "versus", "vs", "comparison", "side by side"],
    "market_analyst": ["market", "trend", "sector", "heat map", "analytics"],
    "auction_tracker": ["auction", "lot", "sold", "hammer", "allee", "haus", "sale"],
    "acquisition_advisor": ["advise", "recommend", "buy", "acquire", "budget", "should i",
                             "roi", "return", "appreciat", "cagr", "invest", "per year",
                             "% a year", "how much would", "grow"],
    "portfolio_analyst": ["portfolio", "holdings", "diversif", "rebalance", "concentration",
                           "performance", "performed", "annualis", "annualiz"],
    "valuator": ["value", "valuation", "worth", "estimate", "apprais", "fair price"],
    "provenance_checker": ["provenance", "authenticity", "ownership", "exhibition history", "origin"],
}


def _prefix_match(message: str) -> str | None:
    m = re.match(r"^(\w+):\s", message.strip())
    if not m:
        return None
    prefix = m.group(1).lower()
    return _PREFIX_MAP.get(prefix)


def _keyword_scores(message: str) -> dict[str, int]:
    lower = message.lower()
    scores: dict[str, int] = {}
    for slug, keywords in _SLUG_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[slug] = score
    return scores


def _llm_classify(message: str) -> str:
    """Cheap LLM call to classify intent. Falls back to artist_lookup."""
    try:
        from utils.llm import build_llm
        slugs = ", ".join(AGENTS_BY_SLUG.keys())
        prompt = (
            f"Classify this user message into exactly one of these agent slugs: {slugs}\n"
            f"Message: {message}\n"
            f"Reply with ONLY the slug, nothing else."
        )
        llm = build_llm(temperature=0)
        resp = llm.invoke(prompt).content.strip().lower()
        if resp in AGENTS_BY_SLUG:
            return resp
    except Exception as e:
        log.warning("LLM classify failed: %s", e)
    return "artist_lookup"


def route(message: str) -> str:
    slug = _prefix_match(message)
    if slug:
        return slug

    scores = _keyword_scores(message)
    if scores:
        return max(scores, key=scores.get)

    return _llm_classify(message)


def strip_prefix(message: str) -> str:
    """Remove the routing prefix from a message before sending to the agent."""
    return re.sub(r"^\w+:\s*", "", message.strip())
