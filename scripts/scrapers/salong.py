"""E-Kunstisalong scraper — Tartu gallery with 57 auctions (1997-present).

Structure:
- Index: /E-kunstisalongi_oksjonid_756 lists all auctions with links
- Each auction page has lots inline with images
- Format: "AuthorN. Title Year. Tech, medium. Dims. Alg: € X, lõpp: € Y"
- Some pages may have pagination via /page/N suffix
"""

from __future__ import annotations

import logging
import re
import time

from scripts.scrapers.base import (
    parse_price, parse_dimensions, parse_year_from_text,
    setup_browser, dismiss_cookies, save_checkpoint, load_checkpoint,
    deduplicate, safe_navigate,
)

log = logging.getLogger(__name__)

BASE_URL = "https://www.e-kunstisalong.ee"
INDEX_URL = f"{BASE_URL}/E-kunstisalongi_oksjonid_756"


def _get_auction_links(page) -> list[dict]:
    """Get all auction page links from the index."""
    return page.evaluate(r"""() => {
        const links = [...document.querySelectorAll('a')];
        const auctions = [];
        const seen = new Set();
        for (const a of links) {
            const href = a.href;
            if (href.includes('oksjon') && href.includes('e-kunstisalong.ee')
                && !href.includes('oksjonid_756') && !href.includes('osalejale')
                && !href.includes('juhend') && !href.includes('toojale')
                && !href.includes('2026_oksjonid')
                && !seen.has(href)) {
                seen.add(href);
                const text = a.textContent.trim() || href.split('/').pop().split('_')[0];
                auctions.push({ url: href, name: text });
            }
        }
        return auctions;
    }""")


def _scrape_auction_page(page) -> list[dict]:
    """Extract lots from a Salong auction page."""
    return page.evaluate(r"""() => {
        const body = document.body.textContent;
        const lots = [];

        // Pattern: "AuthorN. Title Year. Tech. Dims. Alg: € X[, lõpp: € Y]"
        const pattern = /([A-ZÄÖÜÕŠŽ][a-zäöüõšž]+(?:\s+[A-ZÄÖÜÕŠŽ][a-zäöüõšž-]+)*)(\d+)\.\s+(.+?)\s+(\d{4})[\.\s]+([^.]+?)(?:\.\s*(?:Ava\s+)?(\d[\d,]*\s*x\s*\d[\d,]*))?\.\s*(?:Signatuuriga|Signatuurita|Sig\.|E\.A\.)?\s*(?:\.\s*)?Alg:\s*€\s*([\d\s]+)(?:,\s*lõpp:\s*€\s*([\d\s]+))?/g;

        let m;
        while ((m = pattern.exec(body)) !== null) {
            lots.push({
                author: m[1].trim(),
                lot_number: parseInt(m[2]),
                title: m[3].trim(),
                year: parseInt(m[4]),
                tech: m[5].trim(),
                dimensions_raw: m[6] ? m[6].trim() : '',
                start_price_text: m[7].trim(),
                end_price_text: m[8] ? m[8].trim() : '',
            });
        }

        // Fallback: simpler pattern if the complex one fails
        if (lots.length === 0) {
            const simple = /Alg:\s*€\s*([\d\s]+)(?:,\s*lõpp:\s*€\s*([\d\s]+))?/g;
            let idx = 0;
            let s;
            while ((s = simple.exec(body)) !== null) {
                // Extract author from context before this match
                const before = body.substring(Math.max(0, s.index - 200), s.index);
                const authorMatch = before.match(/([A-ZÄÖÜÕŠŽ][a-zäöüõšž]+(?:\s+[A-ZÄÖÜÕŠŽ][a-zäöüõšž-]+)*)\s*\d+\.\s/);
                const numMatch = before.match(/(\d+)\.\s+([^\n]*?)$/);

                lots.push({
                    author: authorMatch ? authorMatch[1].trim() : 'Unknown',
                    lot_number: numMatch ? parseInt(numMatch[1]) : null,
                    title: numMatch ? numMatch[2].trim().substring(0, 100) : '',
                    year: null,
                    tech: '',
                    dimensions_raw: '',
                    start_price_text: s[1].trim(),
                    end_price_text: s[2] ? s[2].trim() : '',
                });
                idx++;
            }
        }

        return lots;
    }""")


def _check_pagination(page) -> list[str]:
    """Check if the auction page has pagination and return additional page URLs."""
    return page.evaluate(r"""() => {
        const links = [...document.querySelectorAll('a')];
        const pages = [];
        const seen = new Set([window.location.href]);
        for (const a of links) {
            if (a.href.includes('/page/') && a.href.includes('oksjon') && !seen.has(a.href)) {
                seen.add(a.href);
                pages.push(a.href);
            }
        }
        return pages;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("salong")
    seen_keys = {(l.get("author", ""), str(l.get("lot_number", "")), l.get("auction_name", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to E-Kunstisalong index...")
        safe_navigate(page, INDEX_URL)
        time.sleep(2)
        dismiss_cookies(page)

        auction_links = _get_auction_links(page)
        log.info("Found %d auction pages", len(auction_links))

        for auc in auction_links:
            auc_name = auc["name"] or auc["url"].split("/")[-1]
            auction_year = parse_year_from_text(auc["url"]) or parse_year_from_text(auc_name)

            log.info("Processing: %s", auc_name)
            try:
                safe_navigate(page, auc["url"])
                time.sleep(2)
            except Exception as e:
                log.warning("  Failed to load %s: %s", auc["url"], e)
                continue

            # Scrape main page
            raw_lots = _scrape_auction_page(page)

            # Check for pagination and scrape additional pages
            extra_pages = _check_pagination(page)
            for extra_url in extra_pages:
                log.info("  Pagination: %s", extra_url)
                try:
                    safe_navigate(page, extra_url)
                    time.sleep(1.5)
                    raw_lots.extend(_scrape_auction_page(page))
                except Exception as e:
                    log.warning("  Failed pagination page: %s", e)

            log.info("  %d lots in %s", len(raw_lots), auc_name)

            for raw in raw_lots:
                key = (raw.get("author", ""), str(raw.get("lot_number", "")), auc_name)
                if key in seen_keys:
                    continue

                start_price = parse_price(raw.get("start_price_text", ""))
                end_price = parse_price(raw.get("end_price_text", ""))
                dims_raw = raw.get("dimensions_raw", "")
                dim_area, dims_clean = parse_dimensions(dims_raw) if dims_raw else (None, "")

                lot = {
                    "auction_provider": "salong",
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
                    "sold": end_price > 0,
                    "lot_number": raw.get("lot_number"),
                }

                lots.append(lot)
                seen_keys.add(key)

            save_checkpoint(lots, "salong")

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

            time.sleep(1.5)

        lots = deduplicate(lots)
        save_checkpoint(lots, "salong")
        log.info("E-Kunstisalong scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
