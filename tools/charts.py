"""Chart tools — return short summaries for the LLM, reference prebuilt market map."""

from __future__ import annotations

import logging

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


def _get_db():
    from db import SessionLocal
    return SessionLocal()


class TreemapArgs(BaseModel):
    title: str = Field(default="Artist Sales Treemap", description="Chart title.")
    provider: str | None = Field(default=None, description="Filter by auction provider: allee or haus.")


def _treemap(**kw) -> str:
    args = TreemapArgs(**kw)
    from sqlalchemy import text
    db = _get_db()
    try:
        where = "WHERE auction_provider = :provider" if args.provider else ""
        params = {"provider": args.provider} if args.provider else {}
        sql = text(f"""
            SELECT author, tech, category,
                   SUM(end_price) as total_sales,
                   AVG(CASE WHEN start_price > 0
                       THEN (end_price - start_price)::float / start_price * 100
                       ELSE 0 END)::int as overbid_pct
            FROM kanvas.auction_lots
            {where}
            GROUP BY author, tech, category
            HAVING SUM(end_price) > 0
            ORDER BY total_sales DESC
            LIMIT 15
        """)
        rows = [dict(r._mapping) for r in db.execute(sql, params)]
        if not rows:
            return "No auction data available for treemap."

        top = rows[:10]
        summary_lines = [f"- {r['author'].strip()}: EUR {int(r['total_sales']):,} total sales, {int(r['overbid_pct'])}% avg overbid ({r['tech']})" for r in top]
        summary = "\n".join(summary_lines)

        return (
            f"Treemap chart '{args.title}' is available at /app/market-map with {len(rows)} artist groups.\n\n"
            f"Top 10 artists by total sales:\n{summary}\n\n"
            f"Direct the user to /app/market-map for the interactive treemap visualization."
        )
    finally:
        db.close()


class PriceTrendArgs(BaseModel):
    author: str | None = Field(default=None, description="Artist name to filter by.")
    category: str | None = Field(default=None, description="Art category to filter by.")
    title: str = Field(default="Price Trends", description="Chart title.")


def _price_trend(**kw) -> str:
    args = PriceTrendArgs(**kw)
    from sqlalchemy import text
    db = _get_db()
    try:
        conditions = []
        params = {}
        if args.author:
            conditions.append("author ILIKE :author")
            params["author"] = f"%{args.author}%"
        if args.category:
            conditions.append("category ILIKE :category")
            params["category"] = f"%{args.category}%"
        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        sql = text(f"""
            SELECT auction_date as year, category,
                   AVG(end_price)::int as avg_price,
                   COUNT(*) as lots
            FROM kanvas.auction_lots
            {where}
            GROUP BY auction_date, category
            ORDER BY auction_date
        """)
        rows = [dict(r._mapping) for r in db.execute(sql, params)]
        if not rows:
            return "No data available for price trend chart."

        summary_lines = [f"- {r['year']} {r['category']}: EUR {int(r['avg_price']):,} avg ({int(r['lots'])} lots)" for r in rows[:12]]
        summary = "\n".join(summary_lines)

        return (
            f"Price trend data for '{args.title}':\n{summary}\n\n"
            f"The interactive chart is available at /app/market-map."
        )
    finally:
        db.close()


treemap_chart = StructuredTool.from_function(
    func=_treemap, name="treemap_chart",
    description="Look up artist sales data grouped by category, technique, and artist. Returns top sellers with overbid percentages. The full interactive treemap is at /app/market-map.",
    args_schema=TreemapArgs,
)

price_trend_chart = StructuredTool.from_function(
    func=_price_trend, name="price_trend_chart",
    description="Look up price trends over time, optionally filtered by artist or category. The full interactive chart is at /app/market-map.",
    args_schema=PriceTrendArgs,
)
