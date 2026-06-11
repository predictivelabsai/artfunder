"""Art Index — interactive treemap + price trends with filters.

GET /app/market-map              → full-page Art Index with filters
GET /api/market-map/treemap      → Plotly JSON (supports ?country=&author=&medium=)
GET /api/market-map/trends       → Plotly JSON (supports ?country=&author=&medium=)
GET /api/market-map/filters      → available filter values
"""

from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd
import plotly.express as px
from fasthtml.common import (
    Html, Head, Body, Meta, Title, Link, Script, NotStr,
    Div, Span, H2, H3, P, A, Button, Select, Option, Label, Input,
)
from starlette.requests import Request
from starlette.responses import JSONResponse

from chat.layout import TAILWIND_CONFIG, _head
from chat.components import left_pane, signin_overlay
from chat.routes import _ensure_user, _list_sessions

log = logging.getLogger(__name__)

MIN_PRICE = 50  # filter out junk (books, porcelain, catalogs)

# ── Art-only filter ──────────────────────────────────────────────────
# The `category` column is ~99% empty, so art is detected from tech/title.
# A lot is dropped only if it matches the non-art list AND shows no fine-art
# medium signal — so a painting titled "Table" or "Mirror" is still kept.
# Scope (per product decision): keep paintings, works on paper, prints,
# sculpture and art-ceramics; drop furniture, jewelry, books, glass,
# clocks/watches, coins and carpets. Applied as Postgres POSIX regex.
_NONART_RE = (
    r"\y(furniture|mobel|mööbel|chair|stol|fatolj|fåtölj|tugitool|kapp|kummut|"
    r"cabinet|skap|skåp|byra|byrå|dresser|kommode|table|laud|bord|tisch|sofa|"
    r"soffa|sohva|diivan|desk|kirjutuslaud|shelf|riiul|bookcase|lamp|lampa|"
    r"lambi|leuchter|mirror|spegel|peegel|jewel|jewellery|jewelry|smycke|ehted|"
    r"sormus|sõrmus|brooch|brosch|prees|necklace|kaelakee|earring|korvarongas|"
    r"kõrvarõngas|orhange|örhänge|clock|klocka|watch|armbandsur|uhr|book|raamat|"
    r"bocker|böcker|bucher|bücher|coin|mynt|munt|münt|medal|medalj|munze|münze|"
    r"carpet|matta|vaip|rug|teppich|glass|glas|klaas)\y"
)
_ART_MEDIUM_RE = (
    r"(oil|õli|oli|olja|olje|öl|canvas|lõuend|louend|duk|pann|watercolo|akvarell|"
    r"akvarel|aquarell|gouache|guašš|guass|tempera|pastel|acrylic|akr[uü]l|akryl|"
    r"graphic|graafika|grafi|litho|lito|etch|eau.?forte|ofort|söövitus|soovitus|"
    r"gravüür|woodcut|linocut|drypoint|mezzotint|serigraph|monotype|aquatint|"
    r"mixed media|sega.?tehnika|segatehnika|\yink\y|tušš|tuss|pencil|pliiats|"
    r"charcoal|s[uü]si|paber|\ypaper\y|panel|pann[oa]|papp|maal|painting|gemälde|"
    r"maleri|drawing|joonistus|sketch|sculpt|skulptuur|bronze|pronks|marble|"
    r"marmor|terracotta|terrakota|porcelain|portselan|ceramic|keraamika|fajanss|"
    r"fa[iy]ence)"
)
# Substituted into WHERE so both the treemap and trends charts share it.
_ART_ONLY_SQL = (
    "(LOWER(COALESCE(tech,'') || ' ' || COALESCE(title,'')) !~* :nonart "
    "OR LOWER(COALESCE(tech,'') || ' ' || COALESCE(title,'')) ~* :artmedium)"
)

CHART_LAYOUT = dict(
    paper_bgcolor="#FFFFFF", plot_bgcolor="#F5F5F5",
    font=dict(family="Inter, system-ui", color="#1A1A1A"),
    margin=dict(l=40, r=20, t=50, b=40),
    title=dict(font=dict(size=15)),
)

COUNTRY_NAMES = {
    "EE": "Estonia", "LV": "Latvia", "LT": "Lithuania",
    "FI": "Finland", "SE": "Sweden", "DK": "Denmark",
    "NO": "Norway", "NL": "Netherlands", "GB": "United Kingdom",
}


