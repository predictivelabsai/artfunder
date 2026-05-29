"""Load auction CSV data from artindex into kanvas.auction_lots.

Usage:
    python -m scripts.load_auction_data
"""

from __future__ import annotations

import csv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
ARTINDEX_CSV = Path(__file__).resolve().parents[2] / "artindex" / "data" / "allee_clean.csv"


def main() -> None:
    from db import SessionLocal
    from sqlalchemy import text

    if not ARTINDEX_CSV.exists():
        raise SystemExit(f"CSV not found: {ARTINDEX_CSV}")

    db = SessionLocal()
    try:
        # Clear existing allee data
        db.execute(text("DELETE FROM kanvas.auction_lots WHERE auction_provider = 'allee'"))
        db.commit()

        with open(ARTINDEX_CSV) as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    db.execute(
                        text("""
                            INSERT INTO kanvas.auction_lots
                                (auction_date, author, start_price, end_price, year, decade, tech, category, dimension, auction_provider)
                            VALUES (:date, :author, :start, :end, :year, :decade, :tech, :cat, :dim, 'allee')
                        """),
                        {
                            "date": int(row["date"]) if row.get("date") else 0,
                            "author": (row.get("author") or "").strip(),
                            "start": int(row["start_price"]) if row.get("start_price") else 0,
                            "end": int(row["end_price"]) if row.get("end_price") else 0,
                            "year": int(row["year"]) if row.get("year") and int(row["year"]) > 1800 else None,
                            "decade": int(row["decade"]) if row.get("decade") and int(row["decade"]) > 1800 else None,
                            "tech": (row.get("tech") or "").strip() or None,
                            "cat": (row.get("category") or "").strip() or None,
                            "dim": float(row["dimension"]) if row.get("dimension") else None,
                        },
                    )
                    count += 1
                except Exception as e:
                    print(f"  skip row: {e}")

            db.commit()
        print(f"Loaded {count} auction lots from {ARTINDEX_CSV.name}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
