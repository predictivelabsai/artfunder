"""Data auditor for kanvas.auction_lots — flags corrupt records as status='inactive'.

Corruption rules (any match → inactive):
  1. Author is numeric-only (lot/serial numbers parsed as names)
  2. Author is single character or empty
  3. Author contains newlines/tabs (mangled HTML scraping)
  4. Author is a book title (>80 chars or contains publishing keywords)
  5. Author is 'Unknown'
  6. Price is serial number (end_price > 500,000 without matching high-value indicators)
  7. Author is 2-3 chars and not a known abbreviation pattern (e.g. 'cm', 'er')
  8. Author contains raw HTML fragments or price strings

Usage:
    python -m scripts.audit_data              # dry-run: report counts
    python -m scripts.audit_data --apply      # mark corrupt rows inactive
    python -m scripts.audit_data --stats      # show status breakdown
"""

from __future__ import annotations

import argparse
import re
import sys

from sqlalchemy import text


RULES: list[tuple[str, str]] = [
    (
        "numeric_author",
        "author ~ '^\\d+$'"
    ),
    (
        "single_char_author",
        "LENGTH(TRIM(author)) <= 1"
    ),
    (
        "empty_author",
        "TRIM(author) = '' OR author IS NULL"
    ),
    (
        "author_is_unknown",
        "LOWER(TRIM(author)) IN ('unknown', '-', '.', '?', 'n/a')"
    ),
    (
        "author_has_newlines",
        r"author ~ E'[\n\t\r]'"
    ),
    (
        "author_book_title_long",
        "LENGTH(author) > 80"
    ),
    (
        "author_book_title_keywords",
        "author ~* '(Изд\\.|Москва|каталог|альбом|книга|издатель|Искусство,|Советский|Бухарест|артия|Ленинград|apgāds|Valters un Rapa)'"
    ),
    (
        "author_short_junk",
        "LENGTH(TRIM(author)) BETWEEN 2 AND 3 "
        "AND author !~ '^[A-Z][a-z]{1,2}$' "
        "AND author !~ '^[A-ZÄÖÜÕŠŽ][a-zäöüõšž]{1,2}$' "
        "AND author NOT IN ('Iwc', 'Uus', 'Agu', 'Cox', 'Fox', 'Doe', 'Cat', 'Dog', 'Roe', 'Cup', 'RPF')"
    ),
    (
        "price_is_serial_number",
        "end_price > 500000 AND auction_provider = 'antonija'"
    ),
    (
        "author_contains_price_html",
        "author ~* '(Alghind|Haamrihind|€|hind)' AND LENGTH(author) > 30"
    ),
    (
        "author_contains_html",
        r"author ~ '(rekordid|oksjon\s+\d{4}|edasi\t)'"
    ),
    (
        "no_price_at_all",
        "end_price <= 0 AND COALESCE(start_price, 0) <= 0"
    ),
]


def get_db():
    from db import SessionLocal
    return SessionLocal()


def audit_dry_run():
    db = get_db()
    try:
        total = db.execute(text("SELECT COUNT(*) FROM kanvas.auction_lots")).scalar()
        print(f"Total rows: {total:,}")
        print()

        flagged_ids = set()
        for name, condition in RULES:
            sql = text(f"SELECT COUNT(*), array_agg(id) FROM kanvas.auction_lots WHERE {condition}")
            row = db.execute(sql).fetchone()
            count = row[0]
            ids = row[1] or []
            flagged_ids.update(ids)
            pct = count / total * 100 if total else 0
            print(f"  {name:35s} {count:>6,} rows  ({pct:.1f}%)")

        print()
        print(f"  {'TOTAL UNIQUE FLAGGED':35s} {len(flagged_ids):>6,} rows  ({len(flagged_ids)/total*100:.1f}%)")
        print(f"  {'REMAINING CLEAN':35s} {total - len(flagged_ids):>6,} rows  ({(total-len(flagged_ids))/total*100:.1f}%)")

        print("\n--- Breakdown by provider ---")
        combined = " OR ".join(f"({c})" for _, c in RULES)
        sql = text(f"""
            SELECT auction_provider,
                   COUNT(*) FILTER (WHERE {combined}) as flagged,
                   COUNT(*) as total
            FROM kanvas.auction_lots
            GROUP BY auction_provider
            ORDER BY auction_provider
        """)
        for r in db.execute(sql):
            prov, flagged, tot = r
            clean = tot - flagged
            print(f"  {prov:20s}  flagged={flagged:>6,}  clean={clean:>6,}  total={tot:>6,}")

    finally:
        db.close()


def audit_apply():
    db = get_db()
    try:
        db.execute(text("ALTER TABLE kanvas.auction_lots ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active'"))
        db.commit()
        db.execute(text("UPDATE kanvas.auction_lots SET status = 'active' WHERE status IS NULL"))

        combined = " OR ".join(f"({c})" for _, c in RULES)
        result = db.execute(text(f"""
            UPDATE kanvas.auction_lots
            SET status = 'inactive'
            WHERE {combined}
        """))
        count = result.rowcount
        db.commit()
        print(f"Marked {count:,} rows as inactive.")

        total = db.execute(text("SELECT COUNT(*) FROM kanvas.auction_lots")).scalar()
        active = db.execute(text("SELECT COUNT(*) FROM kanvas.auction_lots WHERE status = 'active'")).scalar()
        print(f"Active: {active:,} / {total:,} ({active/total*100:.1f}%)")
    finally:
        db.close()


def show_stats():
    db = get_db()
    try:
        rows = db.execute(text("""
            SELECT auction_provider, status, COUNT(*)
            FROM kanvas.auction_lots
            GROUP BY auction_provider, status
            ORDER BY auction_provider, status
        """)).fetchall()

        print(f"{'Provider':20s} {'Status':10s} {'Count':>8s}")
        print("-" * 42)
        for r in rows:
            print(f"{r[0]:20s} {r[1] or 'NULL':10s} {r[2]:>8,}")

        print()
        totals = db.execute(text("""
            SELECT COALESCE(status, 'NULL'), COUNT(*) FROM kanvas.auction_lots GROUP BY 1 ORDER BY 1
        """)).fetchall()
        for r in totals:
            print(f"  TOTAL {r[0]:10s}: {r[1]:>8,}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Audit auction_lots for corrupt data")
    parser.add_argument("--apply", action="store_true", help="Mark corrupt rows as inactive")
    parser.add_argument("--stats", action="store_true", help="Show status breakdown")
    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.apply:
        audit_dry_run()
        print()
        print("=" * 50)
        print("Applying changes...")
        audit_apply()
    else:
        audit_dry_run()


if __name__ == "__main__":
    main()
