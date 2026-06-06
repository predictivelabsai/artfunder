"""Lauritz.com scraper — Northern Europe's largest online auction house.

Protected by Cloudflare (403 on basic fetch). Uses Playwright with stealth.
Daily online auctions since 1999, ~5000 hammer prices/month.
Browse sold art: /en/auction/category/art/?sold=1
"""

from __future__ import annotations

import logging
import re
import time

from scripts.scrapers.base import (
    parse_price, parse_dimensions, parse_year_from_text, is_painting,
    setup_browser, dismiss_cookies, save_checkpoint, load_checkpoint,
    deduplicate, safe_navigate, _clean,
)

log = logging.getLogger(__name__)

BASE_URL = "https://www.lauritz.com"

DKK_TO_EUR = 0.134
SEK_TO_EUR = 0.088


def _setup_stealth_browser(headless: bool = True):
    """Launch Playwright with stealth settings to bypass Cloudflare."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    )
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        locale="da-DK",
        viewport={"width": 1920, "height": 1080},
        java_script_enabled=True,
    )
    page = ctx.new_page()

    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['da-DK', 'da', 'en-US', 'en']});
        window.chrome = {runtime: {}};
    """)

    return pw, browser, ctx, page


def _scrape_listing_page(page) -> list[dict]:
    """Extract lot data from a Lauritz listing/search page."""
    return page.evaluate(r"""() => {
        const lots = [];

        // Try various selectors for lot items
        const selectors = [
            '.lot-card', '.item-card', '.auction-item',
            '[data-lot-id]', '.search-result-item',
            'article', '.product-item',
        ];

        let items = [];
        for (const sel of selectors) {
            items = document.querySelectorAll(sel);
            if (items.length > 0) break;
        }

        // Fallback: look for any links to lot pages
        if (items.length === 0) {
            const links = document.querySelectorAll('a[href*="/auction/"], a[href*="/lot/"]');
            for (const link of links) {
                const container = link.closest('div, li, article') || link.parentElement;
                if (!container) continue;
                const text = container.textContent.replace(/\s+/g, ' ').trim();
                const img = container.querySelector('img');

                // Parse price - DKK or SEK
                const priceMatch = text.match(/([\d\s.,]+)\s*(?:DKK|SEK|EUR|kr)/);
                const price = priceMatch ? parseInt(priceMatch[1].replace(/[\s.,]/g, '')) : 0;
                const currMatch = text.match(/(DKK|SEK|EUR)/);
                const currency = currMatch ? currMatch[1] : 'DKK';

                // Parse artist
                let author = '';
                const boldEl = container.querySelector('strong, b, h3, h4');
                if (boldEl) author = boldEl.textContent.trim();

                lots.push({
                    author: author.substring(0, 200),
                    title: link.textContent.trim().substring(0, 200),
                    end_price: price,
                    currency: currency,
                    source_url: link.href,
                    image_url: img ? img.src : null,
                    raw_text: text.substring(0, 500),
                });
            }
        }

        for (const item of items) {
            const link = item.querySelector('a');
            const img = item.querySelector('img');
            const text = item.textContent.replace(/\s+/g, ' ').trim();

            let author = '';
            let title = '';
            const boldEl = item.querySelector('strong, b, h3, h4, .title, .artist');
            if (boldEl) author = boldEl.textContent.trim();

            const subtitleEl = item.querySelector('.subtitle, .description, p');
            if (subtitleEl) title = subtitleEl.textContent.trim();

            const priceMatch = text.match(/([\d\s.,]+)\s*(?:DKK|SEK|EUR|kr)/);
            const price = priceMatch ? parseInt(priceMatch[1].replace(/[\s.,]/g, '')) : 0;
            const currMatch = text.match(/(DKK|SEK|EUR)/);
            const currency = currMatch ? currMatch[1] : 'DKK';

            lots.push({
                author: author.substring(0, 200),
                title: (title || '').substring(0, 200),
                end_price: price,
                currency: currency,
                source_url: link ? link.href : '',
                image_url: img ? img.src : null,
                raw_text: text.substring(0, 500),
            });
        }

        return lots;
    }""")


def _scrape_detail_page(page) -> dict:
    """Extract full lot details from a Lauritz lot detail page."""
    return page.evaluate(r"""() => {
        const text = document.body.textContent.replace(/\s+/g, ' ').trim();

        let author = '', title = '', tech = '', dims = '';

        const h1 = document.querySelector('h1');
        if (h1) {
            const parts = h1.textContent.trim().split(/[,.]/, 2);
            author = parts[0].trim();
            if (parts.length > 1) title = parts[1].trim();
        }

        // Description fields
        const descEls = document.querySelectorAll('dt, .label, .detail-label');
        for (const el of descEls) {
            const label = el.textContent.trim().toLowerCase();
            const valueEl = el.nextElementSibling;
            if (!valueEl) continue;
            const val = valueEl.textContent.trim();

            if (label.includes('artist') || label.includes('kunstner')) author = author || val;
            if (label.includes('title') || label.includes('titel')) title = title || val;
            if (label.includes('technique') || label.includes('teknik')) tech = val;
            if (label.includes('dimension') || label.includes('mål')) dims = val;
        }

        // Prices
        const hammerMatch = text.match(/(?:Hammer|Slutpris|Tilslag|Sold for)[:\s]*([\d\s.,]+)\s*(DKK|SEK|EUR)/i);
        const startMatch = text.match(/(?:Estimate|Vurdering|Estimat)[:\s]*([\d\s.,]+)\s*(DKK|SEK|EUR)/i);

        const img = document.querySelector('.lot-image img, article img, .gallery img');

        return {
            author: author.substring(0, 200),
            title: title.substring(0, 200),
            tech: tech.substring(0, 200),
            dimensions_raw: dims.substring(0, 100),
            end_price: hammerMatch ? parseInt(hammerMatch[1].replace(/[\s.,]/g, '')) : 0,
            start_price: startMatch ? parseInt(startMatch[1].replace(/[\s.,]/g, '')) : 0,
            currency: hammerMatch ? hammerMatch[2] : (startMatch ? startMatch[2] : 'DKK'),
            image_url: img ? img.src : null,
        };
    }""")