def _build_where(params: dict) -> tuple[str, dict]:
    conditions = [f"end_price >= {MIN_PRICE}", "COALESCE(status, 'active') = 'active'"]
    bind = {}
    conditions.append(_ART_ONLY_SQL)
    bind["nonart"] = _NONART_RE
    bind["artmedium"] = _ART_MEDIUM_RE
    country = params.get("country", "").strip()
    if country and country != "ALL":
        conditions.append("COALESCE(country, 'EE') = :country")
        bind["country"] = country
    else:
        conditions.append("COALESCE(country, 'EE') != 'LV'")
    author = params.get("author", "").strip()
    if author:
        conditions.append("author ILIKE :author")
        bind["author"] = f"%{author}%"
    medium = params.get("medium", "").strip()
    if medium and medium != "ALL":
        conditions.append("COALESCE(NULLIF(tech,''),'Unknown') ILIKE :medium")
        bind["medium"] = f"%{medium}%"
    return "WHERE " + " AND ".join(conditions), bind


def _fetch_treemap_data(params: dict):
    from db import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        where, bind = _build_where(params)
        sql = text(f"""
            SELECT author,
                   COALESCE(NULLIF(tech, ''), 'Unknown') as tech,
                   COALESCE(NULLIF(category, ''), 'Other') as category,
                   SUM(end_price) as total_sales,
                   COUNT(*) as lot_count,
                   AVG(end_price)::int as avg_price,
                   CASE WHEN SUM(CASE WHEN start_price > 0 THEN 1 ELSE 0 END) > 0
                        THEN AVG(CASE WHEN start_price > 0
                             THEN (end_price - start_price)::float / start_price * 100
                             ELSE NULL END)
                        ELSE NULL END as overbid_pct
            FROM kanvas.auction_lots
            {where}
            GROUP BY author, COALESCE(NULLIF(tech, ''), 'Unknown'),
                     COALESCE(NULLIF(category, ''), 'Other')
            HAVING SUM(end_price) > 500
            ORDER BY total_sales DESC
            LIMIT 200
        """)
        rows = [dict(r._mapping) for r in db.execute(sql, bind)]
        return rows
    finally:
        db.close()


MEDIUM_BUCKET = """
    CASE
        WHEN LOWER(COALESCE(tech, '')) ~ '(oil|õli|öl|olje|olja|olie)' THEN 'Oil'
        WHEN LOWER(COALESCE(tech, '')) ~ '(waterc|aquar|akvar|akvarel)' THEN 'Watercolor'
        WHEN LOWER(COALESCE(tech, '')) ~ '(pastel)' THEN 'Pastel'
        WHEN LOWER(COALESCE(tech, '')) ~ '(litho|lito|litogra)' THEN 'Print'
        WHEN LOWER(COALESCE(tech, '')) ~ '(etch|engrav|woodcut|linocut|drypoint|dry.?point|mezzotint|eau.?forte|monotype|grafiika|grafi|serigraphy|screen)' THEN 'Print'
        WHEN LOWER(COALESCE(category, '')) = 'graphics' OR LOWER(COALESCE(tech, '')) ~ '(graphic)' THEN 'Print'
        WHEN LOWER(COALESCE(tech, '')) ~ '(mixed|sega|collage|install)' THEN 'Mixed Media'
        WHEN LOWER(COALESCE(tech, '')) ~ '(ink|tempera|gouache|guašš|pencil|charcoal|pliiats|tušš|pen )' THEN 'Works on Paper'
        WHEN COALESCE(NULLIF(tech, ''), '') = '' THEN 'Other'
        ELSE 'Other'
    END
"""


def _fetch_trend_data(params: dict):
    from db import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        where, bind = _build_where(params)
        where += " AND auction_date > 0"
        sql = text(f"""
            SELECT auction_date as year,
                   {MEDIUM_BUCKET} as category,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY end_price)::int as avg_price,
                   COUNT(*) as lots
            FROM kanvas.auction_lots
            {where}
            GROUP BY auction_date, {MEDIUM_BUCKET}
            ORDER BY auction_date
        """)
        rows = [dict(r._mapping) for r in db.execute(sql, bind)]
        return rows
    finally:
        db.close()


