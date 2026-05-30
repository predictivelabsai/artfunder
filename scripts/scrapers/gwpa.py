"""GWPA (Grev Wedels Plass Auksjoner) scraper — Norway's premier auction house.

Auctions since 1994, /en/auctions/{id} pattern.
Lots as links with inline "Hammer priceNOK X,XXX" text.
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

BASE_URL = "https://gwpa.no"
NOK_TO_EUR = 0.087


def _get_auction_list(page) -> list[dict]:
    """Get all auction links from /en/auctions."""
    return page.evaluate(r"""() => {
        const links = [...document.querySelectorAll('a')];
        const auctions = [];
        const seen = new Set();
        for (const a of links) {
            const m = a.href.match(/\/en\/auctions\/(\d+)/);
            if (m && !seen.has(m[1])) {
                seen.add(m[1]);
                auctions.push({
                    id: parseInt(m[1]),
                    url: a.href,
                    name: a.textContent.trim().substring(0, 100)
                });
            }
        }
        return auctions.sort((a, b) => b.id - a.id);
    }""")


def _scrape_auction_page(page) -> list[dict]:
    """Extract lots from a GWPA auction page."""
    return page.evaluate(r"""() => {
        const links = [...document.querySelectorAll('a[href*="/lots/"]')];
        const lots = [];
        const seen = new Set();
        for (const a of links) {
            if (seen.has(a.href)) continue;
            seen.add(a.href);

            const text = a.textContent.replace(/\s+/g, ' ').trim();

            // Parse lot number at start
            const lotMatch = text.match(/^(\d+)/);
            const lotNum = lotMatch ? parseInt(lotMatch[1]) : null;

            // Parse author: "Name, First(YYYY-YYYY)"
            const authorMatch = text.match(/\d+\s*(.+?)\((\d{4})-/);
            let author = authorMatch ? authorMatch[1].trim().replace(/,$/, '') : '';
            if (!author) {
                const simpleAuthor = text.match(/\d+\s*([^(]+)/);
                author = simpleAuthor ? simpleAuthor[1].trim() : '';
            }

            // Parse title after author section
            const titleMatch = text.match(/\)\s*(.+?)(?:Oil|Watercolor|Pastel|Mixed|Acrylic|Print|Lithograph|Gouache|Pencil|Charcoal|Ink|Bronze|Wood|Estimate|Hammer)/i);
            let title = titleMatch ? titleMatch[1].trim() : '';

            // Parse medium/technique
            const techMatch = text.match(/(Oil on canvas|Oil on panel|Oil on board|Watercolor|Pastel|Mixed media|Acrylic|Print|Lithograph|Gouache|Pencil|Charcoal|Ink on paper|Bronze|Wood)/i);
            let tech = techMatch ? techMatch[1] : '';

            // Parse dimensions
            const dimMatch = text.match(/(\d+)\s*x\s*(\d+)/);
            let dims = dimMatch ? `${dimMatch[1]}x${dimMatch[2]}` : '';

            // Parse hammer price: "Hammer priceNOK X,XXX" or "Hammer price NOK X,XXX"
            const priceMatch = text.match(/Hammer\s*price\s*(?:NOK\s*)?([\d,.\s]+)/i);
            let price = 0;
            if (priceMatch) {
                price = parseInt(priceMatch[1].replace(/[,.\s]/g, '')) || 0;
                price = Math.round(price * 0.087);  // NOK to EUR
            }

            const sold = price > 0;

            // Get image
            const img = a.querySelector('img');

            if (author || lotNum) {
                lots.push({
                    lot_number: lotNum,
                    author: author.substring(0, 200),
                    title: title.substring(0, 200),
                    tech: tech,
                    dimensions_raw: dims,
                    end_price: price,
                    sold: sold,
                    image_url: img ? img.src : null,
                    source_url: a.href,
                });
            }
        }
        return lots;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("gwpa")
    seen_keys = {(str(l.get("lot_number", "")), l.get("auction_name", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to GWPA auctions...")
        safe_navigate(page, f"{BASE_URL}/en/auctions")
        time.sleep(2)
        dismiss_cookies(page)

        auction_list = _get_auction_list(page)
        log.info("Found %d auctions", len(auction_list))

        # Also scan IDs not found on the listing page
        if auction_list:
            max_id = max(a["id"] for a in auction_list)
            known_ids = {a["id"] for a in auction_list}
            for i in range(1, max_id + 1):
                if i not in known_ids:
                    auction_list.append({"id": i, "url": f"{BASE_URL}/en/auctions/{i}", "name": f"Auction {i}"})
            auction_list.sort(key=lambda a: a["id"], reverse=True)

        for auc in auction_list:
            auc_name = auc["name"] or f"Auction {auc['id']}"
            log.info("Processing: %s (id=%d)", auc_name[:40], auc["id"])

            try:
                safe_navigate(page, auc["url"])
                time.sleep(1.5)
            except Exception as e:
                log.warning("  Failed: %s", e)
                continue

            title = page.title()
            if "404" in title or "Not Found" in title:
                continue

            auction_year = parse_year_from_text(title) or parse_year_from_text(auc_name)

            raw_lots = _scrape_auction_page(page)
            if not raw_lots:
                continue

            log.info("  %d lots in %s", len(raw_lots), auc_name[:40])

            for raw in raw_lots:
                key = (str(raw.get("lot_number", "")), auc_name)
                if key in seen_keys:
                    continue

                dims_raw = raw.get("dimensions_raw", "")
                dim_area, dims_clean = parse_dimensions(dims_raw) if dims_raw else (None, "")

                lot = {
                    "auction_provider": "gwpa",
                    "country": "NO",
                    "author": _clean(raw.get("author", "Unknown"), 255) or "Unknown",
                    "title": _clean(raw.get("title", ""), 500),
                    "year": None,
                    "tech": _clean(raw.get("tech", ""), 255),
                    "dimensions_raw": _clean(dims_clean, 100),
                    "dimension": dim_area,
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

            save_checkpoint(lots, "gwpa")

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

            time.sleep(1)

        lots = deduplicate(lots)
        save_checkpoint(lots, "gwpa")
        log.info("GWPA scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
