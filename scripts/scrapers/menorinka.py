"""Menorinka / Vilniaus Aukcionas scraper — Lithuania's oldest auction house.

90+ auctions since 2007, /aukcionas/{id} pattern.
May return 403 to simple bots — uses full browser with realistic UA.
"""

from __future__ import annotations

import logging
import re
import time

from scripts.scrapers.base import (
    parse_price, parse_dimensions, parse_year_from_text,
    setup_browser, dismiss_cookies, save_checkpoint, load_checkpoint,
    deduplicate, safe_navigate, _clean,
)

log = logging.getLogger(__name__)

BASE_URL = "https://www.menorinka.lt"
# Auction IDs roughly correspond to auction numbers. Range ~26-91+
MIN_AUCTION_ID = 26
MAX_AUCTION_ID = 95


def _scrape_auction_page(page) -> list[dict]:
    """Extract lots from a Menorinka auction page."""
    return page.evaluate(r"""() => {
        // Try multiple possible lot container selectors
        const selectors = [
            '.lot', '.auction-lot', '.product', '.item',
            '[class*="lot"]', '[class*="item"]', 'tr',
            '.woocommerce-loop-product__title',
            'article', '.entry'
        ];

        // Check if it's a table
        const tables = document.querySelectorAll('table');
        if (tables.length > 0) {
            const lots = [];
            for (const table of tables) {
                const rows = table.querySelectorAll('tr');
                for (let i = 1; i < rows.length; i++) {
                    const cells = [...rows[i].querySelectorAll('td')];
                    if (cells.length >= 3) {
                        const text = cells.map(c => c.textContent.trim());
                        lots.push({
                            lot_number: parseInt(text[0]) || null,
                            author: text[1] || text[0],
                            title: text.length > 2 ? text[2] : '',
                            price_text: text[text.length - 1] || '',
                        });
                    }
                }
            }
            if (lots.length > 0) return lots;
        }

        // Try product/lot cards
        const items = document.querySelectorAll('.product, .lot-item, .auction-item, [class*="lot"]');
        if (items.length > 0) {
            const lots = [];
            for (const item of items) {
                const text = item.textContent.trim();
                const link = item.querySelector('a');
                const img = item.querySelector('img');

                // Try to parse lot number, author, title, price
                const lotMatch = text.match(/^(\d+)\.\s*/);
                const priceMatch = text.match(/([\d\s]+)\s*€/);

                lots.push({
                    lot_number: lotMatch ? parseInt(lotMatch[1]) : null,
                    author: text.substring(0, 100),
                    title: '',
                    price_text: priceMatch ? priceMatch[0] : '',
                    source_url: link ? link.href : '',
                    image_url: img ? img.src : '',
                });
            }
            if (lots.length > 0) return lots;
        }

        // Fallback: parse body text for price patterns
        const body = document.body.textContent;
        const lots = [];
        const pricePattern = /([\d\s]+)\s*€/g;
        let m;
        while ((m = pricePattern.exec(body)) !== null && lots.length < 300) {
            const before = body.substring(Math.max(0, m.index - 200), m.index);
            const lines = before.split('\n').filter(l => l.trim().length > 2);
            const lastLine = lines[lines.length - 1] || '';

            lots.push({
                lot_number: null,
                author: lastLine.trim().substring(0, 100),
                title: '',
                price_text: m[0].trim(),
            });
        }
        return lots;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("menorinka")
    seen_keys = {(l.get("author", ""), str(l.get("lot_number", "")), l.get("auction_name", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        for auction_id in range(MAX_AUCTION_ID, MIN_AUCTION_ID - 1, -1):
            auction_url = f"{BASE_URL}/aukcionas/{auction_id}"
            auction_name = f"Aukcionas {auction_id}"

            log.info("Processing: %s", auction_name)

            try:
                safe_navigate(page, auction_url)
                time.sleep(2)
            except Exception as e:
                log.warning("  Failed to load %s: %s", auction_url, e)
                continue

            # Check if page loaded (not 403/404)
            page_title = page.title()
            if "403" in page_title or "404" in page_title or "Error" in page_title:
                log.warning("  %s returned %s, skipping", auction_url, page_title)
                continue

            if auction_id == MAX_AUCTION_ID:
                dismiss_cookies(page)

            # Try to get auction name from page
            actual_name = page.evaluate("""() => {
                const h1 = document.querySelector('h1, h2, .page-title, .auction-title');
                return h1 ? h1.textContent.trim().substring(0, 100) : '';
            }""")
            if actual_name:
                auction_name = actual_name

            auction_year = parse_year_from_text(page_title) or parse_year_from_text(auction_name)

            raw_lots = _scrape_auction_page(page)
            log.info("  %d lots in %s", len(raw_lots), auction_name[:40])

            for raw in raw_lots:
                key = (raw.get("author", ""), str(raw.get("lot_number", "")), auction_name)
                if key in seen_keys:
                    continue

                end_price = parse_price(raw.get("price_text", ""))

                lot = {
                    "auction_provider": "menorinka",
                    "country": "LT",
                    "author": _clean(raw.get("author", "Unknown"), 255) or "Unknown",
                    "title": _clean(raw.get("title", ""), 500),
                    "year": None,
                    "tech": "",
                    "dimensions_raw": "",
                    "dimension": None,
                    "start_price": 0,
                    "end_price": end_price,
                    "bid_count": None,
                    "auction_name": _clean(auction_name, 255),
                    "auction_date": auction_year or 0,
                    "image_url": raw.get("image_url"),
                    "source_url": raw.get("source_url"),
                    "sold": end_price > 0,
                    "lot_number": raw.get("lot_number"),
                }

                lots.append(lot)
                seen_keys.add(key)

            save_checkpoint(lots, "menorinka")

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

            time.sleep(2)

        lots = deduplicate(lots)
        save_checkpoint(lots, "menorinka")
        log.info("Menorinka scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
