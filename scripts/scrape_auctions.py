"""CLI entry point for Estonian art auction scrapers.

Usage:
    python -m scripts.scrape_auctions --provider haus --headless
    python -m scripts.scrape_auctions --all --headless
    python -m scripts.scrape_auctions --load --provider haus
    python -m scripts.scrape_auctions --load --all
"""

from __future__ import annotations

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scrape")

PROVIDERS = [
    # Estonia
    "haus", "allee", "vaal", "vaal_archive", "vernissage", "artandtonic", "salong",
    # Latvia
    "antonija",
    # Lithuania
    "menorinka",
    # Finland
    "hagelstam", "bukowskis",
    # Sweden
    "auctionet", "stockholms_auktionsverk",
    # Denmark
    "bruun_rasmussen", "lauritz",
    # Norway
    "gwpa",
    # Netherlands
    "kunstveiling",
    # UK
    "bonhams",
]


def get_scraper(provider: str):
    if provider == "haus":
        from scripts.scrapers.haus import scrape
    elif provider == "allee":
        from scripts.scrapers.allee import scrape
    elif provider == "vaal":
        from scripts.scrapers.vaal import scrape
    elif provider == "vaal_archive":
        from scripts.scrapers.vaal_archive import scrape
    elif provider == "vernissage":
        from scripts.scrapers.vernissage import scrape
    elif provider == "artandtonic":
        from scripts.scrapers.artandtonic import scrape
    elif provider == "salong":
        from scripts.scrapers.salong import scrape
    elif provider == "antonija":
        from scripts.scrapers.antonija import scrape
    elif provider == "menorinka":
        from scripts.scrapers.menorinka import scrape
    elif provider == "hagelstam":
        from scripts.scrapers.hagelstam import scrape
    elif provider == "bukowskis":
        from scripts.scrapers.bukowskis import scrape
    elif provider == "auctionet":
        from scripts.scrapers.auctionet import scrape
    elif provider == "bruun_rasmussen":
        from scripts.scrapers.bruun_rasmussen import scrape
    elif provider == "lauritz":
        from scripts.scrapers.lauritz import scrape
    elif provider == "stockholms_auktionsverk":
        from scripts.scrapers.stockholms_auktionsverk import scrape
    elif provider == "gwpa":
        from scripts.scrapers.gwpa import scrape
    elif provider == "kunstveiling":
        from scripts.scrapers.kunstveiling import scrape
    elif provider == "bonhams":
        from scripts.scrapers.bonhams import scrape
    else:
        raise ValueError(f"Unknown provider: {provider}")
    return scrape


def load_to_db(provider: str):
    """Load scraped JSON data into kanvas.auction_lots."""
    from scripts.scrapers.base import load_checkpoint, lot_to_db_row
    from dotenv import load_dotenv
    load_dotenv()

    import os
    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["DB_URL"])

    lots = load_checkpoint(provider)
    if not lots:
        log.warning("No checkpoint data for %s", provider)
        return 0

    inserted = 0
    skipped = 0
    with engine.connect() as conn:
        for lot in lots:
            row = lot_to_db_row(lot)
            # Dedup by (author, title, auction_provider, auction_name)
            existing = conn.execute(
                text("""SELECT 1 FROM kanvas.auction_lots
                     WHERE LOWER(author) = LOWER(:author)
                     AND LOWER(COALESCE(title,'')) = LOWER(COALESCE(:title,''))
                     AND auction_provider = :provider
                     AND LOWER(COALESCE(auction_name,'')) = LOWER(COALESCE(:aname,''))
                     LIMIT 1"""),
                {
                    "author": row["author"],
                    "title": row.get("title") or "",
                    "provider": row["auction_provider"],
                    "aname": row.get("auction_name") or "",
                },
            ).fetchone()
            if existing:
                skipped += 1
                continue

            conn.execute(
                text("""
                    INSERT INTO kanvas.auction_lots
                    (auction_date, author, start_price, end_price, year, decade,
                     tech, category, dimension, auction_provider,
                     title, lot_number, dimensions_raw, bid_count,
                     auction_name, image_url, source_url, sold, country)
                    VALUES
                    (:auction_date, :author, :start_price, :end_price, :year, :decade,
                     :tech, :category, :dimension, :auction_provider,
                     :title, :lot_number, :dimensions_raw, :bid_count,
                     :auction_name, :image_url, :source_url, :sold, :country)
                """),
                row,
            )
            inserted += 1

        conn.commit()

    log.info("Loaded %s: %d inserted, %d skipped (duplicates)", provider, inserted, skipped)
    return inserted


def main():
    ap = argparse.ArgumentParser(description="Scrape Estonian art auction data")
    ap.add_argument("--provider", choices=PROVIDERS, help="Specific provider to scrape")
    ap.add_argument("--all", action="store_true", help="Scrape all providers")
    ap.add_argument("--limit", type=int, default=0, help="Max lots per provider (0 = unlimited)")
    ap.add_argument("--headless", action="store_true", default=True, help="Run browser headless")
    ap.add_argument("--no-headless", dest="headless", action="store_false")
    ap.add_argument("--load", action="store_true", help="Load scraped JSON into DB instead of scraping")
    args = ap.parse_args()

    if not args.provider and not args.all:
        ap.error("Specify --provider or --all")

    providers = PROVIDERS if args.all else [args.provider]

    if args.load:
        total = 0
        for p in providers:
            total += load_to_db(p)
        log.info("Total loaded: %d lots", total)
        return

    for p in providers:
        log.info("=== Scraping %s ===", p.upper())
        try:
            scraper = get_scraper(p)
            scraper(headless=args.headless, limit=args.limit)
        except Exception as e:
            log.error("Failed scraping %s: %s", p, e, exc_info=True)
            if not args.all:
                sys.exit(1)

    log.info("Done.")


if __name__ == "__main__":
    main()