def _fetch_filter_options():
    from db import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        countries = [r[0] for r in db.execute(text(
            "SELECT DISTINCT COALESCE(country,'EE') FROM kanvas.auction_lots WHERE end_price >= 50 AND COALESCE(status,'active')='active' ORDER BY 1"
        ))]
        mediums = [r[0] for r in db.execute(text(
            """SELECT COALESCE(NULLIF(tech,''),'Unknown') as m, COUNT(*) as c
               FROM kanvas.auction_lots WHERE end_price >= 50 AND COALESCE(status,'active')='active'
               GROUP BY 1 HAVING COUNT(*) > 20 ORDER BY c DESC LIMIT 20"""
        ))]
        return {"countries": countries, "mediums": mediums}
    finally:
        db.close()


def _build_treemap_fig(rows, title="Top Artists — Total Sales"):
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df["total_sales"] = df["total_sales"].astype(float)
    df["avg_price"] = pd.to_numeric(df["avg_price"], errors="coerce").fillna(0)
    df["overbid_pct"] = pd.to_numeric(df["overbid_pct"], errors="coerce")

    has_overbid = df["overbid_pct"].notna().sum() > len(df) * 0.3
    if has_overbid:
        df["overbid_pct"] = df["overbid_pct"].fillna(0)
        color_col = "overbid_pct"
        midpoint = np.average(df[color_col], weights=df["total_sales"])
        color_scale = "RdBu"
        title_suffix = " by Overbid %"
    else:
        color_col = "avg_price"
        midpoint = df[color_col].median()
        color_scale = "Viridis"
        title_suffix = " by Avg Price"

    fig = px.treemap(
        df, path=["category", "tech", "author"],
        values="total_sales", color=color_col,
        color_continuous_scale=color_scale,
        color_continuous_midpoint=midpoint,
        title=title + title_suffix,
    )
    fig.update_layout(**CHART_LAYOUT)
    fig.update_layout(margin=dict(t=30, l=0, r=0, b=0))
    return fig


MEDIUM_COLORS = {
    "Oil": "#1A1A1A",
    "Watercolor": "#3B82F6",
    "Print": "#8B5CF6",
    "Pastel": "#EC4899",
    "Mixed Media": "#F59E0B",
    "Works on Paper": "#10B981",
    "Other": "#9CA3AF",
}


