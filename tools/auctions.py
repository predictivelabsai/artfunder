"""Auction lot query tools for Estonian auction data."""

from __future__ import annotations

import json
import logging
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


def _get_db():
    from db import SessionLocal
    return SessionLocal()


class SearchLotsArgs(BaseModel):
    author: Optional[str] = Field(default=None, description="Artist name to search for.")
    category: Optional[str] = Field(default=None, description="Art category (e.g. Oil paint, Other paint).")
    tech: Optional[str] = Field(default=None, description="Technique (e.g. Oil on canvas, Watercolour).")
    provider: Optional[str] = Field(default=None, description="Auction provider: allee or haus.")
    min_price: Optional[int] = Field(default=None, description="Minimum end price in EUR.")
    max_price: Optional[int] = Field(default=None, description="Maximum end price in EUR.")
    limit: int = Field(default=20, ge=1, le=100)


def _search_lots(**kw) -> str:
    args = SearchLotsArgs(**kw)
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
        if args.tech:
            conditions.append("tech ILIKE :tech")
            params["tech"] = f"%{args.tech}%"
        if args.provider:
            conditions.append("auction_provider = :provider")
            params["provider"] = args.provider
        if args.min_price is not None:
            conditions.append("end_price >= :min_price")
            params["min_price"] = args.min_price
        if args.max_price is not None:
            conditions.append("end_price <= :max_price")
            params["max_price"] = args.max_price

        where = " AND ".join(conditions) if conditions else "TRUE"
        params["lim"] = args.limit
        sql = text(f"SELECT * FROM kanvas.auction_lots WHERE {where} ORDER BY end_price DESC LIMIT :lim")
        rows = [dict(r._mapping) for r in db.execute(sql, params)]

        if not rows:
            return "No auction lots found matching the criteria."

        for r in rows:
            r.pop("created_at", None)

        artifact = {
            "kind": "table",
            "title": f"Auction Lots ({len(rows)} results)",
            "columns": ["id", "auction_date", "author", "start_price", "end_price", "year", "tech", "category", "auction_provider"],
            "rows": rows,
        }
        return "__ARTIFACT__" + json.dumps(artifact, default=str)
    finally:
        db.close()


class ArtistHistoryArgs(BaseModel):
    author: str = Field(description="Artist name to look up auction history for.")


def _artist_auction_history(**kw) -> str:
    args = ArtistHistoryArgs(**kw)
    from sqlalchemy import text
    db = _get_db()
    try:
        sql = text("""
            SELECT author,
                   COUNT(*) as lots_sold,
                   SUM(end_price) as total_sales,
                   AVG(end_price)::int as avg_price,
                   MAX(end_price) as max_price,
                   MIN(end_price) as min_price,
                   AVG(CASE WHEN start_price > 0
                       THEN (end_price - start_price)::float / start_price * 100
                       ELSE 0 END)::int as avg_overbid_pct
            FROM kanvas.auction_lots
            WHERE author ILIKE :author
            GROUP BY author
        """)
        rows = [dict(r._mapping) for r in db.execute(sql, {"author": f"%{args.author}%"})]
        if not rows:
            return f"No auction history found for '{args.author}'."
        return json.dumps(rows, default=str)
    finally:
        db.close()


search_auction_lots = StructuredTool.from_function(
    func=_search_lots, name="search_auction_lots",
    description="Search Estonian auction lot data by artist, category, technique, provider, and price range.",
    args_schema=SearchLotsArgs,
)

artist_auction_history = StructuredTool.from_function(
    func=_artist_auction_history, name="artist_auction_history",
    description="Get aggregated auction statistics for an artist: total sales, average price, overbid percentage.",
    args_schema=ArtistHistoryArgs,
)
