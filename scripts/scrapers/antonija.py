"""Antonija Classic Art Gallery scraper — Latvia's largest art auction house.

148 online auctions (2008-2026), ~15K+ lots with public hammer prices.
Structure: /en/auction/{1-148}, .nf-item divs, 20/page, /page-{N} pagination.
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

BASE_URL = "https://www.antonia.lv"
AUCTION_URL = f"{BASE_URL}/en/auction"
MAX_AUCTION = 148


def _get_max_page(page) -> int:
    """Find the last pagination page number."""
    return page.evaluate(r"""() => {
        const links = [...document.querySelectorAll('a')];
        let maxPage = 1;
        for (const a of links) {
            const m = a.textContent.trim().match(/^(\d+)$/);
            if (m && a.href.includes('page-')) {
                maxPage = Math.max(maxPage, parseInt(m[1]));
            }
        }
        return maxPage;
    }""")


def _scrape_page(page) -> list[dict]:
    """Extract lots from current page."""
    return page.evaluate(r"""() => {
        const items = document.querySelectorAll('.nf-item');
        const lots = [];
        for (const item of items) {
            const text = item.textContent;

            // Lot number
            const lotMatch = text.match(/Lot\s+(\d+)/);
            const lotNum = lotMatch ? parseInt(lotMatch[1]) : null;

            // Author from text after "Lot N - " (handle \xa0 non-breaking spaces)
            const cleanText = text.replace(/ /g, ' ');
            const authorMatch = cleanText.match(/Lot\s+\d+\s*-\s*(.+?)(?:\n|$)/);
            let author = authorMatch ? authorMatch[1].trim() : '';

            // Price: "800 EUR", "800 LVL", or "Ls 250"
            const priceMatch = cleanText.match(/([\d\s]+)\s*(EUR|LVL)/) ||
                               cleanText.match(/Ls\s+([\d\s]+)/);
            let priceText = priceMatch ? priceMatch[1].trim() : '0';
            let currency = (priceMatch && priceMatch[2]) ? priceMatch[2] : 'EUR';
            // Handle "Ls 250" format (Latvian Lats)
            if (cleanText.includes('Ls ') && !cleanText.match(/\d+\s*EUR/)) {
                const lsMatch = cleanText.match(/Ls\s+([\d\s]+)/);
                if (lsMatch) { priceText = lsMatch[1].trim(); currency = 'LVL'; }
            }
            // Skip "- EUR" (no result)
            if (priceText === '-' || priceText === '') priceText = '0';

            // Bid count
            const bidMatch = cleanText.match(/Bids:\s*(\d+)/);
            const bids = bidMatch ? parseInt(bidMatch[1]) : 0;

            // Sold status
            const sold = bids > 0;

            // Description (after "bidding is closed" line)
            const descMatch = cleanText.match(/bidding is closed\s*\n\s*([\s\S]*?)$/);
            let desc = descMatch ? descMatch[1].trim() : '';

            // Parse title and technique from description
            // Format: "Title, technique, WxH cm, year" or similar
            let title = '', tech = '', dimsRaw = '', year = null;
            if (desc) {
                const lines = desc.split('\n').map(l => l.trim()).filter(Boolean);
                const fullDesc = lines.join(', ');

                // Year at end
                const yearMatch = fullDesc.match(/\b(1[89]\d{2}|20[0-3]\d)\b/);
                if (yearMatch) year = parseInt(yearMatch[1]);

                // Dimensions
                const dimMatch = fullDesc.match(/([\d,]+\s*[x×]\s*[\d,]+\s*(?:cm)?)/);
                if (dimMatch) dimsRaw = dimMatch[1].trim();

                // First line is usually the title
                title = lines[0] || '';
                // Technique is usually after title
                if (lines.length >= 2) {
                    tech = lines.slice(1).join(', ').replace(dimsRaw, '').replace(/,\s*$/, '').trim();
                    // Remove year from tech
                    if (year) tech = tech.replace(String(year), '').replace(/,\s*$/, '').trim();
                }
            }

            // Image URL
            const img = item.querySelector('img');
            const imageUrl = img ? (img.src || img.getAttribute('data-original') || '') : '';

            // Detail URL
            const link = item.querySelector('a');
            const sourceUrl = link ? link.href : '';

            // Convert LVL to EUR (Latvia adopted EUR on 2014-01-01, rate 1 EUR = 0.702804 LVL)
            let endPrice = parseInt(priceText.replace(/\s/g, '')) || 0;
            if (currency === 'LVL' && endPrice > 0) {
                endPrice = Math.round(endPrice / 0.702804);
            }

            lots.push({
                lot_number: lotNum,
                author: author,
                title: title,
                tech: tech,
                dimensions_raw: dimsRaw,
                end_price: endPrice,
                bid_count: bids,
                sold: sold,
                year: year,
                image_url: imageUrl,
                source_url: sourceUrl,
                currency: currency,
            });
        }
        return lots;
    }""")


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("antonija")
    seen_keys = {(str(l.get("lot_number", "")), l.get("auction_name", ""))
                 for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        for auction_num in range(1, MAX_AUCTION + 1):
            auction_url = f"{AUCTION_URL}/{auction_num}"
            auction_name = f"Auction {auction_num}"

            log.info("Processing: %s", auction_name)

            try:
                safe_navigate(page, auction_url)
                time.sleep(2)
            except Exception as e:
                log.warning("  Failed to load %s: %s", auction_url, e)
                continue

            # Skip 403/login-only pages
            page_title = page.title()
            if "403" in page_title or "Forbidden" in page_title:
                log.warning("  403 on %s, waiting and retrying...", auction_url)
                time.sleep(5)
                try:
                    safe_navigate(page, auction_url)
                    time.sleep(2)
                    page_title = page.title()
                    if "403" in page_title:
                        log.warning("  Still 403, skipping")
                        continue
                except Exception:
                    continue

            nf_count = page.evaluate("() => document.querySelectorAll('.nf-item').length")
            if nf_count == 0:
                log.info("  No lots found (login-only or empty), skipping")
                continue

            if auction_num <= 5:
                dismiss_cookies(page)

            max_page = _get_max_page(page)
            log.info("  %d pages", max_page)

            auction_year = None
            page_text = page.evaluate("() => document.body.textContent.substring(0, 500)")
            ym = parse_year_from_text(page_text)
            if ym:
                auction_year = ym

            for pg in range(1, max_page + 1):
                if pg > 1:
                    try:
                        safe_navigate(page, f"{auction_url}/page-{pg}")
                        time.sleep(1)
                    except Exception:
                        break

                raw_lots = _scrape_page(page)

                for raw in raw_lots:
                    key = (str(raw.get("lot_number", "")), auction_name)
                    if key in seen_keys:
                        continue

                    dims_raw = raw.get("dimensions_raw", "")
                    dim_area, dims_clean = parse_dimensions(dims_raw) if dims_raw else (None, "")

                    lot = {
                        "auction_provider": "antonija",
                        "country": "LV",
                        "author": raw.get("author", "Unknown"),
                        "title": raw.get("title", ""),
                        "year": raw.get("year"),
                        "tech": raw.get("tech", ""),
                        "dimensions_raw": dims_clean,
                        "dimension": dim_area,
                        "start_price": 0,
                        "end_price": raw.get("end_price", 0),
                        "bid_count": raw.get("bid_count"),
                        "auction_name": auction_name,
                        "auction_date": auction_year or 0,
                        "image_url": raw.get("image_url"),
                        "source_url": raw.get("source_url"),
                        "sold": raw.get("sold", False),
                        "lot_number": raw.get("lot_number"),
                    }

                    lots.append(lot)
                    seen_keys.add(key)

                if limit and len(lots) >= limit:
                    break

            save_checkpoint(lots, "antonija")
            log.info("  Total so far: %d lots", len(lots))

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

            time.sleep(1)

        lots = deduplicate(lots)
        save_checkpoint(lots, "antonija")
        log.info("Antonija scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
