"""Allee Galerii scraper — WordPress portfolio-based auction catalog (2020-present).

Structure:
- Index page /kunstioksjon/ lists auction categories (Kevadoksjon/Sügisoksjon per year)
- Category page shows all lots as .portfolio-entry items (no pagination)
- Detail page per lot has prices, technique, bid count
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

BASE_URL = "https://alleegalerii.ee"
INDEX_URL = f"{BASE_URL}/kunstioksjon/"


def _get_auction_categories(page) -> list[dict]:
    """Get all auction category links from the index page."""
    return page.evaluate("""() => {
        const links = document.querySelectorAll('a[href*="kunstioksjon-kategooria"]');
        return [...links].map(a => ({
            name: a.textContent.trim(),
            url: a.href,
        })).filter(l => l.name && !l.name.includes('Kõik'));
    }""")


def _get_lot_links(page) -> list[dict]:
    """Get all lot links + metadata from a category listing page."""
    return page.evaluate("""() => {
        const entries = document.querySelectorAll('.portfolio-entry');
        return [...entries].map((el, idx) => {
            const links = el.querySelectorAll('a');
            let url = '', text = '';
            for (const a of links) {
                const t = a.textContent.trim();
                if (t && t.length > 5 && a.href.includes('/kunstioksjon/')) {
                    url = a.href;
                    text = t;
                    break;
                }
            }
            if (!url) {
                const a = el.querySelector('a[href*="/kunstioksjon/"]');
                if (a) url = a.href;
            }
            const img = el.querySelector('img');
            return {
                url: url,
                link_text: text,
                image_url: img ? img.src : '',
                lot_number: idx + 1,
            };
        }).filter(l => l.url);
    }""")


def _scrape_lot_detail(page, url: str) -> dict:
    """Scrape a single lot detail page for prices, technique, etc."""
    safe_navigate(page, url)
    time.sleep(0.8)
    dismiss_cookies(page)

    return page.evaluate("""() => {
        const body = document.body.cloneNode(true);
        body.querySelectorAll('[class*=cmplz], [class*=cookie]').forEach(el => el.remove());
        const text = body.textContent.replace(/\\s+/g, ' ').trim();

        const prices = [...document.querySelectorAll('.woocommerce-Price-amount.amount')]
            .map(el => el.textContent.trim());

        // Parse fields from text
        const algMatch = text.match(/Alghind\\s*([\\d\\s]+)\\s*€/);
        const hamMatch = text.match(/Haamrihind\\s*([\\d\\s]+)\\s*€/);
        const bidMatch = text.match(/Pakkumisi\\s*(\\d+)/);
        const dimMatch = text.match(/(\\d+)\\s*[x×]\\s*(\\d+)\\s*cm/);
        const yearMatch = text.match(/\\b(1[89]\\d{2}|20[0-2]\\d)\\b/);

        // Tech / medium from text
        const techPatterns = [
            'Õli lõuend', 'Õli, lõuend', 'Oil on canvas',
            'Akvarell', 'Watercolour', 'Guašš', 'Gouache',
            'Segu', 'Mixed media', 'Segatehnika',
            'Tempera', 'Pastell', 'Pastel',
            'Litograafia', 'Lithograph',
            'Graafika', 'Graphics',
            'Skulptuur', 'Sculpture',
        ];
        let tech = '';
        for (const t of techPatterns) {
            if (text.includes(t)) { tech = t; break; }
        }

        return {
            start_price_text: algMatch ? algMatch[1].trim() : (prices.length >= 3 ? prices[2] : ''),
            end_price_text: hamMatch ? hamMatch[1].trim() : (prices.length >= 4 ? prices[3] : ''),
            bid_count: bidMatch ? parseInt(bidMatch[1]) : null,
            dimensions_text: dimMatch ? dimMatch[0] : '',
            year_text: yearMatch ? yearMatch[1] : '',
            tech: tech,
            full_text: text.substring(0, 500),
        };
    }""")


def _parse_link_text(text: str) -> dict:
    """Parse 'Author "Title", Year. W x H cm' from listing link text."""
    result = {"author": "", "title": "", "year": None, "dimensions_raw": ""}

    # Normalize all quote types to standard double quotes
    _QUOTES = "“”„«»‘’‚‹›"
    normalized = text
    for qc in _QUOTES:
        normalized = normalized.replace(qc, '"')

    # Try pattern: Author "Title", Year. Dims
    m = re.match(r'^(.+?)\s*"(.+?)",?\s*(\d{4})[-–/]?\d{0,4}\.?\s*(.*)', normalized)
    if m:
        result["author"] = m.group(1).strip()
        result["title"] = m.group(2).strip()
        result["year"] = int(m.group(3))
        dims = m.group(4).strip()
        if dims:
            dim_match = re.search(r'[\d]+[,.]?[\d]*\s*[x×]\s*[\d]+[,.]?[\d]*\s*cm', dims)
            if dim_match:
                result["dimensions_raw"] = dim_match.group(0)
            else:
                result["dimensions_raw"] = dims
        return result

    # Simpler: Author "Title" rest
    m = re.match(r'^(.+?)\s*"(.+?)"(.*)$', normalized)
    if m:
        result["author"] = m.group(1).strip()
        result["title"] = m.group(2).strip()
        rest = m.group(3).strip(", .")
        year = parse_year_from_text(rest)
        if year:
            result["year"] = year
        dim_match = re.search(r'[\d]+[,.]?[\d]*\s*[x×]\s*[\d]+[,.]?[\d]*\s*cm', rest)
        if dim_match:
            result["dimensions_raw"] = dim_match.group(0)
        return result

    result["author"] = text.strip()
    return result


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("allee")
    seen_urls = {l.get("source_url") for l in lots if l.get("source_url")}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to Allee index...")
        safe_navigate(page, INDEX_URL)
        time.sleep(2)
        dismiss_cookies(page)

        categories = _get_auction_categories(page)
        log.info("Found %d auction categories", len(categories))

        for cat in categories:
            cat_name = cat["name"]
            log.info("Processing: %s", cat_name)

            safe_navigate(page, cat["url"])
            time.sleep(1.5)

            lot_links = _get_lot_links(page)
            log.info("  %d lots in %s", len(lot_links), cat_name)

            for i, ll in enumerate(lot_links):
                if ll["url"] in seen_urls:
                    continue

                try:
                    detail = _scrape_lot_detail(page, ll["url"])
                except Exception as e:
                    log.warning("  Failed lot %s: %s", ll["url"], e)
                    continue

                parsed = _parse_link_text(ll.get("link_text", ""))

                start_price = parse_price(detail.get("start_price_text", ""))
                end_price = parse_price(detail.get("end_price_text", ""))

                dims_raw = detail.get("dimensions_text") or parsed.get("dimensions_raw", "")
                dim_area, dims_raw_clean = parse_dimensions(dims_raw) if dims_raw else (None, "")

                year = parsed.get("year") or parse_year_from_text(detail.get("year_text", ""))

                # Extract auction year from category name
                auction_year = parse_year_from_text(cat_name)

                lot = {
                    "auction_provider": "allee",
                    "author": parsed.get("author", "Unknown"),
                    "title": parsed.get("title", ""),
                    "year": year,
                    "tech": detail.get("tech", ""),
                    "dimensions_raw": dims_raw_clean,
                    "dimension": dim_area,
                    "start_price": start_price,
                    "end_price": end_price,
                    "bid_count": detail.get("bid_count"),
                    "auction_name": cat_name,
                    "auction_date": auction_year or 0,
                    "image_url": ll.get("image_url") or None,
                    "source_url": ll["url"],
                    "sold": end_price > 0,
                    "lot_number": ll.get("lot_number"),
                }

                lots.append(lot)
                seen_urls.add(ll["url"])

                if (i + 1) % 25 == 0:
                    save_checkpoint(lots, "allee")
                    log.info("  Progress: %d/%d lots in %s, total: %d",
                             i + 1, len(lot_links), cat_name, len(lots))

                if limit and len(lots) >= limit:
                    break

                time.sleep(1)

            save_checkpoint(lots, "allee")

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

        lots = deduplicate(lots)
        save_checkpoint(lots, "allee")
        log.info("Allee scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
