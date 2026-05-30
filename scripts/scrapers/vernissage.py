"""Vernissage Galerii scraper — WordPress auction posts (2007-present).

Format per lot on each auction page:
"Kevadoksjon 2025 Author. Title.Year. Tech, medium. Dims. Alghind: X € [Haamrihind: Y €] [MÜÜDUD] Loe edasi"
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

BASE_URL = "https://vernissage.ee"
INDEX_URL = f"{BASE_URL}/toimunud-oksjonid/"


def _get_auction_links(page) -> list[dict]:
    """Get all past auction page links from the index."""
    return page.evaluate(r"""() => {
        const links = [...document.querySelectorAll('a')];
        const auctions = [];
        const seen = new Set();

        for (const a of links) {
            const href = a.href;
            const text = a.textContent.trim();
            if ((href.includes('kevadoksjon') || href.includes('sugisoksjon') ||
                 href.includes('oksjon-2') || href.includes('klassika'))
                && !href.includes('toimunud') && !href.includes('#')

                && href.startsWith('https://vernissage.ee/')
                && !href.includes('tootekategooria')
                && !seen.has(href)) {
                seen.add(href);
                auctions.push({ url: href, name: text || href.split('/').pop() });
            }
        }
        return auctions;
    }""")


def _scrape_auction_page(page) -> list[dict]:
    """Extract lots from a Vernissage auction post page using Alghind markers."""
    return page.evaluate(r"""() => {
        const body = document.body.textContent;
        const lots = [];

        // Find all "Alghind:" positions and extract context before each
        let idx = 0;
        while ((idx = body.indexOf('Alghind', idx)) !== -1) {
            // Get 300 chars before Alghind and 150 after
            const before = body.substring(Math.max(0, idx - 300), idx);
            const after = body.substring(idx, Math.min(body.length, idx + 150));

            // Parse Alghind and Haamrihind from "after"
            const algMatch = after.match(/Alghind:?\s*([\d\s]+)\s*€/);
            const hamMatch = after.match(/Haamrihind:?\s*([\d\s]+)\s*€/);
            const sold = after.includes('MÜÜDUD') || !!hamMatch;

            // Parse author, title, year, tech from "before"
            // Format: "... Author. Title.Year. Tech, medium. Dims."
            // Work backwards from the end of "before"
            const cleaned = before.replace(/Loe edasi\s*/g, '').replace(/Kevadoksjon \d+\s*/g, '').replace(/Sügisoksjon \d+\s*/g, '').trim();

            // Split on periods to find components
            // The last chunk before Alghind typically has dims
            // Before that: tech, medium
            // Before that: Year
            // Before that: Title
            // First: Author

            // Try regex: "Author. Title. Year. Tech. Dims."
            // or "Author. Title.Year. Tech, medium. Dims."
            const parts = cleaned.split(/\.\s*/);

            let author = '', title = '', year = null, tech = '', dims = '';

            if (parts.length >= 3) {
                // Work from the end - last parts are dims, tech, year
                // Find the year (4-digit number)
                let yearIdx = -1;
                for (let i = parts.length - 1; i >= 0; i--) {
                    const ym = parts[i].match(/^(1[89]\d{2}|20[0-3]\d)/);
                    if (ym) {
                        yearIdx = i;
                        year = parseInt(ym[1]);
                        break;
                    }
                }

                if (yearIdx >= 0) {
                    // Everything before year index is author + title
                    const authorTitle = parts.slice(0, yearIdx).join('. ').trim();
                    // First word group is author (usually "Firstname Lastname")
                    // Try to split at the last name boundary
                    const atParts = authorTitle.split('. ');
                    if (atParts.length >= 2) {
                        author = atParts[0].trim();
                        title = atParts.slice(1).join('. ').trim();
                    } else {
                        author = authorTitle;
                    }

                    // Everything after year is tech + dims
                    const afterYear = parts.slice(yearIdx + 1).join('. ').trim();
                    // Dims pattern
                    const dimMatch = afterYear.match(/([\d,]+\s*[x×]\s*[\d,]+\s*(?:cm)?)/);
                    if (dimMatch) {
                        dims = dimMatch[1];
                        tech = afterYear.substring(0, afterYear.indexOf(dimMatch[0])).replace(/\.\s*$/, '').trim();
                    } else {
                        tech = afterYear;
                    }
                } else {
                    // No year found - just take first part as author
                    author = parts[0].trim();
                    title = parts.slice(1).join('. ').trim();
                }
            } else if (parts.length >= 1) {
                author = parts[0].trim();
            }

            // Clean up author (remove "Kevadoksjon" prefixes etc)
            author = author.replace(/^(?:Kevad|Sügis|Talve)oksjon\s+\d+\s*/i, '').trim();

            if (author) {
                lots.push({
                    author, title, year, tech, dimensions_raw: dims,
                    start_price_text: algMatch ? algMatch[1].trim() : '',
                    end_price_text: hamMatch ? hamMatch[1].trim() : '',
                    sold,
                });
            }

            idx += 7;
        }

        return lots;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("vernissage")
    seen_keys = {(l.get("author", ""), l.get("title", ""), l.get("auction_name", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to Vernissage index...")
        safe_navigate(page, INDEX_URL)
        time.sleep(2)
        dismiss_cookies(page)

        auction_links = _get_auction_links(page)
        log.info("Found %d auction pages", len(auction_links))

        for auc in auction_links:
            auc_name = auc["name"] or auc["url"].split("/")[-2]
            auction_year = parse_year_from_text(auc["url"]) or parse_year_from_text(auc_name)

            log.info("Processing: %s", auc_name)
            try:
                safe_navigate(page, auc["url"])
                time.sleep(2)
            except Exception as e:
                log.warning("  Failed to load %s: %s", auc["url"], e)
                continue

            raw_lots = _scrape_auction_page(page)
            log.info("  %d lots in %s", len(raw_lots), auc_name)

            for raw in raw_lots:
                key = (raw.get("author", ""), raw.get("title", ""), auc_name)
                if key in seen_keys:
                    continue

                start_price = parse_price(raw.get("start_price_text", ""))
                end_price = parse_price(raw.get("end_price_text", ""))
                dims_raw = raw.get("dimensions_raw", "")
                dim_area, dims_clean = parse_dimensions(dims_raw) if dims_raw else (None, "")

                lot = {
                    "auction_provider": "vernissage",
                    "author": raw.get("author", "Unknown"),
                    "title": raw.get("title", ""),
                    "year": raw.get("year"),
                    "tech": raw.get("tech", ""),
                    "dimensions_raw": dims_clean,
                    "dimension": dim_area,
                    "start_price": start_price,
                    "end_price": end_price,
                    "bid_count": None,
                    "auction_name": auc_name,
                    "auction_date": auction_year or 0,
                    "image_url": None,
                    "source_url": auc["url"],
                    "sold": raw.get("sold", end_price > 0),
                    "lot_number": None,
                }

                lots.append(lot)
                seen_keys.add(key)

            save_checkpoint(lots, "vernissage")

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

            time.sleep(1.5)

        lots = deduplicate(lots)
        save_checkpoint(lots, "vernissage")
        log.info("Vernissage scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
