"""Bukowskis scraper — Nordic fine art auctions (Finland + Sweden).

Results as HTML tables at /en/auctions/{id}/results.
Columns: lot#, item description, hammer price in SEK.
Auction IDs found at /en/results_fineart.
"""

from __future__ import annotations

import logging
import re
import time

from scripts.scrapers.base import (
    parse_price, parse_year_from_text,
    setup_browser, dismiss_cookies, save_checkpoint, load_checkpoint,
    deduplicate, safe_navigate, _clean,
)

log = logging.getLogger(__name__)

BASE_URL = "https://www.bukowskis.com"
RESULTS_URL = f"{BASE_URL}/en/results_fineart"

SEK_TO_EUR = 0.088  # approximate SEK→EUR


def _get_auction_ids(page) -> list[int]:
    """Get all auction IDs from the results page."""
    return page.evaluate(r"""() => {
        const links = [...document.querySelectorAll('a')];
        const ids = new Set();
        for (const a of links) {
            const m = a.href.match(/\/auctions\/(\d+)/);
            if (m) ids.add(parseInt(m[1]));
        }
        return [...ids].sort((a, b) => b - a);
    }""")


def _scrape_results_table(page) -> list[dict]:
    """Extract lots from auction results table."""
    return page.evaluate(r"""() => {
        const rows = document.querySelectorAll('tr');
        const lots = [];
        for (let i = 1; i < rows.length; i++) {
            const cells = rows[i].querySelectorAll('td');
            if (cells.length < 3) continue;

            const lotNum = parseInt(cells[0].textContent.trim()) || null;
            const desc = cells[1].textContent.trim();
            const priceText = cells[2].textContent.trim();
            const link = rows[i].querySelector('a');

            // Parse price (SEK or EUR)
            const priceMatch = priceText.match(/([\d\s]+)\s*(SEK|EUR)?/);
            const price = priceMatch ? parseInt(priceMatch[1].replace(/\s/g, '')) : 0;
            const currency = priceMatch && priceMatch[2] ? priceMatch[2] : 'SEK';

            // Parse author from description
            // Format: "AUTHOR NAME, description of item"
            // Author is typically in CAPS
            let author = '', title = '';
            const capsMatch = desc.match(/^([A-ZÄÖÜÅÉÈÊËÀÂÏÎÔÛÙÜÇ\s.'-]+),\s*/);
            if (capsMatch) {
                author = capsMatch[1].trim();
                // Title case
                author = author.split(' ').map(w =>
                    w.charAt(0) + w.slice(1).toLowerCase()
                ).join(' ');
                title = desc.substring(capsMatch[0].length).trim();
            } else {
                author = desc.substring(0, 60);
            }

            lots.push({
                lot_number: lotNum,
                author: author,
                title: title.substring(0, 200),
                price: price,
                currency: currency,
                source_url: link ? link.href : '',
            });
        }
        return lots;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("bukowskis")
    seen_keys = {(l.get("author", ""), l.get("title", ""), l.get("auction_name", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to Bukowskis results...")
        safe_navigate(page, RESULTS_URL)
        time.sleep(2)
        dismiss_cookies(page)

        auction_ids = _get_auction_ids(page)
        log.info("Found %d auctions", len(auction_ids))

        # Also try a range of IDs to catch more auctions
        known_ids = set(auction_ids)
        if auction_ids:
            max_id = max(auction_ids)
            min_id = min(auction_ids)
            for i in range(min_id, max_id + 1):
                known_ids.add(i)

        all_ids = sorted(known_ids, reverse=True)
        log.info("Scanning %d auction IDs (%d-%d)", len(all_ids), all_ids[-1] if all_ids else 0, all_ids[0] if all_ids else 0)

        for auction_id in all_ids:
            results_url = f"{BASE_URL}/en/auctions/{auction_id}/results"
            auction_name = f"Auction {auction_id}"

            try:
                safe_navigate(page, results_url)
                time.sleep(1)
            except Exception:
                continue

            # Check if page has results
            title = page.title()
            if "404" in title or "Not Found" in title:
                continue

            # Get auction name from page title
            if " - " in title:
                auction_name = title.split(" - ")[1].strip() if "Results" in title else title.split(" - ")[0].strip()

            auction_year = parse_year_from_text(title) or parse_year_from_text(auction_name)

            raw_lots = _scrape_results_table(page)
            if not raw_lots:
                continue

            log.info("  Auction %d: %s — %d lots", auction_id, auction_name[:40], len(raw_lots))

            # Determine country from auction name
            country = "SE"
            name_lower = auction_name.lower()
            if "helsinki" in name_lower or "finnish" in name_lower or "finland" in name_lower:
                country = "FI"

            for raw in raw_lots:
                key = (raw.get("author", ""), raw.get("title", ""), auction_name)
                if key in seen_keys:
                    continue

                # Convert SEK to EUR
                price = raw.get("price", 0)
                if raw.get("currency") == "SEK" and price > 0:
                    price = int(price * SEK_TO_EUR)

                lot = {
                    "auction_provider": "bukowskis",
                    "country": country,
                    "author": _clean(raw.get("author", "Unknown"), 255) or "Unknown",
                    "title": _clean(raw.get("title", ""), 500),
                    "year": None,
                    "tech": "",
                    "dimensions_raw": "",
                    "dimension": None,
                    "start_price": 0,
                    "end_price": price,
                    "bid_count": None,
                    "auction_name": _clean(auction_name, 255),
                    "auction_date": auction_year or 0,
                    "image_url": None,
                    "source_url": raw.get("source_url"),
                    "sold": price > 0,
                    "lot_number": raw.get("lot_number"),
                }

                lots.append(lot)
                seen_keys.add(key)

            save_checkpoint(lots, "bukowskis")

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

        lots = deduplicate(lots)
        save_checkpoint(lots, "bukowskis")
        log.info("Bukowskis scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
