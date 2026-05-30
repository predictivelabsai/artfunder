"""Text-to-SQL tool for agents — queries kanvas.auction_lots and artworks."""

from __future__ import annotations

import json
import logging
import re

import pandas as pd
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

SCHEMA_SNIPPET = """\
kanvas.auction_lots (
    id, auction_date BIGINT (auction year), author VARCHAR,
    start_price BIGINT (EUR), end_price BIGINT (EUR, 0 if unsold),
    year BIGINT (year artwork created), decade BIGINT,
    tech VARCHAR (e.g. 'Oil on canvas', 'Watercolour', 'Lithograph'),
    category VARCHAR (e.g. 'Oil paint', 'Graphics', 'Drawing'),
    dimension DOUBLE PRECISION (area cm²),
    auction_provider VARCHAR ('haus','allee','vaal','vernissage','artandtonic'),
    title VARCHAR, lot_number INT, dimensions_raw VARCHAR,
    bid_count INT, auction_name VARCHAR, sold BOOLEAN
)
-- 10,000+ lots from 5 Estonian galleries (1998-2026)

kanvas.artworks (
    id, title, artist_name, category, medium, year_created,
    estimated_value NUMERIC, status, origin_country, dimensions
)
"""


class SQLQueryArgs(BaseModel):
    question: str = Field(description="Natural-language question about art market data, e.g. 'Top 10 artists by total sales' or 'Average price for Konrad Mägi works'")


def _draft_sql(question: str) -> str:
    from utils.llm import build_llm

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
{SCHEMA_SNIPPET}"""

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
