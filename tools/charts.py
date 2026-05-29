"""Plotly chart generation tools -- return __ARTIFACT__ payloads."""

from __future__ import annotations

import json
import logging

import pandas as pd
import plotly.express as px
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

CHART_LAYOUT = dict(
    paper_bgcolor="#FFFFFF", plot_bgcolor="#F5F5F5",
    font=dict(family="Inter, system-ui", color="#1A1A1A"),
    margin=dict(l=40, r=20, t=50, b=40),
    title=dict(font=dict(size=15)),
)


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
                       ELSE 0 END) as overbid_pct
            FROM kanvas.auction_lots
            {where}
            GROUP BY author, tech, category
            HAVING SUM(end_price) > 0
        """)
        rows = [dict(r._mapping) for r in db.execute(sql, params)]
        if not rows:
            return "No auction data available for treemap."

        df = pd.DataFrame(rows)
        import numpy as np
        midpoint = np.average(df["overbid_pct"], weights=df["total_sales"]) if len(df) > 0 else 0

        fig = px.treemap(
            df, path=["category", "tech", "author"],
            values="total_sales", color="overbid_pct",
            color_continuous_scale="RdBu",
            color_continuous_midpoint=midpoint,
            title=args.title,
        )
        fig.update_layout(**CHART_LAYOUT)
        fig.update_layout(margin=dict(t=30, l=0, r=0, b=0))

        artifact = {
            "kind": "chart",
            "title": args.title,
            "figure": json.loads(fig.to_json()),
        }
        return "__ARTIFACT__" + json.dumps(artifact)
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

        df = pd.DataFrame(rows)
        fig = px.area(
            df, x="year", y="avg_price", color="category",
            title=args.title, markers=True,
        )
        fig.update_layout(**CHART_LAYOUT)

        artifact = {
            "kind": "chart",
            "title": args.title,
            "figure": json.loads(fig.to_json()),
        }
        return "__ARTIFACT__" + json.dumps(artifact)
    finally:
        db.close()


treemap_chart = StructuredTool.from_function(
    func=_treemap, name="treemap_chart",
    description="Generate a treemap of artist sales colored by overbid percentage. Groups by category, technique, and artist.",
    args_schema=TreemapArgs,
)

price_trend_chart = StructuredTool.from_function(
    func=_price_trend, name="price_trend_chart",
    description="Generate an area chart showing price trends over time, optionally filtered by artist or category.",
    args_schema=PriceTrendArgs,
)
