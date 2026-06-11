"""Historical price-index & ROI analytics over kanvas.auction_lots.

Auction data here is annual (`auction_date` = sale year, 1998-2026) and the lots
are heterogeneous, so we build a per-year MEDIAN end-price index for a segment
(artist / category / medium / country / creation-period) across the ENTIRE
history (all record statuses, sold lots only), then derive CAGR + total return
with sample-size and dispersion confidence guardrails.

A single artist is usually too thin for a reliable index (a year may hold one
lot), so artist queries also return a broader segment as a proxy anchor. The
medium classifier (MEDIUM_BUCKET) and the art-only filter are shared with the
Art Index charts via tools.art_filter.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from tools.art_filter import ART_ONLY_INLINE, MEDIUM_BUCKET, MEDIUM_BUCKETS

log = logging.getLogger(__name__)


def _get_db():
    from db import SessionLocal
    return SessionLocal()


# A year counts as an index point only at >= this many sold lots; a segment
# needs >= MIN_QUALIFYING_YEARS such points to earn "high" confidence.
MIN_N_PER_YEAR = 8
MIN_QUALIFYING_YEARS = 3

# Creation-period -> artwork creation-year bounds (the `year` column).
PERIOD_BOUNDS = {
    "classical": (None, 1945),     # up to WWII — Mägi-era modernists and earlier
    "modern": (1945, 1990),
    "contemporary": (1990, None),
}

_MEDIUM_ALIASES = {
    "oil": "Oil", "oils": "Oil", "oil on canvas": "Oil", "oil painting": "Oil",
    "watercolor": "Watercolor", "watercolour": "Watercolor", "aquarelle": "Watercolor",
    "pastel": "Pastel",
    "print": "Print", "prints": "Print", "graphics": "Print", "graphic": "Print",
    "lithograph": "Print", "etching": "Print",
    "mixed media": "Mixed Media", "mixed": "Mixed Media",
    "works on paper": "Works on Paper", "drawing": "Works on Paper", "ink": "Works on Paper",
}


def _normalize_medium(medium: Optional[str]) -> Optional[str]:
    """Map free-text medium input to a MEDIUM_BUCKET label, or None."""
    if not medium:
        return None
    m = medium.strip()
    if m in MEDIUM_BUCKETS:
        return m
    low = m.lower()
    if low in _MEDIUM_ALIASES:
        return _MEDIUM_ALIASES[low]
    for key, label in _MEDIUM_ALIASES.items():
        if key in low:
            return label
    return None


def _build_segment_where(author=None, category=None, medium=None, country=None,
                         period=None, start_year=None, end_year=None):
    """Build a WHERE body (no 'WHERE' keyword) + bind dict for sold art lots."""
    conds = ["end_price > 0", "auction_date > 0", ART_ONLY_INLINE]
    binds: dict = {}
    if author:
        conds.append("author ILIKE :author")
        binds["author"] = f"%{author}%"
    if category:
        conds.append("category ILIKE :category")
        binds["category"] = f"%{category}%"
    norm_medium = _normalize_medium(medium)
    if norm_medium:
        conds.append(f"({MEDIUM_BUCKET}) = :medium")
        binds["medium"] = norm_medium
    if country:
        conds.append("COALESCE(country, 'EE') = :country")
        binds["country"] = country.upper()
    if period and period.lower() in PERIOD_BOUNDS:
        lo, hi = PERIOD_BOUNDS[period.lower()]
        if lo is not None:
            conds.append("year >= :pyr_lo")
            binds["pyr_lo"] = lo
        if hi is not None:
            conds.append("year <= :pyr_hi")
            binds["pyr_hi"] = hi
    if start_year:
        conds.append("auction_date >= :sy")
        binds["sy"] = int(start_year)
    if end_year:
        conds.append("auction_date <= :ey")
        binds["ey"] = int(end_year)
    return " AND ".join(conds), binds


def build_price_index(**filters) -> list[dict]:
    """Per-year median/mean end-price index for a segment, across all history."""
    from sqlalchemy import text
    where, binds = _build_segment_where(**filters)
    db = _get_db()
    try:
        sql = text(f"""
            SELECT auction_date AS year,
                   COUNT(*) AS n,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY end_price)::int AS median,
                   AVG(end_price)::int AS mean,
                   PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY end_price)::int AS q1,
                   PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY end_price)::int AS q3
            FROM kanvas.auction_lots
            WHERE {where}
            GROUP BY auction_date
            ORDER BY auction_date
        """)
        return [dict(r._mapping) for r in db.execute(sql, binds)]
    finally:
        db.close()


def compute_performance(index: list[dict], min_n: int = MIN_N_PER_YEAR,
                        min_years: int = MIN_QUALIFYING_YEARS) -> dict:
    """Derive CAGR + total return + confidence from a price index.

    Uses the median series between the first and last *qualifying* years (years
    with >= min_n sold lots). Falls back to all priced years with a low-confidence
    flag when too few years qualify.
    """
    n_total = sum(r["n"] for r in index)
    qualifying = [r for r in index if r["n"] >= min_n and r["median"]]

    if len(qualifying) >= 2:
        first, last = qualifying[0], qualifying[-1]
        disp = [(r["q3"] - r["q1"]) / r["median"]
                for r in qualifying if r.get("q1") and r.get("q3") and r["median"]]
        avg_disp = sum(disp) / len(disp) if disp else None
        if len(qualifying) >= min_years and (avg_disp is None or avg_disp < 1.5):
            conf = "high"
        else:
            conf = "medium"
        reason = f"{len(qualifying)} qualifying years (>= {min_n} sold lots/yr)."
    else:
        priced = [r for r in index if r["median"]]
        if len(priced) < 2:
            return {"ok": False, "confidence": "none", "n_total": n_total,
                    "reason": "Too few sold lots to compute a reliable index."}
        first, last = priced[0], priced[-1]
        conf = "low"
        reason = (f"Only {len(qualifying)} year(s) meet the sample threshold "
                  f"(>= {min_n} lots/yr); figure is indicative only.")

    years = last["year"] - first["year"]
    sv, ev = first["median"], last["median"]
    if years <= 0 or not sv:
        return {"ok": False, "confidence": "none", "n_total": n_total,
                "reason": "Insufficient time span between data points."}

    total_return = (ev - sv) / sv * 100
    cagr = ((ev / sv) ** (1 / years) - 1) * 100
    return {
        "ok": True, "confidence": conf, "reason": reason,
        "start_year": first["year"], "end_year": last["year"], "years": years,
        "start_value": sv, "end_value": ev,
        "cagr": round(cagr, 1), "total_return": round(total_return, 1),
        "n_total": n_total, "qualifying_years": len(qualifying),
    }


def _artist_dominant_segment(author: str) -> Optional[dict]:
    """The artist's most common (country, medium) — used to pick a proxy segment."""
    from sqlalchemy import text
    db = _get_db()
    try:
        sql = text(f"""
            SELECT COALESCE(country, 'EE') AS country, ({MEDIUM_BUCKET}) AS medium, COUNT(*) AS n
            FROM kanvas.auction_lots
            WHERE author ILIKE :a AND end_price > 0 AND auction_date > 0
            GROUP BY 1, 2 ORDER BY n DESC LIMIT 1
        """)
        r = db.execute(sql, {"a": f"%{author}%"}).fetchone()
        return {"country": r[0], "medium": r[1]} if r else None
    finally:
        db.close()