def _convert_price(price: int, currency: str) -> int:
    if currency == "DKK":
        return int(price * DKK_TO_EUR)
    elif currency == "SEK":
        return int(price * SEK_TO_EUR)
    return price


SEARCH_URLS = [
    f"{BASE_URL}/en/auction/category/paintings/?sold=1",
    f"{BASE_URL}/en/auction/category/art/?sold=1",
    f"{BASE_URL}/en/auction/category/art/?sold=1&sort=price_desc",
    f"{BASE_URL}/en/search/paintings?status=sold",
]


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("lauritz")
    seen_urls = {l.get("source_url", "") for l in lots}

    pw, browser, ctx, page = _setup_stealth_browser(headless=headless)

    try:
        # Try multiple URL patterns since Lauritz blocks aggressively
        landed = False
        for try_url in SEARCH_URLS:
            log.info("Trying URL: %s", try_url)
            try:
                page.goto(try_url, timeout=30000, wait_until="domcontentloaded")
                time.sleep(5)  # Extra wait for Cloudflare challenge

                status = page.evaluate("() => document.title")
                body_len = page.evaluate("() => document.body.textContent.length")
                log.info("  Title: %s, Body length: %d", status, body_len)

                if "403" in status or "Forbidden" in status or body_len < 500:
                    log.warning("  Blocked on %s", try_url)
                    continue

                landed = True
                break
            except Exception as e:
                log.warning("  Failed: %s", e)
                continue

        if not landed:
            # Try the main page and navigate from there
            log.info("Trying main page navigation...")
            page.goto(f"{BASE_URL}/en/", timeout=30000, wait_until="domcontentloaded")
            time.sleep(5)
            dismiss_cookies(page)
            time.sleep(2)

            body_len = page.evaluate("() => document.body.textContent.length")
            if body_len < 500:
                log.error("Cannot access Lauritz.com — all URLs blocked")
                save_checkpoint(lots, "lauritz")
                return lots

        dismiss_cookies(page)
        time.sleep(1)

        max_pages = 100
        if limit:
            max_pages = min(max_pages, (limit // 20) + 1)

        for pg in range(1, max_pages + 1):
            log.info("Page %d (%d lots so far)", pg, len(lots))

            raw_lots = _scrape_listing_page(page)
            if not raw_lots:
                log.info("  No lots found on page %d", pg)
                break

            new_count = 0
            for raw in raw_lots:
                src_url = raw.get("source_url", "")
                if not src_url or src_url in seen_urls:
                    continue

                author = raw.get("author", "")
                if not is_painting(title=raw.get("title", ""), author=author):
                    continue

                end_price = raw.get("end_price", 0)
                currency = raw.get("currency", "DKK")
                end_price_eur = _convert_price(end_price, currency)

                lot = {
                    "auction_provider": "lauritz",
                    "country": "DK",
                    "author": _clean(author, 255) or "Unknown",
                    "title": _clean(raw.get("title"), 500),
                    "year": None,
                    "tech": "",
                    "dimensions_raw": "",
                    "dimension": None,
                    "start_price": 0,
                    "end_price": end_price_eur,
                    "bid_count": None,
                    "auction_name": "",
                    "auction_date": 0,
                    "image_url": raw.get("image_url"),
                    "source_url": src_url,
                    "sold": end_price > 0,
                    "lot_number": None,
                }

                lots.append(lot)
                seen_urls.add(src_url)
                new_count += 1

            log.info("  Page %d: %d new lots", pg, new_count)
            save_checkpoint(lots, "lauritz")

            if limit and len(lots) >= limit:
                break

            # Try to find and click "next page"
            has_next = page.evaluate(r"""() => {
                const nextBtns = document.querySelectorAll(
                    'a[rel="next"], .pagination .next a, a:has-text("Next"), ' +
                    'a:has-text("Næste"), button:has-text("Next"), [aria-label="Next"]'
                );
                for (const btn of nextBtns) {
                    if (btn.offsetParent !== null) {
                        btn.click();
                        return true;
                    }
                }
                // Try page number links
                const current = document.querySelector('.pagination .active, .page-item.active');
                if (current) {
                    const next = current.nextElementSibling;
                    if (next) {
                        const link = next.querySelector('a') || next;
                        link.click();
                        return true;
                    }
                }
                return false;
            }""")

            if not has_next:
                log.info("No more pages found")
                break

            time.sleep(2)

        lots = deduplicate(lots)
        save_checkpoint(lots, "lauritz")
        log.info("Lauritz scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
