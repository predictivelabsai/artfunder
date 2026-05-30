"""Auctionet scraper — Sweden's largest online auction platform.

468K+ ended art items. Covers Stockholms Auktionsverk + Uppsala post-2021.
Listing pages: /en/search/25-art?is=ended&status=ended&page={N}
Item thumbs have title + sold/unsold status. Detail pages have hammer prices.
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

BASE_URL = "https://auctionet.com"
SEARCH_URL = f"{BASE_URL}/en/search/25-art?is=ended&status=ended&sort_order=end_desc"


def _scrape_listing_page(page) -> list[dict]:
    """Extract lot links and basic info from search results page."""
    return page.evaluate(r"""() => {
        const items = document.querySelectorAll('.item-thumb');
        const lots = [];
        for (const item of items) {
            const titleEl = item.querySelector('.item-thumb__title, .test-item-title');
            const priceEl = item.querySelector('.item-thumb__amount-label');
            const linkEl = item.querySelector('a');
            const imgEl = item.querySelector('img');

            const titleText = titleEl ? titleEl.textContent.trim() : '';
            const priceText = priceEl ? priceEl.textContent.trim() : '';
            const href = linkEl ? linkEl.href : '';

            // Parse lot number from title: "123. AUTHOR NAME. \"Title\"."
            const lotMatch = titleText.match(/^(\d+)\.\s*/);
            const lotNum = lotMatch ? parseInt(lotMatch[1]) : null;
            const rest = lotMatch ? titleText.substring(lotMatch[0].length) : titleText;

            // Parse author (usually in CAPS before period)
            let author = '', title = '';
            const authorMatch = rest.match(/^([A-ZÄÖÜÅÉÈÊËÀÂÏÎÔÛÙÜÇ\s.'-]+)\.\s*/);
            if (authorMatch) {
                author = authorMatch[1].trim();
                author = author.split(' ').map(w => w.charAt(0) + w.slice(1).toLowerCase()).join(' ');
                title = rest.substring(authorMatch[0].length).replace(/^[""]|[""]\.?$/g, '').trim();
            } else {
                author = rest.substring(0, 60);
            }

            const sold = !priceText.includes('Unsold');

            lots.push({
                lot_number: lotNum,
                author: author,
                title: title.substring(0, 200),
                sold: sold,
                source_url: href,
                image_url: imgEl ? imgEl.src : null,
                price_text: priceText,
            });
        }
        return lots;
    }""")


def _get_detail_price(page, url: str) -> int:
    """Visit a lot detail page and extract the hammer price."""
    try:
        safe_navigate(page, url)
        time.sleep(0.5)
        price = page.evaluate(r"""() => {
            const body = document.body.textContent;
            // Look for "Hammer price: X SEK" or "Klubbat: X SEK"
            const m = body.match(/(?:Hammer price|Klubbat|Slutpris)[:\s]*([\d\s]+)\s*(SEK|EUR)/i);
            if (m) return { price: m[1].replace(/\s/g, ''), currency: m[2] };
            // Try any "X SEK" near "hammer"
            const m2 = body.match(/([\d\s]+)\s*(SEK|EUR)\s*(?:inkl|incl|hammer)/i);
            if (m2) return { price: m2[1].replace(/\s/g, ''), currency: m2[2] };
            return null;
        }""")
        if price:
            val = int(price["price"]) if price["price"] else 0
            if price["currency"] == "SEK":
                val = int(val * 0.088)
            return val
    except Exception:
        pass
    return 0


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("auctionet")
    seen_keys = {(l.get("author", ""), l.get("title", ""), l.get("source_url", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to Auctionet art search...")

        max_pages = 200  # 48 items per page × 200 = ~9600 lots
        if limit:
            max_pages = min(max_pages, (limit // 48) + 1)

        for pg in range(1, max_pages + 1):
            url = f"{SEARCH_URL}&page={pg}"
            log.info("Page %d / %d", pg, max_pages)

            try:
                safe_navigate(page, url)
                time.sleep(1.5)
            except Exception as e:
                log.warning("  Failed page %d: %s", pg, e)
                break

            if pg == 1:
                dismiss_cookies(page)

            raw_lots = _scrape_listing_page(page)
            if not raw_lots:
                log.info("  No more lots on page %d, stopping", pg)
                break

            for raw in raw_lots:
                key = (raw.get("author", ""), raw.get("title", ""), raw.get("source_url", ""))
                if key in seen_keys:
                    continue

                # Extract auction info from URL: /events/{id}-{name}/{lot}
                auction_name = ""
                event_match = re.search(r"/events/(\d+)-([^/]+)/", raw.get("source_url", ""))
                if event_match:
                    auction_name = event_match.group(2).replace("-", " ").title()

                auction_year = parse_year_from_text(auction_name) or parse_year_from_text(raw.get("source_url", ""))

                lot = {
                    "auction_provider": "auctionet",
                    "country": "SE",
                    "author": _clean(raw.get("author", "Unknown"), 255) or "Unknown",
                    "title": _clean(raw.get("title", ""), 500),
                    "year": None,
                    "tech": "",
                    "dimensions_raw": "",
                    "dimension": None,
                    "start_price": 0,
                    "end_price": 0,
                    "bid_count": None,
                    "auction_name": _clean(auction_name, 255),
                    "auction_date": auction_year or 0,
                    "image_url": raw.get("image_url"),
                    "source_url": raw.get("source_url"),
                    "sold": raw.get("sold", False),
                    "lot_number": raw.get("lot_number"),
                }

                lots.append(lot)
                seen_keys.add(key)

            save_checkpoint(lots, "auctionet")

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

        lots = deduplicate(lots)
        save_checkpoint(lots, "auctionet")
        log.info("Auctionet scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