_COUNTRY_NAMES = {"EE": "Estonian", "LV": "Latvian", "LT": "Lithuanian",
                  "FI": "Finnish", "SE": "Swedish", "NO": "Norwegian", "DK": "Danish"}


def segment_proxy_for_artist(author: str) -> Optional[dict]:
    """A broader segment (country + medium) for an artist, as a reliable anchor."""
    seg = _artist_dominant_segment(author)
    if not seg:
        return None
    country = seg.get("country") or "EE"
    medium = seg.get("medium")
    if medium in (None, "Other"):
        medium = None
    idx = build_price_index(country=country, medium=medium)
    perf = compute_performance(idx)
    label = f"{_COUNTRY_NAMES.get(country, country)} {(medium or 'art').lower()}"
    return {"label": label, "country": country, "medium": medium,
            "performance": perf, "index": idx}


# ── Text formatting (for the LLM to narrate) ─────────────────────────

def _fmt_index_table(index: list[dict], max_rows: int = 14) -> str:
    rows = [r for r in index if r["median"]]
    if len(rows) > max_rows:
        rows = rows[-max_rows:]
    return "\n".join(f"  {r['year']}: EUR {int(r['median']):,} (n={r['n']})" for r in rows)


def _fmt_performance(label: str, perf: dict, index: list[dict]) -> str:
    if not perf.get("ok"):
        return f"{label}: {perf.get('reason', 'no reliable performance figure available.')}"
    arrow = "+" if perf["cagr"] >= 0 else ""
    return (
        f"{label} — median price index ({perf['start_year']}–{perf['end_year']}):\n"
        f"- CAGR: {arrow}{perf['cagr']}%/yr over {perf['years']} years "
        f"({perf['start_year']} EUR {perf['start_value']:,} → {perf['end_year']} EUR {perf['end_value']:,})\n"
        f"- Total return: {('+' if perf['total_return'] >= 0 else '')}{perf['total_return']}%\n"
        f"- Based on {perf['n_total']} sold lots; confidence: {perf['confidence']} ({perf['reason']})\n"
        f"Per-year median (sold lots):\n{_fmt_index_table(index)}"
    )


