"""Text-to-SQL tool for agents — queries kanvas schema via sql/schema.json."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import pandas as pd
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

_SCHEMA_JSON = Path(__file__).resolve().parents[1] / "sql" / "schema.json"


def _load_schema_snippet() -> str:
    """Build a human-readable schema snippet from sql/schema.json."""
    if not _SCHEMA_JSON.exists():
        return "(schema.json not found — query kanvas.auction_lots and kanvas.artworks)"
    data = json.loads(_SCHEMA_JSON.read_text())
    lines = []
    for table, info in data.items():
        cols = info.get("columns", [])
        col_parts = []
        for c in cols:
            part = f"{c['name']} {c['type']}"
            col_parts.append(part)
        count = info.get("row_count", "?")
        providers = info.get("providers")
        categories = info.get("categories_sample")
        header = f"{table} ({count} rows)"
        lines.append(header)
        lines.append(f"  ({', '.join(col_parts)})")
        if providers:
            lines.append(f"  -- providers: {', '.join(repr(p) for p in providers)}")
        if categories:
            lines.append(f"  -- categories sample: {', '.join(repr(c) for c in categories)}")
        lines.append("")
    return "\n".join(lines)


class SQLQueryArgs(BaseModel):
    question: str = Field(description="Natural-language question about art market data, e.g. 'Top 10 artists by total sales' or 'Average price for Konrad Mägi works'")


def _draft_sql(question: str) -> str:
    from utils.llm import build_llm

    schema = _load_schema_snippet()
    system = f"""You translate plain-English questions into a single PostgreSQL SELECT query.

Rules:
- Return ONLY the raw SQL, nothing else. No markdown, no explanation.
- SELECT only. Never modify data.
- Use schema-qualified names (kanvas.auction_lots, kanvas.artworks).
- LIMIT to 50 rows max unless aggregating.
- For time series, ORDER BY the time column.
- Use ILIKE for name matching.
- Prices are in whole EUR (not cents).

Schema:
{schema}"""

    llm = build_llm()
    resp = llm.invoke(f"{system}\n\nQuestion: {question}\n\nSQL:").content
    sql = resp.strip().strip("`").strip()
    if sql.lower().startswith("sql"):
        sql = sql[3:].strip()
    sql = sql.rstrip(";")
    return sql


def _guard_sql(sql: str) -> None:
    lowered = sql.lower().strip()
    if not lowered.startswith("select") and not lowered.startswith("with"):
        raise ValueError("Only SELECT / WITH queries are allowed.")
    for kw in ["insert ", "update ", "delete ", "drop ", "truncate ", "alter ", "create "]:
        if kw in lowered:
            raise ValueError(f"Disallowed keyword: {kw.strip()}")


def _run_query(question: str) -> str:
    sql = _draft_sql(question)
    _guard_sql(sql)

    from db import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        result = db.execute(text(sql))
        rows = [dict(r._mapping) for r in result]
    finally:
        db.close()

    if not rows:
        return f"No results found.\n\nSQL used: {sql}"

    df = pd.DataFrame(rows)

    # Format numeric columns
    for col in df.select_dtypes(include=["float", "int"]).columns:
        if df[col].abs().max() > 1000:
            df[col] = df[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "")

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str[:60]

    # Build markdown table
    preview = df.head(20)
    headers = " | ".join(str(c) for c in preview.columns)
    separator = " | ".join("---" for _ in preview.columns)
    body_rows = []
    for _, row in preview.iterrows():
        body_rows.append(" | ".join(str(v) for v in row.values))

    lines = [f"Query results ({len(df)} rows):\n"]
    lines.append(headers)
    lines.append(separator)
    lines.extend(body_rows)

    if len(df) > 20:
        lines.append(f"\n*Showing first 20 of {len(df)} rows.*")

    return "\n".join(lines)


def _safe_query(**kw) -> str:
    args = SQLQueryArgs(**kw)
    try:
        return _run_query(args.question)
    except Exception as e:
        log.warning("SQL query failed: %s", e)
        return f"Query failed: {e}"


art_market_query = StructuredTool.from_function(
    func=_safe_query,
    name="art_market_query",
    description=(
        "Query the Kanvas art market database using natural language. "
        "Contains 10,000+ auction lots from 5 Estonian galleries (Haus, Allee, Vaal, Vernissage, Art&Tonic) "
        "spanning 1998-2026. Use for: artist sales history, price trends, market statistics, "
        "top sellers, category analysis, overbid percentages, gallery comparisons."
    ),
    args_schema=SQLQueryArgs,
)
