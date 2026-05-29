"""Vaal Galerii scraper — catalog pages with inline lot data (2008-present).

Structure:
- Index /oksjonid lists auction seasons + archive links
- Each catalog page has lots inline: technique, lot#, title, author, Alghind, Haamrihind
- Detail pages at /oksjonid/teos?ID (optional, for dimensions/image)
"""

from __future__ import annotations

import logging
import re
import time

from scripts.scrapers.base import (
    parse_price, parse_dimensions, parse_year_from_text, decade_from_year,
    setup_browser, dismiss_cookies, save_checkpoint, load_checkpoint,
    deduplicate, safe_navigate,
)

log = logging.getLogger(__name__)

BASE_URL = "https://www.vaal.ee"
INDEX_URL = f"{BASE_URL}/oksjonid"


def _get_auction_links(page) -> list[dict]:
    """Get all past auction catalog links from the index page."""
    return page.evaluate("""() => {
        const links = [...document.querySelectorAll('a')];
        const auctions = [];
        const seen = new Set();

        for (const a of links) {
            const href = a.href;
            const text = a.textContent.trim();
            // Match patterns like /oksjonid/2025-sugisoksjon or /oksjonid/2024-kevadoksjon
            if (href.match(/\\/oksjonid\\/\\d{4}-(kevad|sugis|talve|suve|joulud?)oksjon/) && !seen.has(href)) {
                seen.add(href);
                auctions.push({ url: href, name: text || href.split('/').pop() });
            }
        }

        // Also look for numbered archive auctions like "62. 2021 kevadoksjon"
        const bodyText = document.body.textContent;
        const archiveMatches = bodyText.matchAll(/(\\d+)\\.\\s+(\\d{4})\\s+(\\w+oksjon)/g);
        // These may not have direct links, but the pattern helps us know what exists

        return auctions;
    }""")


def _scrape_catalog_page(page) -> list[dict]:
    """Extract all lots from a Vaal catalog page."""
    return page.evaluate("""() => {
        const lots = [];
        // Vaal lots are in links to /oksjonid/teos?ID
        const teosLinks = document.querySelectorAll('a[href*="/oksjonid/teos?"]');

        for (const a of teosLinks) {
            const text = a.textContent.replace(/\\s+/g, ' ').trim();
            const href = a.href;

            // Parse: "technique LOT#. Title Author Alghind: X € Haamrihind: Y € Vaata lähemalt"
            const lotMatch = text.match(/(\\d+)\\./);
            const algMatch = text.match(/Alghind:\\s*([\\d\\s]+)\\s*€/);
            const hamMatch = text.match(/Haamrihind:\\s*([\\d\\s]+)\\s*€/);

            // The text before the lot number is the technique
            let tech = '';
            let title = '';
            let author = '';

            if (lotMatch) {
                const beforeLot = text.substring(0, text.indexOf(lotMatch[0])).trim();
                tech = beforeLot;

                // After lot number, before "Alghind" is "Title Author"
                const afterLot = text.substring(text.indexOf(lotMatch[0]) + lotMatch[0].length);
                const titleAuthor = afterLot.split(/Alghind/)[0].replace('Vaata lähemalt', '').trim();

                // Heuristic: last two+ capitalized words are the author
                const words = titleAuthor.split(/\\s+/);
                // Find where author name starts (usually 2-3 words from end before Alghind)
                // Better heuristic: look for name pattern at end
                const nameMatch = titleAuthor.match(/([A-ZÄÖÜÕ][a-zäöüõ]+(?:\\s+[A-ZÄÖÜÕ][a-zäöüõ]+)+)\\s*$/);
                if (nameMatch) {
                    author = nameMatch[1];
                    title = titleAuthor.substring(0, titleAuthor.lastIndexOf(author)).trim();
                } else {
                    title = titleAuthor;
                }
            }

            // Get image from the lot area
            const parent = a.closest('div, li, article') || a.parentElement;
            const img = parent ? parent.querySelector('img') : null;
            const imgSrc = img ? (img.getAttribute('data-src') || img.src) : '';

            lots.push({
                source_url: href,
                lot_number: lotMatch ? parseInt(lotMatch[1]) : null,
                tech: tech,
                title: title,
                author: author,
                start_price_text: algMatch ? algMatch[1].trim() : '',
                end_price_text: hamMatch ? hamMatch[1].trim() : '',
                image_url: imgSrc,
                raw_text: text.substring(0, 300),
            });
        }

        return lots;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("vaal")
    seen_urls = {l.get("source_url") for l in lots if l.get("source_url")}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to Vaal index...")
        safe_navigate(page, INDEX_URL)
        time.sleep(2)
        dismiss_cookies(page)

        auction_links = _get_auction_links(page)
        log.info("Found %d auction catalogs", len(auction_links))

        for auc in auction_links:
            auc_name = auc["name"]
            auction_year = parse_year_from_text(auc["url"])

            log.info("Processing: %s", auc_name)
            safe_navigate(page, auc["url"])
            time.sleep(1.5)

            raw_lots = _scrape_catalog_page(page)
            log.info("  %d lots in %s", len(raw_lots), auc_name)

            for raw in raw_lots:
                src_url = raw.get("source_url", "")
                if src_url in seen_urls:
                    continue

                start_price = parse_price(raw.get("start_price_text", ""))
                end_price = parse_price(raw.get("end_price_text", ""))

                lot = {
                    "auction_provider": "vaal",
                    "author": raw.get("author", "").strip() or "Unknown",
                    "title": raw.get("title", "").strip(),
                    "year": None,
                    "tech": raw.get("tech", "").strip(),
                    "dimensions_raw": "",
                    "dimension": None,
                    "start_price": start_price,
                    "end_price": end_price,
                    "bid_count": None,
                    "auction_name": auc_name,
                    "auction_date": auction_year or 0,
                    "image_url": raw.get("image_url") or None,
                    "source_url": src_url,
                    "sold": end_price > 0,
                    "lot_number": raw.get("lot_number"),
                }

                lots.append(lot)
                seen_urls.add(src_url)

            save_checkpoint(lots, "vaal")

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

            time.sleep(1)

        lots = deduplicate(lots)
        save_checkpoint(lots, "vaal")
        log.info("Vaal scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