# ── Tools ────────────────────────────────────────────────────────────

class PerformanceArgs(BaseModel):
    scope: str = Field(default="segment", description="'artist' for one artist, or 'segment' for a category/medium/country group.")
    author: Optional[str] = Field(default=None, description="Artist name (required when scope='artist').")
    category: Optional[str] = Field(default=None, description="Art category filter (e.g. 'Oil paint').")
    medium: Optional[str] = Field(default=None, description="Medium: Oil, Watercolor, Print, Pastel, Mixed Media, Works on Paper (free text like 'oil painting' is accepted).")
    country: Optional[str] = Field(default=None, description="Two-letter country code, e.g. EE, FI, SE.")
    period: Optional[str] = Field(default=None, description="Creation period: 'classical' (<=1945), 'modern' (1945-1990), 'contemporary' (>=1990).")
    start_year: Optional[int] = Field(default=None, description="Earliest sale year to include.")
    end_year: Optional[int] = Field(default=None, description="Latest sale year to include.")
    lookback_years: Optional[int] = Field(default=None, description="Restrict to the most recent N years (e.g. 5 for 'invested 5 years ago'). Overrides start_year.")


def _apply_window(index: list[dict], lookback_years: Optional[int]) -> list[dict]:
    """Keep only the most recent `lookback_years` of the index (by available data)."""
    if not lookback_years or not index:
        return index
    max_year = max(r["year"] for r in index)
    cutoff = max_year - int(lookback_years)
    return [r for r in index if r["year"] >= cutoff]


