"""Bruun Rasmussen scraper — Denmark's largest auction house.

Categories with sold lots at /m/categories/{id}?status=sold
Lots as .lot-list-item with .lot-details. Prices JS-rendered (needs Playwright).
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

BASE_URL = "https://bruun-rasmussen.dk"

# Art categories with their IDs
CATEGORIES = [
    (55538, "Modern Paintings"),
    (55539, "Older Paintings"),
    (55540, "Contemporary Art"),
    (55541, "Prints & Multiples"),
    (55542, "Sculpture"),
    (55543, "Photography"),
]


def _scrape_category_page(page) -> list[dict]:
    """Extract lots from a Bruun Rasmussen sold lots page."""
    return page.evaluate(r"""() => {
        const items = document.querySelectorAll('.lot-list-item');
        const lots = [];
        for (const item of items) {
            const link = item.querySelector('a[href*="/lots/"]');
            const img = item.querySelector('img');
            const text = item.textContent.replace(/\s+/g, ' ').trim();

            // Parse lot number: "2622/962"
            const lotMatch = text.match(/(\d+\/\d+)/);

            // Parse artist and title from description
            // Format: "2622/962 Artist Name: Title. Medium. WxH cm."
            let author = '', title = '', tech = '', dims = '';
            const descMatch = text.match(/\d+\/\d+\s*(?:\w+\s+)?(.+?):\s*(.+?)(?:Estimate|Price|Selling|$)/);
            if (descMatch) {
                author = descMatch[1].trim();
                const rest = descMatch[2].trim();
                // Title is usually before first period
                const parts = rest.split('.');
                title = parts[0].trim();
                if (parts.length > 1) {
                    tech = parts.slice(1).join('.').trim();
                }
            }

            // Parse price: "Price realised: DKK X" or "DKK X,XXX"
            const priceMatch = text.match(/(?:Price realised|Pris)[\s:]*(?:DKK\s*)?([\d.,\s]+)/i) ||
                               text.match(/DKK\s*([\d.,\s]+)/);
            let price = 0;
            if (priceMatch) {
                price = parseInt(priceMatch[1].replace(/[.,\s]/g, '')) || 0;
                // Convert DKK to EUR (~0.134)
                price = Math.round(price * 0.134);
            }

            // Parse dimensions
            const dimMatch = text.match(/([\d]+\s*x\s*[\d]+)\s*cm/);
            dims = dimMatch ? dimMatch[1] + ' cm' : '';

            const sold = text.includes('Price realised') || text.includes('Sold');

            if (author || title) {
                lots.push({
                    lot_number: lotMatch ? lotMatch[1] : null,
                    author: author.substring(0, 200),
                    title: title.substring(0, 200),
                    tech: tech.substring(0, 200),
                    dimensions_raw: dims,
                    end_price: price,
                    sold: sold,
                    image_url: img ? img.src : null,
                    source_url: link ? link.href : null,
                });
            }
        }
        return lots;
    }""")


def _scroll_to_load_all(page, max_scrolls=20):
    """Scroll down to load lazy-loaded content."""
    for _ in range(max_scrolls):
        prev_count = page.evaluate("() => document.querySelectorAll('.lot-list-item').length")
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        new_count = page.evaluate("() => document.querySelectorAll('.lot-list-item').length")
        if new_count == prev_count:
            break


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("bruun_rasmussen")
    seen_keys = {(str(l.get("lot_number", "")), l.get("auction_name", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        for cat_id, cat_name in CATEGORIES:
            url = f"{BASE_URL}/m/categories/{cat_id}?status=sold&cas=guest&locale=en"
            log.info("Processing category: %s", cat_name)

            try:
                safe_navigate(page, url)
                time.sleep(3)
            except Exception as e:
                log.warning("  Failed: %s", e)
                continue

            if cat_id == CATEGORIES[0][0]:
                dismiss_cookies(page)

            _scroll_to_load_all(page)

            raw_lots = _scrape_category_page(page)
            log.info("  %d lots in %s", len(raw_lots), cat_name)

            for raw in raw_lots:
                key = (str(raw.get("lot_number", "")), cat_name)
                if key in seen_keys:
                    continue

                dims_raw = raw.get("dimensions_raw", "")
                dim_area, dims_clean = parse_dimensions(dims_raw) if dims_raw else (None, "")

                lot = {
                    "auction_provider": "bruun_rasmussen",
                    "country": "DK",
                    "author": _clean(raw.get("author", "Unknown"), 255) or "Unknown",
                    "title": _clean(raw.get("title", ""), 500),
                    "year": None,
                    "tech": _clean(raw.get("tech", ""), 255),
                    "dimensions_raw": dims_clean,
                    "dimension": dim_area,
                    "start_price": 0,
                    "end_price": raw.get("end_price", 0),
                    "bid_count": None,
                    "auction_name": _clean(cat_name, 255),
                    "auction_date": 0,
                    "image_url": raw.get("image_url"),
                    "source_url": raw.get("source_url"),
                    "sold": raw.get("sold", False),
                    "lot_number": raw.get("lot_number"),
                }

                lots.append(lot)
                seen_keys.add(key)

            save_checkpoint(lots, "bruun_rasmussen")

            if limit and len(lots) >= limit:
                break

            time.sleep(2)

        lots = deduplicate(lots)
        save_checkpoint(lots, "bruun_rasmussen")
        log.info("Bruun Rasmussen scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
