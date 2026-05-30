"""Prebuilt market map — server-rendered Plotly treemap + area chart.

GET /app/market-map         → full-page treemap + price trends
GET /api/market-map/treemap → Plotly JSON for embedding
GET /api/market-map/trends  → Plotly JSON for price trends
"""

from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd
import plotly.express as px
from fasthtml.common import (
    Html, Head, Body, Meta, Title, Link, Script, NotStr,
    Div, Span, H2, H3, P, A, Button,
)
from starlette.responses import JSONResponse

from chat.layout import TAILWIND_CONFIG, _head
from chat.components import left_pane, signin_overlay
from chat.routes import _ensure_user, _list_sessions

log = logging.getLogger(__name__)

CHART_LAYOUT = dict(
    paper_bgcolor="#FFFFFF", plot_bgcolor="#F5F5F5",
    font=dict(family="Inter, system-ui", color="#1A1A1A"),
    margin=dict(l=40, r=20, t=50, b=40),
    title=dict(font=dict(size=15)),
)


def _fetch_treemap_data(provider=None):
    from db import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        where = "WHERE end_price > 0"
        params = {}
        if provider:
            where += " AND auction_provider = :provider"
            params["provider"] = provider
        sql = text(f"""
            SELECT author,
                   COALESCE(NULLIF(tech, ''), 'Unknown') as tech,
                   COALESCE(NULLIF(category, ''), 'Other') as category,
                   SUM(end_price) as total_sales,
                   AVG(CASE WHEN start_price > 0
                       THEN (end_price - start_price)::float / start_price * 100
                       ELSE 0 END) as overbid_pct
            FROM kanvas.auction_lots
            {where}
            GROUP BY author, COALESCE(NULLIF(tech, ''), 'Unknown'),
                     COALESCE(NULLIF(category, ''), 'Other')
            HAVING SUM(end_price) > 500
            ORDER BY total_sales DESC
            LIMIT 200
        """)
        rows = [dict(r._mapping) for r in db.execute(sql, params)]
        return rows
    finally:
        db.close()


def _fetch_trend_data(author=None, category=None):
    from db import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        conditions = ["end_price > 0", "auction_date > 0"]
        params = {}
        if author:
            conditions.append("author ILIKE :author")
            params["author"] = f"%{author}%"
        if category:
            conditions.append("category ILIKE :category")
            params["category"] = f"%{category}%"
        where = "WHERE " + " AND ".join(conditions)
        sql = text(f"""
            SELECT auction_date as year,
                   COALESCE(NULLIF(category, ''), COALESCE(NULLIF(tech, ''), 'Other')) as category,
                   AVG(end_price)::int as avg_price,
                   COUNT(*) as lots
            FROM kanvas.auction_lots
            {where}
            GROUP BY auction_date,
                     COALESCE(NULLIF(category, ''), COALESCE(NULLIF(tech, ''), 'Other'))
            ORDER BY auction_date
        """)
        rows = [dict(r._mapping) for r in db.execute(sql, params)]
        return rows
    finally:
        db.close()


def _build_treemap_fig(rows, title="Top Selling Artists — Total Sales by Overbid %"):
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df["total_sales"] = df["total_sales"].astype(float)
    df["overbid_pct"] = df["overbid_pct"].astype(float)
    midpoint = np.average(df["overbid_pct"], weights=df["total_sales"]) if len(df) > 0 else 0

    fig = px.treemap(
        df, path=["category", "tech", "author"],
        values="total_sales", color="overbid_pct",
        color_continuous_scale="RdBu",
        color_continuous_midpoint=midpoint,
        title=title,
    )
    fig.update_layout(**CHART_LAYOUT)
    fig.update_layout(margin=dict(t=30, l=0, r=0, b=0))
    return fig


def _build_trend_fig(rows, title="Price Trends by Category"):
    if not rows:
        return None
    df = pd.DataFrame(rows)
    for col in ["avg_price", "lots"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    fig = px.area(
        df, x="year", y="avg_price", color="category",
        title=title, markers=True,
    )
    fig.update_layout(**CHART_LAYOUT)
    return fig


def register_market_map_routes(rt):

    @rt("/api/market-map/treemap")
    def treemap_json():
        rows = _fetch_treemap_data()
        fig = _build_treemap_fig(rows)
        if not fig:
            return JSONResponse({"error": "No data"})
        return JSONResponse(json.loads(fig.to_json()))

    @rt("/api/market-map/trends")
    def trends_json():
        rows = _fetch_trend_data()
        fig = _build_trend_fig(rows)
        if not fig:
            return JSONResponse({"error": "No data"})
        return JSONResponse(json.loads(fig.to_json()))

    @rt("/app/market-map")
    def market_map_page(sess):
        uid, email = _ensure_user(sess)
        sessions = _list_sessions(uid) if uid else []

        body = Body(
            signin_overlay(),
            Div(id="left-overlay", cls="left-overlay", onclick="toggleLeftPane()"),
            left_pane(user_email=email, sessions=sessions, current_sid=""),
            Div(
                Div(
                    Div(
                        Button("=", cls="mobile-menu-btn", onclick="toggleLeftPane()"),
                        Span("Market Map", cls="chat-header-title"),
                        Span("--", cls="chat-header-dot"),
                        Span("Estonian Art Market", cls="chat-header-agent"),
                        cls="chat-header-left",
                    ),
                    Div(
                        A("Back to chat", href="/app", cls="header-action-btn"),
                        A("Analytics", href="/app/analytics", cls="header-action-btn"),
                        cls="chat-header-actions",
                    ),
                    cls="chat-header",
                ),
                Div(
                    Div(
                        H2("Estonian Art Market Map", cls="text-xl font-display font-bold mb-1"),
                        P("Interactive treemap of artist sales colored by overbid percentage. Larger blocks = higher total sales. Blue = below-average overbid, Red = above-average.",
                          cls="text-sm text-gray-500 mb-4"),
                        cls="mb-2",
                    ),
                    Div(id="treemap-chart", style="width:100%;min-height:500px;"),
                    Div(
                        H3("Price Trends by Category", cls="text-lg font-display font-bold mt-8 mb-1"),
                        P("Average end price over time, grouped by art category.",
                          cls="text-sm text-gray-500 mb-4"),
                    ),
                    Div(id="trend-chart", style="width:100%;min-height:400px;"),
                    cls="px-6 py-4 overflow-y-auto flex-1",
                ),
                cls="center-pane",
            ),
            Script(NotStr("""
                async function loadCharts() {
                    const t = await fetch('/api/market-map/treemap');
                    const tData = await t.json();
                    if (tData.data) Plotly.newPlot('treemap-chart', tData.data, tData.layout, {responsive: true});

                    const r = await fetch('/api/market-map/trends');
                    const rData = await r.json();
                    if (rData.data) Plotly.newPlot('trend-chart', rData.data, rData.layout, {responsive: true});
                }
                loadCharts();
            """)),
            Script(src="/static/chat.js"),
            cls="bg-white text-ink font-sans antialiased app pane-closed",
        )
        return Html(_head("Market Map"), body)
