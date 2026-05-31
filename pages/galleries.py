"""Galleries & Auctions page — auto-generated from config/auction_sources.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml
from fasthtml.common import *

from utils.i18n import t, get_lang

ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "config" / "auction_sources.yaml"

COUNTRY_NAMES = {
    "EE": "Estonia", "LV": "Latvia", "LT": "Lithuania",
    "FI": "Finland", "SE": "Sweden", "DK": "Denmark",
    "NO": "Norway", "NL": "Netherlands", "GB": "United Kingdom",
}

COUNTRY_FLAGS = {
    "EE": "\U0001f1ea\U0001f1ea", "LV": "\U0001f1f1\U0001f1fb",
    "LT": "\U0001f1f1\U0001f1f9", "FI": "\U0001f1eb\U0001f1ee",
    "SE": "\U0001f1f8\U0001f1ea", "DK": "\U0001f1e9\U0001f1f0",
    "NO": "\U0001f1f3\U0001f1f4", "NL": "\U0001f1f3\U0001f1f1",
    "GB": "\U0001f1ec\U0001f1e7",
}

STATUS_BADGE = {
    "active": ("Live", "bg-green-50 text-green-700 border-green-200"),
    "planned": ("Planned", "bg-yellow-50 text-yellow-700 border-yellow-200"),
    "blocked": ("Blocked", "bg-red-50 text-red-700 border-red-200"),
}


def _load_sources() -> list[dict]:
    if not SOURCES_FILE.exists():
        return []
    with open(SOURCES_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("sources", [])


def _group_by_country(sources: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for s in sources:
        country = s.get("country", "??")
        groups.setdefault(country, []).append(s)
    return groups


def galleries_page(sess=None):
    lang = get_lang(sess or {})
    sources = _load_sources()
    by_country = _group_by_country(sources)

    country_order = ["EE", "LV", "LT", "FI", "SE", "DK", "NO", "NL", "GB"]
    country_sections = []

    total_sources = len(sources)
    total_countries = len(by_country)
    active_count = sum(1 for s in sources if s.get("status") == "active")

    for code in country_order:
        galleries = by_country.get(code, [])
        if not galleries:
            continue

        flag = COUNTRY_FLAGS.get(code, "")
        name = COUNTRY_NAMES.get(code, code)

        cards = []
        for g in galleries:
            status = g.get("status", "planned")
            badge_label, badge_cls = STATUS_BADGE.get(status, ("Unknown", "bg-gray-50 text-gray-500 border-gray-200"))
            year_range = g.get("year_range", [])
            years_str = f"{year_range[0]}-{year_range[1]}" if len(year_range) == 2 else ""
            lots = g.get("lots_estimate", 0)
            lots_str = f"{lots:,}" if lots else "—"

            notes = g.get("notes", "")
            if isinstance(notes, str):
                notes = notes.strip().split("\n")[0][:120]

            cards.append(
                A(
                    Div(
                        Div(
                            Span(g.get("name", ""), cls="text-sm font-medium text-black"),
                            Span(badge_label, cls=f"text-[10px] px-2 py-0.5 rounded-full border {badge_cls}"),
                            cls="flex items-center justify-between gap-2",
                        ),
                        P(notes, cls="text-xs text-gray-400 mt-1 leading-relaxed line-clamp-2") if notes else "",
                        Div(
                            Span(f"{lots_str} lots", cls="text-xs text-gray-400") if lots else "",
                            Span(years_str, cls="text-xs text-gray-400") if years_str else "",
                            cls="flex gap-3 mt-2",
                        ),
                        cls="p-4",
                    ),
                    href=g.get("url", "#"),
                    target="_blank",
                    cls="block rounded-xl border border-gray-100 hover:border-gray-300 transition-colors no-underline",
                )
            )

        country_sections.append(
            Div(
                H3(f"{flag} {name}", cls="text-lg font-medium text-black mb-4"),
                Div(*cards, cls="grid md:grid-cols-2 lg:grid-cols-3 gap-3"),
                cls="mb-10",
            )
        )

    hero = Section(
        Div(
            Span("Data Sources", cls="text-[11px] tracking-[0.18em] uppercase text-gray-400"),
            H1("Galleries & Auctions", cls="text-[36px] sm:text-4xl md:text-5xl font-medium tracking-tight text-black leading-[1.08] mt-3"),
            P("Auction houses and galleries providing historical sales data to the Kanvas.ai Art Index. "
              "Each source is scraped with Playwright and loaded into our database for AI-powered market analysis.",
              cls="mt-4 text-gray-500 text-base max-w-2xl leading-relaxed"),
            Div(
                Div(
                    Span(str(total_sources), cls="text-xl font-semibold text-black"),
                    Span("Sources", cls="text-[11px] tracking-wider uppercase text-gray-400 mt-1"),
                    cls="flex flex-col",
                ),
                Div(
                    Span(str(total_countries), cls="text-xl font-semibold text-black"),
                    Span("Countries", cls="text-[11px] tracking-wider uppercase text-gray-400 mt-1"),
                    cls="flex flex-col",
                ),
                Div(
                    Span(str(active_count), cls="text-xl font-semibold text-black"),
                    Span("Live Scrapers", cls="text-[11px] tracking-wider uppercase text-gray-400 mt-1"),
                    cls="flex flex-col",
                ),
                cls="flex gap-10 mt-8",
            ),
            cls="max-w-7xl mx-auto px-5 md:px-6 py-16 md:py-20",
        ),
    )

    listing = Section(
        Div(
            *country_sections,
            cls="max-w-7xl mx-auto px-5 md:px-6",
        ),
        cls="py-10 md:py-14 border-t border-gray-100",
    )

    return Div(hero, listing, style="overflow-x:hidden")
