"""Kunstveiling.nl scraper — Netherlands' largest online art auction (500K+ lots).

Paginated results at /en/auction-results/list?offset=N (48 items/page).
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

BASE_URL = "https://www.kunstveiling.nl"
RESULTS_URL = f"{BASE_URL}/en/auction-results/list"


def _scrape_results_page(page) -> list[dict]:
    """Extract lots from a Kunstveiling results page."""
    return page.evaluate(r"""() => {
        // Find all item containers - they typically have images + text + price
        const items = document.querySelectorAll('.item, .product, .result-item, [class*="auction-result"], article');
        const lots = [];

        // If structured items found
        if (items.length > 2) {
            items.forEach(item => {
                const text = item.textContent.replace(/\s+/g, ' ').trim();
                const link = item.querySelector('a');
                const img = item.querySelector('img');

                const priceMatch = text.match(/€\s*([\d.,]+)/);
                const price = priceMatch ? parseInt(priceMatch[1].replace(/[.,]/g, '')) : 0;

                if (text.length > 10 && text.length < 500) {
                    lots.push({
                        author: text.substring(0, 100),
                        title: '',
                        end_price: price,
                        source_url: link ? link.href : '',
                        image_url: img ? img.src : '',
                    });
                }
            });
            return lots;
        }

        // Fallback: find all links near € symbols
        const allLinks = [...document.querySelectorAll('a')];
        for (const a of allLinks) {
            const parent = a.closest('div, li, article, tr') || a.parentElement;
            if (!parent) continue;
            const pText = parent.textContent.replace(/\s+/g, ' ').trim();
            const priceMatch = pText.match(/€\s*([\d.,]+)/);
            if (priceMatch && pText.length > 20 && pText.length < 500) {
                const price = parseInt(priceMatch[1].replace(/[.,]/g, '')) || 0;
                const img = parent.querySelector('img');
                lots.push({
                    author: pText.replace(/€\s*[\d.,]+/, '').trim().substring(0, 100),
                    title: '',
                    end_price: price,
                    source_url: a.href,
                    image_url: img ? img.src : '',
                });
            }
        }
        return lots;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("kunstveiling")
    seen_urls = {l.get("source_url", "") for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        max_pages = 200  # ~9600 lots
        if limit:
            max_pages = min(max_pages, (limit // 48) + 1)

        for pg in range(max_pages):
            offset = pg * 48
            url = f"{RESULTS_URL}?offset={offset}"
            log.info("Page %d (offset %d)", pg + 1, offset)

            try:
                safe_navigate(page, url)
                time.sleep(2)
            except Exception as e:
                log.warning("  Failed: %s", e)
                break

            if pg == 0:
                dismiss_cookies(page)

            raw_lots = _scrape_results_page(page)
            if not raw_lots:
                log.info("  No more lots, stopping")
                break

            new_count = 0
            for raw in raw_lots:
                src = raw.get("source_url", "")
                if src in seen_urls:
                    continue
                seen_urls.add(src)

                lot = {
                    "auction_provider": "kunstveiling",
                    "country": "NL",
                    "author": _clean(raw.get("author", "Unknown"), 255) or "Unknown",
                    "title": _clean(raw.get("title", ""), 500),
                    "year": None,
                    "tech": "",
                    "dimensions_raw": "",
                    "dimension": None,
                    "start_price": 0,
                    "end_price": raw.get("end_price", 0),
                    "bid_count": None,
                    "auction_name": "Kunstveiling.nl",
                    "auction_date": 0,
                    "image_url": raw.get("image_url"),
                    "source_url": src,
                    "sold": raw.get("end_price", 0) > 0,
                    "lot_number": None,
                }
                lots.append(lot)
                new_count += 1

            log.info("  %d new lots (total: %d)", new_count, len(lots))
            save_checkpoint(lots, "kunstveiling")

            if limit and len(lots) >= limit:
                break

            time.sleep(1.5)

        lots = deduplicate(lots)
        save_checkpoint(lots, "kunstveiling")
        log.info("Kunstveiling scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
