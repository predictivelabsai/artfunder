"""Vaal Galerii ARCHIVE scraper — arhiiv.vaal.ee (1999-2021, 62 auctions).

The archive site has a different structure from the modern vaal.ee:
- Index: /est/avaleht/oksjon/toimunud_oksjonid lists all 62 past auctions
- Each auction page has lots inline with: "NN. Author (birth-death) Alghind NNNN EUR"
- No pagination within auctions
"""

from __future__ import annotations

import logging
import re
import time

from scripts.scrapers.base import (
    parse_price, parse_year_from_text,
    setup_browser, dismiss_cookies, save_checkpoint, load_checkpoint,
    deduplicate, safe_navigate,
)

log = logging.getLogger(__name__)

BASE_URL = "http://arhiiv.vaal.ee"
INDEX_URL = f"{BASE_URL}/est/avaleht/oksjon/toimunud_oksjonid"


def _get_auction_links(page) -> list[dict]:
    """Get all past auction links from the archive index."""
    return page.evaluate(r"""() => {
        const links = [...document.querySelectorAll('a')];
        const auctions = [];
        const seen = new Set();
        for (const a of links) {
            const href = a.href;
            const text = a.textContent.trim();
            if (href.includes('toimunud_oksjonid/') && href !== window.location.href
                && !href.endsWith('toimunud_oksjonid') && !seen.has(href)) {
                seen.add(href);
                auctions.push({ url: href, name: text || href.split('/').pop() });
            }
        }
        return auctions;
    }""")


def _scrape_archive_page(page) -> list[dict]:
    """Extract lots from a Vaal archive auction page."""
    return page.evaluate(r"""() => {
        const body = document.body.textContent;
        const lots = [];
        const pattern = /(\d{1,3})\.\s+([^\n]+?)\s*(?:\(([\d–\-]+)\))?\s*\n\s*Alghind\s+([\d.,]+)\s*EUR(?:\s*Haamrihind\s+([\d.,]+)\s*EUR)?/g;
        let m;
        while ((m = pattern.exec(body)) !== null) {
            lots.push({
                lot_number: parseInt(m[1]),
                author: m[2].trim(),
                birth_death: m[3] || '',
                start_price_str: m[4],
                end_price_str: m[5] || '',
            });
        }
        return lots;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("vaal_archive")
    seen_keys = {(l.get("author", ""), str(l.get("lot_number", "")), l.get("auction_name", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to Vaal archive index...")
        safe_navigate(page, INDEX_URL)
        time.sleep(2)

        auction_links = _get_auction_links(page)
        log.info("Found %d archive auctions", len(auction_links))

        for auc in auction_links:
            auc_name = auc["name"]
            auction_year = parse_year_from_text(auc["url"]) or parse_year_from_text(auc_name)

            log.info("Processing: %s", auc_name)
            try:
                safe_navigate(page, auc["url"])
                time.sleep(1.5)
            except Exception as e:
                log.warning("  Failed to load %s: %s", auc["url"], e)
                continue

            raw_lots = _scrape_archive_page(page)
            log.info("  %d lots in %s", len(raw_lots), auc_name)

            for raw in raw_lots:
                key = (raw.get("author", ""), str(raw.get("lot_number", "")), auc_name)
                if key in seen_keys:
                    continue

                start_price = int(float(raw.get("start_price_str", "0").replace(",", ".")))
                end_price = int(float(raw.get("end_price_str", "0").replace(",", "."))) if raw.get("end_price_str") else 0

                lot = {
                    "auction_provider": "vaal",
                    "author": raw.get("author", "Unknown"),
                    "title": "",
                    "year": None,
                    "tech": "",
                    "dimensions_raw": "",
                    "dimension": None,
                    "start_price": start_price,
                    "end_price": end_price,
                    "bid_count": None,
                    "auction_name": auc_name,
                    "auction_date": auction_year or 0,
                    "image_url": None,
                    "source_url": auc["url"],
                    "sold": end_price > 0,
                    "lot_number": raw.get("lot_number"),
                }

                lots.append(lot)
                seen_keys.add(key)

            save_checkpoint(lots, "vaal_archive")

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

            time.sleep(1)

        lots = deduplicate(lots)
        save_checkpoint(lots, "vaal_archive")
        log.info("Vaal archive scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
