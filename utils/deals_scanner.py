"""Art Deals Scanner — surfaces interesting auction lots for the daily digest.

Four sections:
  1. Bidding Wars     — lots that sold far above estimate (highest overbid %)
  2. Value Finds      — works by top artists that sold below their average
  3. Market Movers    — artists with the highest total sales and lot count
  4. Art News         — latest headlines from RSS feeds + Exa
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from urllib.parse import quote

log = logging.getLogger(__name__)

BASE_URL = os.getenv("SERVICE_URL_KANVAS", "https://kanvas.ai")

PROVIDER_LABELS = {
    "haus": "Haus Galerii",
    "allee": "Allee Galerii",
    "vaal": "Vaal Galerii",
    "vernissage": "Vernissage",
    "artandtonic": "Art & Tonic",
    "salong": "E-Kunstisalong",
    "antonija": "Antonija",
    "bonhams": "Bonhams",
    "bukowskis": "Bukowskis",
    "hagelstam": "Hagelstam",
    "gwpa": "GWPA",
    "bruun_rasmussen": "Bruun Rasmussen",
    "auctionet": "Auctionet",
}

COUNTRY_FOR_PROVIDER = {
    "haus": "EE", "allee": "EE", "vaal": "EE", "vernissage": "EE",
    "artandtonic": "EE", "salong": "EE",
    "antonija": "LV",
    "bonhams": "GB",
    "bukowskis": "SE",
    "hagelstam": "FI",
    "gwpa": "GB",
    "bruun_rasmussen": "DK",
    "auctionet": "SE",
}


def scan_bidding_wars(limit: int = 10) -> list[dict]:
    """Lots that sold furthest above estimate — shows market heat.

    Picks from the top 100 by overbid, then shuffles daily using a
    date-based seed so each day's digest features different lots.
    """
    from db import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        sql = text("""
            SELECT * FROM (
                SELECT author, title, start_price, end_price,
                       ROUND((end_price - start_price)::numeric / start_price * 100, 1) AS overbid_pct,
                       tech, auction_provider, auction_date, image_url, source_url
                FROM kanvas.auction_lots
                WHERE COALESCE(status, 'active') = 'active'
                  AND end_price >= 100 AND start_price > 0
                  AND end_price > start_price
                  AND author !~ '^\\d+$'
                  AND LENGTH(TRIM(author)) > 3
                  AND image_url IS NOT NULL AND image_url != ''
                ORDER BY (end_price - start_price)::float / start_price DESC
                LIMIT 100
            ) pool
            ORDER BY md5(author || title || CURRENT_DATE::text)
            LIMIT :lim
        """)
        return [dict(r._mapping) for r in db.execute(sql, {"lim": limit})]
    finally:
        db.close()


def scan_value_finds(limit: int = 10) -> list[dict]:
    """Works by top artists that sold below their historical average — potential bargains.

    Picks from a larger pool and rotates daily via date-based hash.
    """
    from db import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        sql = text("""
            SELECT * FROM (
                WITH top_artists AS (
                    SELECT author, AVG(end_price)::int AS avg_price,
                           COUNT(*) AS total_lots, SUM(end_price) AS total_sales
                    FROM kanvas.auction_lots
                    WHERE COALESCE(status, 'active') = 'active'
                      AND end_price >= 100
                    GROUP BY author
                    HAVING COUNT(*) >= 5 AND AVG(end_price) >= 200
                )
                SELECT l.author, l.title, l.start_price, l.end_price,
                       a.avg_price AS artist_avg,
                       ROUND((a.avg_price - l.end_price)::numeric / a.avg_price * 100, 1) AS discount_pct,
                       l.tech, l.auction_provider, l.auction_date,
                       l.image_url, l.source_url,
                       a.total_lots, a.total_sales
                FROM kanvas.auction_lots l
                JOIN top_artists a ON l.author = a.author
                WHERE COALESCE(l.status, 'active') = 'active'
                  AND l.end_price >= 50
                  AND l.end_price < a.avg_price * 0.5
                  AND l.image_url IS NOT NULL AND l.image_url != ''
                ORDER BY a.total_sales DESC, discount_pct DESC
                LIMIT 100
            ) pool
            ORDER BY md5(author || title || CURRENT_DATE::text)
            LIMIT :lim
        """)
        return [dict(r._mapping) for r in db.execute(sql, {"lim": limit})]
    finally:
        db.close()


def scan_market_movers(limit: int = 10) -> list[dict]:
    """Artists with the highest auction activity and total sales volume.

    Picks from top 50 artists and rotates daily.
    """
    from db import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        sql = text("""
            SELECT * FROM (
                SELECT author,
                       COUNT(*) AS lot_count,
                       SUM(end_price) AS total_sales,
                       AVG(end_price)::int AS avg_price,
                       MIN(end_price) AS min_price,
                       MAX(end_price) AS max_price,
                       CASE WHEN SUM(CASE WHEN start_price > 0 THEN 1 ELSE 0 END) > 0
                            THEN ROUND(AVG(CASE WHEN start_price > 0
                                 THEN (end_price - start_price)::float / start_price * 100
                                 ELSE NULL END)::numeric, 1)
                            ELSE NULL END AS avg_overbid_pct
                FROM kanvas.auction_lots
                WHERE COALESCE(status, 'active') = 'active'
                  AND end_price >= 100
                  AND author !~ '^\\d+$'
                  AND LENGTH(TRIM(author)) > 3
                GROUP BY author
                HAVING COUNT(*) >= 5
                ORDER BY SUM(end_price) DESC
                LIMIT 50
            ) pool
            ORDER BY md5(author || CURRENT_DATE::text)
            LIMIT :lim
        """)
        return [dict(r._mapping) for r in db.execute(sql, {"lim": limit})]
    finally:
        db.close()


def fetch_news(max_items: int = 6) -> list[dict]:
    """Fetch fresh art news (bypasses the in-memory cache)."""
    try:
        from tools.news import _fetch_fresh
        items = _fetch_fresh(max_items=max_items)
        return items
    except Exception as e:
        log.warning("News fetch failed: %s", e)
        return []


def _fmt_eur(n) -> str:
    if not n:
        return "--"
    try:
        v = float(n)
        if v >= 1_000_000:
            return f"EUR {v / 1_000_000:,.1f}M"
        return f"EUR {v:,.0f}"
    except (TypeError, ValueError):
        return str(n)


def _provider_label(provider: str | None) -> str:
    return PROVIDER_LABELS.get(provider or "", provider or "")


def _country_flag(provider: str | None) -> str:
    flags = {
        "EE": "\U0001f1ea\U0001f1ea", "LV": "\U0001f1f1\U0001f1fb",
        "FI": "\U0001f1eb\U0001f1ee", "SE": "\U0001f1f8\U0001f1ea",
        "DK": "\U0001f1e9\U0001f1f0", "GB": "\U0001f1ec\U0001f1e7",
    }
    country = COUNTRY_FOR_PROVIDER.get(provider or "", "")
    return flags.get(country, "")


def build_digest_html(bidding_wars: list[dict], value_finds: list[dict],
                      market_movers: list[dict], news: list[dict] | None = None,
                      unsubscribe_url: str = "") -> str:
    now = datetime.now()
    today = now.strftime("%A, %B %d, %Y")
    period = "Morning" if now.hour < 12 else ("Afternoon" if now.hour < 17 else "Evening")

    link_style = "color:inherit; text-decoration:none;"

    # --- Bidding Wars rows ---
    war_rows = ""
    for d in bidding_wars:
        overbid = float(d.get("overbid_pct") or 0)
        badge_color = "#DC2626" if overbid >= 500 else "#F59E0B" if overbid >= 100 else "#16A34A"
        provider = _provider_label(d.get("auction_provider"))
        flag = _country_flag(d.get("auction_provider"))
        title = (d.get("title") or "Untitled")[:50]
        author = (d.get("author") or "Unknown")[:40]
        url = d.get("source_url") or f"{BASE_URL}/app/market-map?author={quote(author)}"
        img = d.get("image_url") or ""
        img_td = f'''<td style="padding:10px 8px; border-bottom:1px solid #E5E7EB; width:56px;">
                <a href="{url}" style="{link_style}" target="_blank"><img src="{img}" alt="" style="width:48px;height:48px;object-fit:cover;border-radius:4px;"></a>
            </td>''' if img else ""

        war_rows += f"""
        <tr>
            {img_td}
            <td style="padding:10px 8px; border-bottom:1px solid #E5E7EB;">
                <a href="{url}" style="{link_style}" target="_blank">
                    <strong style="color:#1A1A1A; font-size:13px;">{author}</strong><br>
                    <span style="font-size:12px; color:#6B7280;">{title}</span><br>
                    <span style="font-size:11px; color:#9CA3AF;">{flag} {provider}</span>
                </a>
            </td>
            <td style="padding:10px 8px; border-bottom:1px solid #E5E7EB; text-align:right;">
                <span style="font-family:'Courier New',monospace; font-size:12px; color:#6B7280;">{_fmt_eur(d.get('start_price'))}</span><br>
                <span style="font-family:'Courier New',monospace; font-size:13px; font-weight:600; color:#1A1A1A;">{_fmt_eur(d.get('end_price'))}</span>
            </td>
            <td style="padding:10px 8px; border-bottom:1px solid #E5E7EB; text-align:center;">
                <span style="background:{badge_color}; color:white; padding:2px 8px; border-radius:12px; font-size:12px; font-weight:600;">
                    +{overbid:.0f}%
                </span>
            </td>
        </tr>"""

    # --- Value Finds rows ---
    value_rows = ""
    for d in value_finds:
        discount = float(d.get("discount_pct") or 0)
        author = (d.get("author") or "Unknown")[:40]
        title = (d.get("title") or "Untitled")[:50]
        provider = _provider_label(d.get("auction_provider"))
        flag = _country_flag(d.get("auction_provider"))
        url = d.get("source_url") or f"{BASE_URL}/app/market-map?author={quote(author)}"
        img = d.get("image_url") or ""
        img_td = f'''<td style="padding:10px 8px; border-bottom:1px solid #E5E7EB; width:56px;">
                <a href="{url}" style="{link_style}" target="_blank"><img src="{img}" alt="" style="width:48px;height:48px;object-fit:cover;border-radius:4px;"></a>
            </td>''' if img else ""

        value_rows += f"""
        <tr>
            {img_td}
            <td style="padding:10px 8px; border-bottom:1px solid #E5E7EB;">
                <a href="{url}" style="{link_style}" target="_blank">
                    <strong style="color:#1A1A1A; font-size:13px;">{author}</strong><br>
                    <span style="font-size:12px; color:#6B7280;">{title}</span><br>
                    <span style="font-size:11px; color:#9CA3AF;">{flag} {provider} &middot; {d.get('total_lots', 0)} lots</span>
                </a>
            </td>
            <td style="padding:10px 8px; border-bottom:1px solid #E5E7EB; text-align:right;">
                <span style="font-family:'Courier New',monospace; font-size:13px; font-weight:600; color:#16A34A;">{_fmt_eur(d.get('end_price'))}</span><br>
                <span style="font-family:'Courier New',monospace; font-size:11px; color:#6B7280;">avg {_fmt_eur(d.get('artist_avg'))}</span>
            </td>
            <td style="padding:10px 8px; border-bottom:1px solid #E5E7EB; text-align:center;">
                <span style="background:#16A34A; color:white; padding:2px 8px; border-radius:12px; font-size:12px; font-weight:600;">
                    -{discount:.0f}%
                </span>
            </td>
        </tr>"""

    # --- Market Movers rows ---
    mover_rows = ""
    for d in market_movers:
        author = (d.get("author") or "Unknown")[:40]
        overbid = d.get("avg_overbid_pct")
        overbid_str = f"+{float(overbid):.0f}%" if overbid else "--"
        url = f"{BASE_URL}/app/market-map?author={quote(author)}"

        mover_rows += f"""
        <tr>
            <td style="padding:8px 12px; border-bottom:1px solid #E5E7EB;">
                <a href="{url}" style="{link_style}" target="_blank">
                    <strong style="color:#1A1A1A; font-size:13px;">{author}</strong>
                </a>
            </td>
            <td style="padding:8px 12px; border-bottom:1px solid #E5E7EB; text-align:right; font-family:'Courier New',monospace; font-size:13px;">
                {_fmt_eur(d.get('total_sales'))}
            </td>
            <td style="padding:8px 12px; border-bottom:1px solid #E5E7EB; text-align:right; font-size:12px; color:#6B7280;">
                {d.get('lot_count', 0)} lots
            </td>
            <td style="padding:8px 12px; border-bottom:1px solid #E5E7EB; text-align:right; font-size:12px;">
                {_fmt_eur(d.get('avg_price'))}
            </td>
            <td style="padding:8px 12px; border-bottom:1px solid #E5E7EB; text-align:center; font-size:12px; color:#F59E0B; font-weight:600;">
                {overbid_str}
            </td>
        </tr>"""

    empty_msg = '<tr><td colspan="5" style="padding:16px; text-align:center; color:#6B7280;">No data available.</td></tr>'

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0; padding:0; background:#F5F5F5; font-family:'Inter','Helvetica Neue',Arial,sans-serif;">
<div style="max-width:680px; margin:0 auto; padding:24px 16px;">

    <!-- Header -->
    <div style="text-align:center; padding:20px 0 24px;">
        <h1 style="color:#1A1A1A; font-size:22px; font-weight:700; margin:0; letter-spacing:-0.02em; font-family:'Cormorant Garamond',Georgia,serif;">
            Kanvas<span style="color:#9CA3AF;">.ai</span>
        </h1>
        <p style="color:#6B7280; font-size:14px; margin:6px 0 0;">{period} Art Deals &middot; {today}</p>
        <p style="color:#9CA3AF; font-size:12px; margin:4px 0 0;">Nordic &amp; Baltic art auction insights</p>
    </div>

    <!-- Bidding Wars -->
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px; padding:16px; margin-bottom:20px;">
        <h2 style="color:#1A1A1A; font-size:16px; font-weight:600; margin:0 0 4px; border-bottom:2px solid #000000; padding-bottom:6px;">
            Bidding Wars
        </h2>
        <p style="color:#6B7280; font-size:12px; margin:0 0 12px;">
            Lots that sold far above estimate &mdash; highest demand right now.
        </p>
        <table width="100%" cellpadding="0" cellspacing="0" style="font-size:13px; color:#1A1A1A;">
            <thead>
                <tr style="color:#6B7280; font-size:11px; text-transform:uppercase; letter-spacing:0.05em;">
                    <th style="padding:6px 8px;"></th>
                    <th style="padding:6px 8px; text-align:left;">Artist / Work</th>
                    <th style="padding:6px 8px; text-align:right;">Est &rarr; Sold</th>
                    <th style="padding:6px 8px; text-align:center;">Overbid</th>
                </tr>
            </thead>
            <tbody>
                {war_rows if war_rows else empty_msg}
            </tbody>
        </table>
    </div>

    <!-- Value Finds -->
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px; padding:16px; margin-bottom:20px;">
        <h2 style="color:#1A1A1A; font-size:16px; font-weight:600; margin:0 0 4px; border-bottom:2px solid #16A34A; padding-bottom:6px;">
            Value Finds
        </h2>
        <p style="color:#6B7280; font-size:12px; margin:0 0 12px;">
            Works by established artists that sold below their historical average &mdash; potential bargains.
        </p>
        <table width="100%" cellpadding="0" cellspacing="0" style="font-size:13px; color:#1A1A1A;">
            <thead>
                <tr style="color:#6B7280; font-size:11px; text-transform:uppercase; letter-spacing:0.05em;">
                    <th style="padding:6px 8px;"></th>
                    <th style="padding:6px 8px; text-align:left;">Artist / Work</th>
                    <th style="padding:6px 8px; text-align:right;">Price vs Avg</th>
                    <th style="padding:6px 8px; text-align:center;">Discount</th>
                </tr>
            </thead>
            <tbody>
                {value_rows if value_rows else empty_msg}
            </tbody>
        </table>
    </div>

    <!-- Market Movers -->
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px; padding:16px; margin-bottom:20px;">
        <h2 style="color:#1A1A1A; font-size:16px; font-weight:600; margin:0 0 4px; border-bottom:2px solid #F59E0B; padding-bottom:6px;">
            Market Movers
        </h2>
        <p style="color:#6B7280; font-size:12px; margin:0 0 12px;">
            Artists with the strongest auction track records by total sales volume.
        </p>
        <table width="100%" cellpadding="0" cellspacing="0" style="font-size:13px; color:#1A1A1A;">
            <thead>
                <tr style="color:#6B7280; font-size:11px; text-transform:uppercase; letter-spacing:0.05em;">
                    <th style="padding:6px 12px; text-align:left;">Artist</th>
                    <th style="padding:6px 12px; text-align:right;">Total Sales</th>
                    <th style="padding:6px 12px; text-align:right;">Lots</th>
                    <th style="padding:6px 12px; text-align:right;">Avg Price</th>
                    <th style="padding:6px 12px; text-align:center;">Overbid</th>
                </tr>
            </thead>
            <tbody>
                {mover_rows if mover_rows else empty_msg}
            </tbody>
        </table>
    </div>

    <!-- Art News -->
    {_build_news_section_html(news or [])}

    <!-- Footer -->
    <div style="text-align:center; padding:20px 0; border-top:1px solid #E5E7EB; margin-top:12px;">
        <p style="color:#6B7280; font-size:12px; margin:0 0 4px;">
            <a href="{BASE_URL}/app" style="color:#000000; text-decoration:none; font-weight:600;">Open Kanvas.ai</a>
            &nbsp;&middot;&nbsp;
            <a href="{BASE_URL}/app/market-map" style="color:#000000; text-decoration:none;">Art Index</a>
            &nbsp;&middot;&nbsp;
            <a href="{BASE_URL}/app/analytics" style="color:#000000; text-decoration:none;">Analytics</a>
            &nbsp;&middot;&nbsp;
            <a href="{BASE_URL}/app/profile" style="color:#000000; text-decoration:none;">Preferences</a>
        </p>
        <p style="color:#9CA3AF; font-size:11px; margin:0;">
            Predictive Labs Ltd &middot; You&rsquo;re receiving this because you signed up for Kanvas.ai alerts.
            {f'<br><a href="{unsubscribe_url}" style="color:#9CA3AF;">Unsubscribe</a>' if unsubscribe_url else ''}
        </p>
    </div>

</div>
</body>
</html>"""


