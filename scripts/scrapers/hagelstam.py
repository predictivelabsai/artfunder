"""Hagelstam & Co scraper — Finland's oldest auction house, 162K+ lots.

Structure: /paattyneet-huutokaupat lists completed auctions.
Each auction has categories (taide, veistokset, design, etc.).
Lots as .product-item-info with .product-name, .hammer-price, .start-price.
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

BASE_URL = "https://www.hagelstam.fi"
INDEX_URL = f"{BASE_URL}/paattyneet-huutokaupat"


def _get_auction_links(page) -> list[dict]:
    """Get all completed auction category page links."""
    return page.evaluate(r"""() => {
        const links = [...document.querySelectorAll('a')];
        const auctions = [];
        const seen = new Set();
        for (const a of links) {
            const href = a.href;
            const text = a.textContent.trim();
            if (href.includes('/huutokaupat/') && !href.endsWith('paattyneet-huutokaupat')
                && !href.includes('#') && href.includes('hagelstam.fi')
                && !seen.has(href)) {
                seen.add(href);
                auctions.push({ url: href, name: text.substring(0, 80) });
            }
        }
        return auctions;
    }""")


def _scrape_category_page(page) -> list[dict]:
    """Extract lots from a Hagelstam auction category page."""
    return page.evaluate(r"""() => {
        const items = document.querySelectorAll('.product-item-info');
        const lots = [];
        for (const item of items) {
            const nameEl = item.querySelector('.product-name');
            const hammerEl = item.querySelector('.hammer-price');
            const startEl = item.querySelector('.start-price');
            const imgEl = item.querySelector('img');
            const linkEl = item.querySelector('a');

            const nameText = nameEl ? nameEl.textContent.trim() : '';
            const hammerText = hammerEl ? hammerEl.textContent.trim() : '';
            const startText = startEl ? startEl.textContent.trim() : '';

            // Parse lot number and author from name: "123. Author Name*"
            const lotMatch = nameText.match(/^(\d+)\.\s*(.+?)(\*?)$/);
            const lotNum = lotMatch ? parseInt(lotMatch[1]) : null;
            let author = lotMatch ? lotMatch[2].trim() : nameText;

            // Parse hammer price
            const hpMatch = hammerText.match(/([\d\s]+)\s*€/);
            const hammerPrice = hpMatch ? hpMatch[1].replace(/\s/g, '') : '0';

            // Parse start price
            const spMatch = startText.match(/([\d\s]+)\s*€/);
            const startPrice = spMatch ? spMatch[1].replace(/\s/g, '') : '0';

            // Unsold if hammer says "-" or no price
            const unsold = hammerText.includes('-') && !hpMatch;

            lots.push({
                lot_number: lotNum,
                author: author,
                end_price: parseInt(hammerPrice) || 0,
                start_price: parseInt(startPrice) || 0,
                sold: !unsold && parseInt(hammerPrice) > 0,
                image_url: imgEl ? imgEl.src : null,
                source_url: linkEl ? linkEl.href : null,
            });
        }
        return lots;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("hagelstam")
    seen_keys = {(l.get("author", ""), str(l.get("lot_number", "")), l.get("auction_name", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to Hagelstam completed auctions...")
        safe_navigate(page, INDEX_URL)
        time.sleep(2)
        dismiss_cookies(page)

        auction_links = _get_auction_links(page)
        log.info("Found %d auction/category pages", len(auction_links))

        for auc in auction_links:
            auc_name = auc["name"] or auc["url"].split("/")[-1]
            auction_year = parse_year_from_text(auc_name) or parse_year_from_text(auc["url"])

            # Skip parent auction links (only scrape category sub-pages with lots)
            if auc_name in ("Toggle",) or not auc_name:
                continue

            log.info("Processing: %s", auc_name[:60])
            try:
                safe_navigate(page, auc["url"])
                time.sleep(1.5)
            except Exception as e:
                log.warning("  Failed to load %s: %s", auc["url"], e)
                continue

            raw_lots = _scrape_category_page(page)
            log.info("  %d lots in %s", len(raw_lots), auc_name[:40])

            for raw in raw_lots:
                key = (raw.get("author", ""), str(raw.get("lot_number", "")), auc_name)
                if key in seen_keys:
                    continue

                lot = {
                    "auction_provider": "hagelstam",
                    "country": "FI",
                    "author": _clean(raw.get("author", "Unknown"), 255) or "Unknown",
                    "title": "",
                    "year": None,
                    "tech": "",
                    "dimensions_raw": "",
                    "dimension": None,
                    "start_price": raw.get("start_price", 0),
                    "end_price": raw.get("end_price", 0),
                    "bid_count": None,
                    "auction_name": _clean(auc_name, 255),
                    "auction_date": auction_year or 0,
                    "image_url": raw.get("image_url"),
                    "source_url": raw.get("source_url"),
                    "sold": raw.get("sold", False),
                    "lot_number": raw.get("lot_number"),
                }

                lots.append(lot)
                seen_keys.add(key)

            save_checkpoint(lots, "hagelstam")

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

            time.sleep(1)

        lots = deduplicate(lots)
        save_checkpoint(lots, "hagelstam")
        log.info("Hagelstam scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
