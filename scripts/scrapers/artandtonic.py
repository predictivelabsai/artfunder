"""Art & Tonic scraper — single page with all past auction results (2019-present).

All lots on one page: /en/auctions/held/
Format: Author"Title"AH: Price€ (straight quotes, no spaces)
"""

from __future__ import annotations

import logging
import time

from scripts.scrapers.base import (
    parse_price, parse_year_from_text,
    setup_browser, dismiss_cookies, save_checkpoint, load_checkpoint,
    deduplicate, safe_navigate,
)

log = logging.getLogger(__name__)

BASE_URL = "https://artandtonic.art"
HELD_URL = f"{BASE_URL}/en/auctions/held/"


def _scrape_all_lots(page) -> list[dict]:
    """Extract all lots from the held auctions page."""
    return page.evaluate(r"""() => {
        const body = document.body.textContent;
        const lots = [];

        // Find auction headers: "Winter Auction 2020, 2020-12-11 18:00"
        // and lot entries: Author"Title"AH: Price€
        // The pattern: word chars + "title" + AH: + digits + €
        const lotPattern = /([\wÀ-ɏ][\wÀ-ɏ\s]+?)"([^"]+)"\s*AH:\s*([\d\s]+)€/g;

        // Also find auction headers to associate lots with auctions
        const headerPattern = /((?:Winter|Spring|Summer|Autumn|Fall|Kevad|Sugis|Talve)\s*(?:Auction|oksjon)\s*\d{4})/gi;
        const headers = [...body.matchAll(headerPattern)].map(m => ({
            name: m[1].trim(),
            index: m.index,
        }));

        let match;
        while ((match = lotPattern.exec(body)) !== null) {
            // Find which auction this lot belongs to
            let auctionName = '';
            for (const h of headers) {
                if (h.index < match.index) auctionName = h.name;
            }

            // Check for lot number prefix: "N. Author" or "N.Author"
            const before = body.substring(Math.max(0, match.index - 10), match.index);
            const numMatch = before.match(/(\d+)\.\s*$/);

            lots.push({
                lot_number: numMatch ? parseInt(numMatch[1]) : null,
                author: match[1].trim(),
                title: match[2].trim(),
                end_price_text: match[3].trim(),
                auction_name: auctionName,
            });
        }

        return lots;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("artandtonic")
    seen_keys = {(l.get("author", ""), l.get("title", ""), l.get("auction_name", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to Art & Tonic held auctions...")
        safe_navigate(page, HELD_URL)
        time.sleep(3)
        dismiss_cookies(page)

        raw_lots = _scrape_all_lots(page)
        log.info("Found %d lots on Art & Tonic", len(raw_lots))

        for raw in raw_lots:
            key = (raw.get("author", ""), raw.get("title", ""), raw.get("auction_name", ""))
            if key in seen_keys:
                continue

            end_price = parse_price(raw.get("end_price_text", ""))
            auction_year = parse_year_from_text(raw.get("auction_name", ""))

            lot = {
                "auction_provider": "artandtonic",
                "author": raw.get("author", "Unknown"),
                "title": raw.get("title", ""),
                "year": None,
                "tech": "",
                "dimensions_raw": "",
                "dimension": None,
                "start_price": 0,
                "end_price": end_price,
                "bid_count": None,
                "auction_name": raw.get("auction_name", ""),
                "auction_date": auction_year or 0,
                "image_url": None,
                "source_url": None,
                "sold": end_price > 0,
                "lot_number": raw.get("lot_number"),
            }

            lots.append(lot)
            seen_keys.add(key)

            if limit and len(lots) >= limit:
                break

        lots = deduplicate(lots)
        save_checkpoint(lots, "artandtonic")
        log.info("Art & Tonic scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