def _build_news_section_html(news: list[dict]) -> str:
    if not news:
        return ""
    items_html = ""
    for n in news:
        title = (n.get("title") or "")[:80]
        url = n.get("url") or ""
        source = n.get("source") or ""
        snippet = (n.get("snippet") or "")[:120]
        if snippet and not snippet.endswith("."):
            snippet += "..."
        items_html += f"""
        <tr>
            <td style="padding:8px 12px; border-bottom:1px solid #E5E7EB;">
                <a href="{url}" style="color:#1A1A1A; text-decoration:none; font-size:13px; font-weight:500;" target="_blank">
                    {title}
                </a><br>
                <span style="font-size:11px; color:#6B7280;">{snippet}</span><br>
                <span style="font-size:10px; color:#9CA3AF;">{source}</span>
            </td>
        </tr>"""
    return f"""
    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px; padding:16px; margin-bottom:20px;">
        <h2 style="color:#1A1A1A; font-size:16px; font-weight:600; margin:0 0 4px; border-bottom:2px solid #6366F1; padding-bottom:6px;">
            Art Market News
        </h2>
        <p style="color:#6B7280; font-size:12px; margin:0 0 12px;">
            Latest from Estonian art media and international sources.
        </p>
        <table width="100%" cellpadding="0" cellspacing="0">
            <tbody>{items_html}</tbody>
        </table>
    </div>"""


