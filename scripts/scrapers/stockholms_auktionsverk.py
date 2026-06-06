"""Stockholms Auktionsverk scraper — world's oldest auction house (1674).

Server-rendered HTML archive with ~182K art lots (12 per page, ~15,204 pages).
List URL: /arkiv/online/kategori/konst/page/{N}?order=id
Detail URL: /arkiv/online/{LOT_ID}

List pages have: artist+title in h2, start price (Utropspris), hammer price
(Klubbat for), image, link. Detail pages add: date, description with medium
and dimensions.

No anti-bot protection. Pure HTML, no JS needed.
"""

from __future__ import annotations

import logging
import re
import time

from scripts.scrapers.base import (
    parse_dimensions, parse_year_from_text, is_painting,
    setup_browser, dismiss_cookies, save_checkpoint, load_checkpoint,
    deduplicate, safe_navigate, _clean,
)

log = logging.getLogger(__name__)

BASE_URL = "https://stockholmsauktionsverk.com"
ARCHIVE_URL = f"{BASE_URL}/arkiv/online/kategori/konst"

SEK_TO_EUR = 0.088
MAX_PAGE = 15210


def _parse_sek_price(text: str) -> tuple[int, str]:
    """Parse '580 000 SEK' or '520 000 EUR' -> (amount, currency)."""
    m = re.search(r"([\d\s]+)\s*(SEK|EUR)", text)
    if not m:
        return 0, "SEK"
    amount = int(m.group(1).replace(" ", "").replace("\xa0", ""))
    return amount, m.group(2)


def _scrape_list_page(page) -> list[dict]:
    """Extract lots from an archive listing page using exact selectors."""
    return page.evaluate(r"""() => {
        const items = document.querySelectorAll('.col-md-3.object');
        const lots = [];

        for (const item of items) {
            const titleLink = item.querySelector('h2.object__title a, .object__title a');
            const img = item.querySelector('.object__image img');
            const footer = item.querySelector('.object__footer');

            const href = titleLink ? titleLink.href : '';
            const titleText = titleLink ? titleLink.textContent.trim() : '';
            const imgSrc = img ? img.src : null;
            const imgAlt = img ? img.alt : '';

            let startPrice = 0, startCurrency = 'SEK';
            let endPrice = 0, endCurrency = 'SEK';

            if (footer) {
                const paragraphs = footer.querySelectorAll('p');
                for (const p of paragraphs) {
                    const text = p.textContent.trim();
                    if (text.includes('Utropspris')) {
                        const strong = p.querySelector('strong');
                        if (strong) {
                            const m = strong.textContent.match(/([\d\s]+)\s*(SEK|EUR)/);
                            if (m) {
                                startPrice = parseInt(m[1].replace(/\s/g, ''));
                                startCurrency = m[2];
                            }
                        }
                    }
                    if (text.includes('Klubbat')) {
                        const strong = p.querySelector('strong');
                        if (strong) {
                            const m = strong.textContent.match(/([\d\s]+)\s*(SEK|EUR)/);
                            if (m) {
                                endPrice = parseInt(m[1].replace(/\s/g, ''));
                                endCurrency = m[2];
                            }
                        }
                    }
                }
            }

            const idMatch = href.match(/\/arkiv\/online\/(\d+)/);

            lots.push({
                title_text: titleText,
                alt_text: imgAlt,
                start_price: startPrice,
                start_currency: startCurrency,
                end_price: endPrice,
                end_currency: endCurrency,
                source_url: href,
                lot_id: idMatch ? idMatch[1] : null,
                image_url: imgSrc,
            });
        }

        return lots;
    }""")


MEDIUM_WORDS = re.compile(
    r'\b(olja|oljemålning|olje|akvarell|aquarell|gouache|tempera|pastell|'
    r'litografi|litho|etsning|skulptur|brons|trä|glas|keramik|porslin|'
    r'blandteknik|collage|fotografi|serigrafi|grafik|tryck|på duk|på pannå|'
    r'teckning|kolteckning|lavering|mixed media|watercolor|oil on|tusch|'
    r'akryl|screentryck|färglitografi)\b', re.IGNORECASE)


