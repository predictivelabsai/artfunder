"""Haus Galerii scraper — sales statistics archive (1997-present).

Haus has the largest Estonian auction archive. Data is loaded via a GET search
form at haus.ee/?c=sales-statistics. Each .artwork div has structured HTML:
  em.aut       → author
  strong.title → title + span.year
  p.tech       → technique + dimensions
  p.ok         → auction name + date
  div.price    → starting/final price
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

BASE_URL = "https://haus.ee"
SEARCH_URL = f"{BASE_URL}/?c=sales-statistics&l=en&_order=ok_date.dsc&ps=250&_s=1"


def _extract_lots(page) -> list[dict]:
    """Extract all .artwork items from the current page."""
    return page.evaluate("""() => {
        const items = document.querySelectorAll('.artwork.ok');
        return [...items].map(el => {
            // Structured selectors matching actual Haus HTML
            const aut = el.querySelector('em.aut');
            const titleEl = el.querySelector('strong.title');
            const yearEl = el.querySelector('span.year');
            const techEl = el.querySelector('p.tech');
            const okEl = el.querySelector('p.ok');
            const timeEl = el.querySelector('time');
            const priceEls = el.querySelectorAll('div.price strong.price');

            const author = aut ? aut.textContent.trim() : '';
            let title = '';
            if (titleEl) {
                title = titleEl.textContent.trim();
                // Remove year from title text
                if (yearEl) title = title.replace(yearEl.textContent.trim(), '').replace(/\\.\\s*$/, '').trim();
            }
            const year_str = yearEl ? yearEl.textContent.trim() : '';
            const techDims = techEl ? techEl.textContent.trim() : '';
            const auctionName = okEl ? okEl.querySelector('strong')?.textContent?.trim() || '' : '';
            const auctionDate = timeEl ? timeEl.getAttribute('datetime') || timeEl.textContent.trim() : '';

            // Parse tech vs dimensions from "oil on canvas. 65.5 × 65.5 cm"
            let tech = techDims;
            let dims = '';
            const dimMatch = techDims.match(/([\\d.,]+\\s*[×x]\\s*[\\d.,]+\\s*(?:cm)?)/);
            if (dimMatch) {
                dims = dimMatch[1].trim();
                tech = techDims.substring(0, techDims.indexOf(dimMatch[0])).replace(/\\.\\s*$/, '').trim();
            }

            // Prices: first strong.price = starting, second = final
            let startPrice = '', finalPrice = '';
            if (priceEls.length >= 1) startPrice = priceEls[0].textContent.replace('€', '').trim();
            if (priceEls.length >= 2) finalPrice = priceEls[1].textContent.replace('€', '').trim();

            // Image
            const img = el.querySelector('img');
            const imgSrc = img ? img.src : '';

            // Detail link
            const link = el.querySelector('a[href*="item="]') || el.querySelector('a');
            const href = link ? link.href : '';

            return {
                author, title, year_str, tech, dimensions_raw: dims,
                start_price_str: startPrice, end_price_str: finalPrice,
                auction_name: auctionName, auction_date_str: auctionDate,
                image_url: imgSrc, source_url: href,
            };
        });
    }""")


def _parse_lot(raw: dict) -> dict:
    """Convert raw JS-extracted data into a normalized lot dict."""
    start_price = parse_price(raw.get("start_price_str", ""))
    end_price = parse_price(raw.get("end_price_str", ""))

    year = None
    year_str = raw.get("year_str", "")
    if year_str:
        try:
            year = int(float(year_str))
        except (ValueError, TypeError):
            year = parse_year_from_text(year_str)

    dim_area, dims_raw = parse_dimensions(raw.get("dimensions_raw", ""))

    # Parse auction date from "2017-07-05 12:57:00" or "05.07.2017"
    auction_date_str = raw.get("auction_date_str", "")
    auction_date = 0
    if auction_date_str:
        y = parse_year_from_text(auction_date_str)
        if y:
            auction_date = y

    return {
        "auction_provider": "haus",
        "author": raw.get("author", "").strip(),
        "title": raw.get("title", "").strip(),
        "year": year,
        "tech": raw.get("tech", "").strip(),
        "dimensions_raw": dims_raw,
        "dimension": dim_area,
        "start_price": start_price,
        "end_price": end_price,
        "bid_count": None,
        "auction_name": raw.get("auction_name", "").strip(),
        "auction_date": auction_date,
        "image_url": raw.get("image_url", "").strip() or None,
        "source_url": raw.get("source_url", "").strip() or None,
        "sold": end_price > 0,
    }


def _get_max_page(page) -> int:
    """Find the highest page number from pagination links."""
    return page.evaluate("""() => {
        const links = document.querySelectorAll('.pages a');
        let maxPage = 1;
        for (const a of links) {
            const m = a.href.match(/p=(\\d+)/);
            if (m) {
                const n = parseInt(m[1]);
                if (n > maxPage) maxPage = n;
            }
            // Also check text content for page numbers
            const num = parseInt(a.textContent.trim());
            if (!isNaN(num) && num > maxPage) maxPage = num;
        }
        return maxPage;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("haus")
    seen_urls = {l.get("source_url") for l in lots if l.get("source_url")}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to Haus sales statistics...")
        safe_navigate(page, SEARCH_URL)
        time.sleep(2)
        dismiss_cookies(page)

        max_page = _get_max_page(page)
        log.info("Detected %d pages", max_page)

        for page_num in range(1, max_page + 1):
            url = f"{SEARCH_URL}&p={page_num}"
            if page_num > 1:
                safe_navigate(page, url)
                time.sleep(2)

            raw_items = _extract_lots(page)
            if not raw_items:
                log.info("No items on page %d, stopping", page_num)
                break

            new_count = 0
            for raw in raw_items:
                lot = _parse_lot(raw)
                if not lot["author"]:
                    continue
                src = lot.get("source_url")
                if src and src in seen_urls:
                    continue
                lots.append(lot)
                if src:
                    seen_urls.add(src)
                new_count += 1

            log.info("Page %d/%d: %d items (%d new), total: %d",
                     page_num, max_page, len(raw_items), new_count, len(lots))

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

            if page_num % 10 == 0:
                save_checkpoint(lots, "haus")

            time.sleep(2)

        lots = deduplicate(lots)
        save_checkpoint(lots, "haus")
        log.info("Haus scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
