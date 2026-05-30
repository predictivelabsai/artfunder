"""Bonhams scraper — major UK auction house with public results.

Past auctions at /auctions/results/, individual auctions at /auction/{id}/.
Light anti-bot protection.
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

BASE_URL = "https://www.bonhams.com"
GBP_TO_EUR = 1.17


def _get_past_auctions(page) -> list[dict]:
    """Get past auction links from results page."""
    return page.evaluate(r"""() => {
        const links = [...document.querySelectorAll('a')];
        const auctions = [];
        const seen = new Set();
        for (const a of links) {
            const m = a.href.match(/\/auction\/(\d+)\/?$/);
            if (m && !seen.has(m[1])) {
                seen.add(m[1]);
                auctions.push({
                    id: parseInt(m[1]),
                    url: a.href,
                    name: a.textContent.trim().substring(0, 100)
                });
            }
        }
        return auctions;
    }""")


def _scrape_auction_lots(page) -> list[dict]:
    """Extract lots from a Bonhams auction page."""
    return page.evaluate(r"""() => {
        // Find lot elements
        const items = document.querySelectorAll('[class*="lot"], [class*="item"], [class*="card"]');
        const lots = [];
        const seen = new Set();

        for (const item of items) {
            const text = item.textContent.replace(/\s+/g, ' ').trim();
            if (text.length < 20 || text.length > 1000) continue;

            const link = item.querySelector('a[href*="/lot/"]');
            if (!link || seen.has(link.href)) continue;
            seen.add(link.href);

            const img = item.querySelector('img');

            // Parse lot number
            const lotMatch = text.match(/Lot\s*(\d+)/i) || text.match(/^(\d+)\s/);
            const lotNum = lotMatch ? parseInt(lotMatch[1]) : null;

            // Parse price: "Sold for GBP X,XXX" or "£X,XXX" or "GBP X"
            const priceMatch = text.match(/(?:Sold for|Hammer|Price|£|GBP)\s*([\d,.\s]+)/i);
            let price = 0;
            if (priceMatch) {
                price = parseInt(priceMatch[1].replace(/[,.\s]/g, '')) || 0;
                price = Math.round(price * 1.17);  // GBP to EUR
            }

            // Parse author: usually first significant text
            let author = text.substring(0, 80).split('.')[0].split(',')[0].trim();
            // Remove lot number prefix
            author = author.replace(/^Lot\s*\d+\s*/i, '').replace(/^\d+\s*/, '').trim();

            const sold = text.includes('Sold') || price > 0;

            lots.push({
                lot_number: lotNum,
                author: author.substring(0, 200),
                title: '',
                end_price: price,
                sold: sold,
                image_url: img ? img.src : null,
                source_url: link.href,
            });
        }
        return lots;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("bonhams")
    seen_keys = {(str(l.get("lot_number", "")), l.get("auction_name", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to Bonhams results...")
        safe_navigate(page, f"{BASE_URL}/auctions/results/")
        time.sleep(3)
        dismiss_cookies(page)

        auctions = _get_past_auctions(page)
        log.info("Found %d past auctions", len(auctions))

        for auc in auctions:
            auc_name = auc["name"] or f"Auction {auc['id']}"
            log.info("Processing: %s", auc_name[:50])

            try:
                safe_navigate(page, auc["url"])
                time.sleep(2)
            except Exception as e:
                log.warning("  Failed: %s", e)
                continue

            title = page.title()
            if "404" in title:
                continue

            auction_year = parse_year_from_text(title) or parse_year_from_text(auc_name)

            raw_lots = _scrape_auction_lots(page)
            if not raw_lots:
                continue

            log.info("  %d lots", len(raw_lots))

            for raw in raw_lots:
                key = (str(raw.get("lot_number", "")), auc_name)
                if key in seen_keys:
                    continue

                lot = {
                    "auction_provider": "bonhams",
                    "country": "GB",
                    "author": _clean(raw.get("author", "Unknown"), 255) or "Unknown",
                    "title": _clean(raw.get("title", ""), 500),
                    "year": None,
                    "tech": "",
                    "dimensions_raw": "",
                    "dimension": None,
                    "start_price": 0,
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

            save_checkpoint(lots, "bonhams")

            if limit and len(lots) >= limit:
                break

            time.sleep(2)

        lots = deduplicate(lots)
        save_checkpoint(lots, "bonhams")
        log.info("Bonhams scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