def _parse_title_text(text: str) -> tuple[str, str, str]:
    """Parse list title into (author, title, tech).

    Examples:
        'Albert Edelfelt (1854-1905), Dopfärd' -> ('Albert Edelfelt', 'Dopfärd', '')
        'Asmund Arle skulptur brons' -> ('Asmund Arle', '', 'skulptur brons')
        'Acke Fornander oljemålning' -> ('Acke Fornander', '', 'oljemålning')
    """
    text = text.strip()
    m = re.match(r'^(.+?)\s*\((\d{4})\s*[-–]\s*\d{0,4}\)\s*,?\s*(.*)', text)
    if m:
        return m.group(1).strip(), m.group(3).strip(), ""
    parts = text.split(",", 1)
    if len(parts) == 2 and len(parts[0]) < 80:
        return parts[0].strip(), parts[1].strip(), ""
    med = MEDIUM_WORDS.search(text)
    if med:
        author = text[:med.start()].strip()
        tech = text[med.start():].strip()
        if author:
            return author, "", tech
    return text, "", ""


def _to_eur(amount: int, currency: str) -> int:
    if currency == "SEK":
        return int(amount * SEK_TO_EUR)
    return amount


def scrape(headless: bool = True, limit: int = 0):
    lots = load_checkpoint("stockholms_auktionsverk")
    seen_urls = {l.get("source_url", "") for l in lots}

    pw, browser, ctx, page = setup_browser(headless=headless)

    try:
        log.info("Navigating to Stockholms Auktionsverk archive...")
        safe_navigate(page, f"{ARCHIVE_URL}?order=id")
        time.sleep(2)
        dismiss_cookies(page)

        max_page = MAX_PAGE
        if limit:
            max_page = min(max_page, (limit // 12) + 2)

        for pg in range(1, max_page + 1):
            url = f"{ARCHIVE_URL}/page/{pg}?order=id"
            log.info("Page %d / %d (%d lots so far)", pg, max_page, len(lots))

            try:
                safe_navigate(page, url)
                time.sleep(0.8)
            except Exception as e:
                log.warning("  Failed page %d: %s", pg, e)
                continue

            if pg == 1:
                dismiss_cookies(page)

            raw_lots = _scrape_list_page(page)
            if not raw_lots:
                log.info("  No lots on page %d, stopping", pg)
                break

            new_count = 0
            for raw in raw_lots:
                src_url = raw.get("source_url", "")
                if not src_url or src_url in seen_urls:
                    continue

                title_text = raw.get("title_text") or raw.get("alt_text") or ""
                author, title, tech = _parse_title_text(title_text)

                if not is_painting(tech, title, author):
                    continue

                end_price = _to_eur(raw.get("end_price", 0), raw.get("end_currency", "SEK"))
                start_price = _to_eur(raw.get("start_price", 0), raw.get("start_currency", "SEK"))

                lot = {
                    "auction_provider": "stockholms_auktionsverk",
                    "country": "SE",
                    "author": _clean(author, 255) or "Unknown",
                    "title": _clean(title, 500),
                    "year": None,
                    "tech": _clean(tech, 255),
                    "dimensions_raw": "",
                    "dimension": None,
                    "start_price": start_price,
                    "end_price": end_price,
                    "bid_count": None,
                    "auction_name": "Online Auction",
                    "auction_date": 0,
                    "image_url": raw.get("image_url"),
                    "source_url": src_url,
                    "sold": end_price > 0,
                    "lot_number": raw.get("lot_id"),
                }

                lots.append(lot)
                seen_urls.add(src_url)
                new_count += 1

            if new_count:
                log.info("  Page %d: %d new lots", pg, new_count)

            if pg % 50 == 0:
                save_checkpoint(lots, "stockholms_auktionsverk")

            if limit and len(lots) >= limit:
                log.info("Reached limit of %d lots", limit)
                break

            time.sleep(0.5)

        lots = deduplicate(lots)
        save_checkpoint(lots, "stockholms_auktionsverk")
        log.info("Stockholms Auktionsverk scrape complete: %d lots", len(lots))

    finally:
        browser.close()
        pw.stop()

    return lots