def build_digest_text(bidding_wars: list[dict], value_finds: list[dict],
                      market_movers: list[dict], news: list[dict] | None = None,
                      unsubscribe_url: str = "") -> str:
    now = datetime.now()
    today = now.strftime("%A, %B %d, %Y")
    period = "Morning" if now.hour < 12 else ("Afternoon" if now.hour < 17 else "Evening")

    lines = [f"Kanvas.ai {period} Art Deals -- {today}", "=" * 48, ""]

    lines.append("BIDDING WARS")
    lines.append("-" * 48)
    for d in bidding_wars:
        overbid = float(d.get("overbid_pct") or 0)
        provider = _provider_label(d.get("auction_provider"))
        lines.append(f"  {d.get('author', 'Unknown')}")
        lines.append(f"    {(d.get('title') or 'Untitled')[:60]}")
        lines.append(f"    Est: {_fmt_eur(d.get('start_price'))} -> Sold: {_fmt_eur(d.get('end_price'))} (+{overbid:.0f}%)")
        lines.append(f"    {provider}")
        lines.append("")

    lines.append("VALUE FINDS")
    lines.append("-" * 48)
    for d in value_finds:
        discount = float(d.get("discount_pct") or 0)
        lines.append(f"  {d.get('author', 'Unknown')}")
        lines.append(f"    {(d.get('title') or 'Untitled')[:60]}")
        lines.append(f"    Sold: {_fmt_eur(d.get('end_price'))}  (avg {_fmt_eur(d.get('artist_avg'))}, -{discount:.0f}%)")
        lines.append("")

    lines.append("MARKET MOVERS")
    lines.append("-" * 48)
    for d in market_movers:
        overbid = d.get("avg_overbid_pct")
        overbid_str = f"+{float(overbid):.0f}%" if overbid else "--"
        lines.append(f"  {d.get('author', 'Unknown'):30s}  {_fmt_eur(d.get('total_sales'))}  {d.get('lot_count', 0)} lots  avg {_fmt_eur(d.get('avg_price'))}  {overbid_str}")
    lines.append("")

    if news:
        lines.append("ART MARKET NEWS")
        lines.append("-" * 48)
        for n in news:
            lines.append(f"  {n.get('title', '')[:70]}")
            lines.append(f"    {n.get('url', '')}")
            lines.append(f"    {n.get('source', '')}")
            lines.append("")

    lines.append("---")
    lines.append(f"{BASE_URL}/app")
    lines.append(f"Preferences: {BASE_URL}/app/profile")
    if unsubscribe_url:
        lines.append(f"Unsubscribe: {unsubscribe_url}")
    return "\n".join(lines)
