"""Art & Tonic scraper — single page with all past auction results.

All lots on one page: /en/auctions/held/
Structure: h2 auction headers with dates, then per-lot divs containing
  h2 "N. Author", h3 "\"Title\"", h3 "AH: Price€"
"""

from __future__ import annotations

import logging
import re
import time

from scripts.scrapers.base import (
    parse_price,
    setup_browser, dismiss_cookies, save_checkpoint, load_checkpoint,
    deduplicate, safe_navigate,
)

log = logging.getLogger(__name__)

BASE_URL = "https://artandtonic.art"
HELD_URL = f"{BASE_URL}/en/auctions/held/"


def _scrape_all_lots(page) -> list[dict]:
    """Extract all lots from the held auctions page using DOM structure."""
    return page.evaluate(r"""() => {
        const allH2 = [...document.querySelectorAll('h2')];
        const lots = [];
        let currentAuction = '';
        let currentYear = 0;

        for (const h2 of allH2) {
            const text = h2.textContent.trim();

            // Check if this is an auction header (contains a date like YYYY-MM-DD)
            const dateMatch = text.match(/(\d{4})-(\d{2})-(\d{2})/);
            if (dateMatch) {
                currentAuction = text.split(',')[0].trim();
                currentYear = parseInt(dateMatch[1]);
                continue;
            }

            // Check if this is a lot author (starts with "N. Author" or "N.Author")
            const lotMatch = text.match(/^(\d+)\.\s*(.+)$/);
            if (!lotMatch) continue;

            const lotNumber = parseInt(lotMatch[1]);
            const author = lotMatch[2].trim();

            // Find the title and price h3s that follow this h2
            const container = h2.closest('div') || h2.parentElement;
            if (!container) continue;

            const h3s = container.querySelectorAll('h3');
            let title = '';
            let priceText = '';

            for (const h3 of h3s) {
                const h3text = h3.textContent.trim();
                if (h3text.startsWith('AH:') || h3text.startsWith('AH :')) {
                    priceText = h3text;
                } else if (h3text.startsWith('"') || h3text.startsWith('“')) {
                    title = h3text.replace(/^[""“]+|[""”]+$/g, '').trim();
                }
            }

            if (author && currentAuction) {
                lots.push({
                    lot_number: lotNumber,
                    author: author,
                    title: title,
                    end_price_text: priceText.replace(/^AH\s*:\s*/, ''),
                    auction_name: currentAuction,
                    auction_year: currentYear,
                });
            }
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
                "auction_date": raw.get("auction_year", 0),
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