def _build_trend_fig(rows, title="Price Trends by Medium"):
    if not rows:
        return None
    df = pd.DataFrame(rows)
    for col in ["avg_price", "lots"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df[df["lots"] >= 3]
    fig = px.line(
        df, x="year", y="avg_price", color="category",
        title=title, markers=True,
        color_discrete_map=MEDIUM_COLORS,
        labels={"avg_price": "Median Price (EUR)", "year": "Year", "category": "Medium"},
    )
    fig.update_layout(**CHART_LAYOUT)
    fig.update_traces(line=dict(width=2))
    fig.update_xaxes(dtick=1)
    return fig


def register_market_map_routes(rt):

    @rt("/api/market-map/treemap")
    def treemap_json(request: Request):
        params = dict(request.query_params)
        if not params.get("country"):
            params["country"] = "EE"
        rows = _fetch_treemap_data(params)
        fig = _build_treemap_fig(rows)
        if not fig:
            return JSONResponse({"error": "No data"})
        return JSONResponse(json.loads(fig.to_json()))

    @rt("/api/market-map/trends")
    def trends_json(request: Request):
        params = dict(request.query_params)
        if not params.get("country"):
            params["country"] = "EE"
        rows = _fetch_trend_data(params)
        fig = _build_trend_fig(rows)
        if not fig:
            return JSONResponse({"error": "No data"})
        return JSONResponse(json.loads(fig.to_json()))

    @rt("/api/market-map/filters")
    def filter_options():
        return JSONResponse(_fetch_filter_options())

    @rt("/app/market-map")
    def market_map_page(sess):
        uid, email = _ensure_user(sess)
        sessions = _list_sessions(uid) if uid else []

        country_options = [
            Option("Estonia", value="EE", selected=True),
            Option("Finland", value="FI"),
            Option("Sweden", value="SE"),
            Option("Norway", value="NO"),
            Option("Denmark", value="DK"),
            Option("Netherlands", value="NL"),
            Option("United Kingdom", value="GB"),
            Option("── All Countries ──", value="ALL"),
        ]

        body = Body(
            signin_overlay(),
            Div(id="left-overlay", cls="left-overlay", onclick="toggleLeftPane()"),
            left_pane(user_email=email, sessions=sessions, current_sid=""),
            Div(
                Div(
                    Div(
                        Button("=", cls="mobile-menu-btn", onclick="toggleLeftPane()"),
                        Span("Art Index", cls="chat-header-title"),
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
                        H2("Art Index", cls="text-xl font-display font-bold mb-1"),
                        P("Interactive treemap of artist sales. Larger blocks = higher total sales. Color = overbid percentage.",
                          cls="text-sm text-gray-500 mb-4"),
                        cls="mb-2",
                    ),
                    # ── Filters ──
                    Div(
                        Div(
                            Label("Country", cls="text-xs text-gray-400 block mb-1"),
                            Select(*country_options, id="filter-country",
                                   cls="text-sm border border-gray-200 rounded px-2 py-1.5 bg-white",
                                   onchange="applyFilters()"),
                            cls="flex flex-col",
                        ),
                        Div(
                            Label("Artist", cls="text-xs text-gray-400 block mb-1"),
                            Input(type="text", id="filter-author", placeholder="Search artist...",
                                  cls="text-sm border border-gray-200 rounded px-2 py-1.5 w-40",
                                  onkeydown="if(event.key==='Enter')applyFilters()"),
                            cls="flex flex-col",
                        ),
                        Div(
                            Label("Medium", cls="text-xs text-gray-400 block mb-1"),
                            Select(
                                Option("All", value="ALL"),
                                Option("Oil on canvas", value="Oil"),
                                Option("Watercolor", value="Watercolor"),
                                Option("Graphics", value="Graphics"),
                                Option("Lithograph", value="Lithograph"),
                                Option("Pastel", value="Pastel"),
                                Option("Mixed media", value="Mixed"),
                                id="filter-medium",
                                cls="text-sm border border-gray-200 rounded px-2 py-1.5 bg-white",
                                onchange="applyFilters()"),
                            cls="flex flex-col",
                        ),
                        Button("Apply", onclick="applyFilters()",
                               cls="self-end px-4 py-1.5 text-sm bg-black text-white rounded cursor-pointer border-none hover:bg-gray-800"),
                        cls="flex flex-wrap items-end gap-4 mb-6 p-3 bg-gray-50 rounded-lg border border-gray-100",
                    ),
                    Div(id="treemap-chart", style="width:100%;min-height:500px;"),
                    Div(
                        H3("Price Trends", cls="text-lg font-display font-bold mt-8 mb-1"),
                        P("Median end price over time by medium. Same filters apply.",
                          cls="text-sm text-gray-500 mb-4"),
                    ),
                    Div(id="trend-chart", style="width:100%;min-height:400px;"),
                    cls="px-6 py-4 overflow-y-auto flex-1",
                ),
                cls="center-pane",
            ),
            Script(NotStr("""
                function getFilterParams() {
                    const country = document.getElementById('filter-country').value;
                    const author = document.getElementById('filter-author').value.trim();
                    const medium = document.getElementById('filter-medium').value;
                    const params = new URLSearchParams();
                    if (country) params.set('country', country);
                    if (author) params.set('author', author);
                    if (medium && medium !== 'ALL') params.set('medium', medium);
                    return params.toString();
                }

                async function applyFilters() {
                    const qs = getFilterParams();
                    const t = await fetch('/api/market-map/treemap?' + qs);
                    const tData = await t.json();
                    if (tData.data) Plotly.newPlot('treemap-chart', tData.data, tData.layout, {responsive: true});
                    else document.getElementById('treemap-chart').innerHTML = '<p style="color:#888;padding:2rem">No data for these filters.</p>';

                    const r = await fetch('/api/market-map/trends?' + qs);
                    const rData = await r.json();
                    if (rData.data) Plotly.newPlot('trend-chart', rData.data, rData.layout, {responsive: true});
                    else document.getElementById('trend-chart').innerHTML = '<p style="color:#888;padding:2rem">No trend data.</p>';
                }

                applyFilters();
            """)),
            Script(src="/static/chat.js"),
            cls="bg-white text-ink font-sans antialiased app pane-closed",
        )
        return Html(_head("Art Index"), body)