def _market_performance(**kw) -> str:
    args = PerformanceArgs(**kw)
    if args.scope == "artist":
        if not args.author:
            return "Provide an artist name for scope='artist'."
        idx = _apply_window(build_price_index(author=args.author, start_year=args.start_year, end_year=args.end_year), args.lookback_years)
        perf = compute_performance(idx)
        out = [_fmt_performance(args.author, perf, idx)]
        if perf.get("confidence") in ("low", "none", "medium"):
            out.append(
                "\n⚠ Single-artist auction data is sparse and lumpy (a year may hold "
                "only a handful of lots and is swung by whether a major work sold), so the "
                "figure above is indicative. For a steadier read, anchor to the artist's "
                "broader market segment:"
            )
            proxy = segment_proxy_for_artist(args.author)
            if proxy:
                pidx = _apply_window(proxy["index"], args.lookback_years)
                out.append("\n" + _fmt_performance(f"Segment proxy — {proxy['label']}",
                                                    compute_performance(pidx), pidx))
        return "\n".join(out)

    # segment scope
    label_bits = []
    if args.period:
        label_bits.append(args.period.capitalize())
    if args.country:
        label_bits.append(_COUNTRY_NAMES.get(args.country.upper(), args.country.upper()))
    norm_medium = _normalize_medium(args.medium)
    label_bits.append((norm_medium or args.category or "art").lower() if label_bits else (norm_medium or args.category or "All art"))
    label = " ".join(label_bits).strip() or "Segment"
    idx = _apply_window(build_price_index(category=args.category, medium=args.medium, country=args.country,
                                          period=args.period, start_year=args.start_year, end_year=args.end_year),
                        args.lookback_years)
    perf = compute_performance(idx)
    return _fmt_performance(label, perf, idx)


def _performance_chart(**kw) -> str:
    args = PerformanceArgs(**kw)
    if args.scope == "artist" and args.author:
        idx = _apply_window(build_price_index(author=args.author, start_year=args.start_year, end_year=args.end_year), args.lookback_years)
        title = f"{args.author} — median price index"
    else:
        idx = _apply_window(build_price_index(category=args.category, medium=args.medium, country=args.country,
                                              period=args.period, start_year=args.start_year, end_year=args.end_year),
                            args.lookback_years)
        bits = [b for b in [args.period, args.country, _normalize_medium(args.medium) or args.category] if b]
        title = (" ".join(str(b) for b in bits) or "Segment") + " — median price index"

    pts = [r for r in idx if r["median"]]
    if len(pts) < 2:
        return "Not enough sold lots over time to chart a price index for this selection."
    years = [int(r["year"]) for r in pts]
    medians = [int(r["median"]) for r in pts]
    figure = {
        "data": [{"type": "scatter", "mode": "lines+markers", "x": years, "y": medians,
                  "line": {"color": "#1a1a1a", "width": 2}, "marker": {"size": 6}}],
        "layout": {"title": {"text": title}, "font": {"family": "Inter, sans-serif"},
                   "xaxis": {"title": "Year", "dtick": 1},
                   "yaxis": {"title": "Median end price (EUR)"},
                   "paper_bgcolor": "#fff", "plot_bgcolor": "#F5F5F5"},
    }
    payload = json.dumps({"kind": "chart", "title": title,
                          "subtitle": f"{len(pts)} years of sold-lot medians", "figure": figure})
    return f"__ARTIFACT__{payload}"


market_performance = StructuredTool.from_function(
    func=_market_performance,
    name="market_performance",
    description=(
        "Compute historical price performance (CAGR / total return) from auction sales over the "
        "ENTIRE history for an artist or a market segment (category/medium/country/creation-period). "
        "Use for any ROI, appreciation, 'what % per year', or 'invested N years ago' question. "
        "Returns a median price index with a confidence rating; for a single artist it also returns a "
        "broader segment as a proxy. Numbers reflect realized auction prices only — never extrapolate beyond them."
    ),
    args_schema=PerformanceArgs,
)

performance_chart = StructuredTool.from_function(
    func=_performance_chart,
    name="performance_chart",
    description=(
        "Render an interactive line chart of the median price index over time for an artist or segment "
        "(same filters as market_performance). The chart appears in the Canvas pane. Offer it when a "
        "trend visual helps illustrate performance."
    ),
    args_schema=PerformanceArgs,
)
