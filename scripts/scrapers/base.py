"""Shared utilities for Estonian art auction scrapers."""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "auctions"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def parse_price(text: str) -> int:
    """Extract integer EUR price from text like '31 500 €' or 'AH: 350€'."""
    if not text:
        return 0
    cleaned = re.sub(r"[^\d\s]", "", text.split("€")[0] if "€" in text else text)
    cleaned = cleaned.strip()
    if not cleaned:
        return 0
    return int(cleaned.replace(" ", "").replace(" ", ""))


def parse_dimensions(text: str) -> tuple[float | None, str]:
    """Parse '100 x 80 cm' or '39,2 x 64 cm' -> (area_cm2, raw_string)."""
    raw = text.strip()
    m = re.search(r"([\d]+[,.]?[\d]*)\s*[x×]\s*([\d]+[,.]?[\d]*)", raw)
    if m:
        try:
            w = float(m.group(1).replace(",", "."))
            h = float(m.group(2).replace(",", "."))
            return round(w * h, 1), raw
        except ValueError:
            pass
    return None, raw


def parse_year_from_text(text: str) -> int | None:
    """Extract a 4-digit year (1800-2030) from free text."""
    m = re.search(r"\b(1[89]\d{2}|20[0-3]\d)\b", text)
    return int(m.group(1)) if m else None


def decade_from_year(year: int | None) -> int | None:
    if year and year >= 1800:
        return (year // 10) * 10
    return None


def setup_browser(headless: bool = True):
    """Launch Playwright Chromium and return (playwright, browser, context, page)."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        locale="et-EE",
        viewport={"width": 1920, "height": 1080},
    )
    page = ctx.new_page()
    return pw, browser, ctx, page


def dismiss_cookies(page):
    """Try to dismiss common cookie consent dialogs."""
    selectors = [
        "button:has-text('Nõustun')",
        "button:has-text('Accept')",
        ".cmplz-btn.cmplz-accept",
        "[data-cli_action='accept']",
        "button:has-text('OK')",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=1000):
                btn.click()
                time.sleep(0.5)
                return True
        except Exception:
            continue
    return False


def save_checkpoint(lots: list[dict], provider: str) -> Path:
    path = DATA_DIR / f"{provider}.json"
    path.write_text(json.dumps(lots, ensure_ascii=False, indent=2, default=str))
    log.info("Checkpoint saved: %s (%d lots)", path, len(lots))
    return path


def load_checkpoint(provider: str) -> list[dict]:
    path = DATA_DIR / f"{provider}.json"
    if path.exists():
        data = json.loads(path.read_text())
        log.info("Resumed from checkpoint: %s (%d lots)", path, len(data))
        return data
    return []


def deduplicate(lots: list[dict]) -> list[dict]:
    """Deduplicate by composite key including lot_number when available."""
    seen = set()
    result = []
    for lot in lots:
        lot_num = lot.get("lot_number")
        aname = (lot.get("auction_name") or "").strip().lower()
        if lot_num is not None:
            key = (
                str(lot_num),
                aname,
                (lot.get("auction_provider") or "").strip().lower(),
            )
        else:
            key = (
                (lot.get("author") or "").strip().lower(),
                (lot.get("title") or "").strip().lower(),
                aname,
            )
        if key in seen:
            continue
        seen.add(key)
        result.append(lot)
    return result


def safe_navigate(page, url: str, timeout: int = 30000):
    """Navigate with retry on timeout."""
    for attempt in range(3):
        try:
            page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            return
        except Exception as e:
            if attempt < 2:
                log.warning("Navigate retry %d for %s: %s", attempt + 1, url, e)
                time.sleep(2)
            else:
                raise


def _clean(val: str | None, maxlen: int = 500) -> str | None:
    """Strip HTML tags, whitespace, and truncate."""
    if not val:
        return None
    cleaned = re.sub(r"<[^>]+>", "", val).strip()
    return cleaned[:maxlen] if cleaned else None


def lot_to_db_row(lot: dict) -> dict:
    """Normalize a scraped lot dict to match the auction_lots DB columns."""
    year = lot.get("year")
    if isinstance(year, str):
        year = parse_year_from_text(year)
    elif isinstance(year, float):
        year = int(year) if year > 1800 else None

    return {
        "auction_date": lot.get("auction_date", 0),
        "author": _clean(lot.get("author"), 255) or "Unknown",
        "start_price": lot.get("start_price", 0),
        "end_price": lot.get("end_price", 0),
        "year": year if year and year > 1800 else None,
        "decade": decade_from_year(year),
        "tech": (lot.get("tech") or lot.get("technique") or "").strip() or None,
        "category": (lot.get("category") or "").strip() or None,
        "dimension": lot.get("dimension"),
        "auction_provider": lot["auction_provider"],
        "title": _clean(lot.get("title")),
        "lot_number": lot.get("lot_number"),
        "dimensions_raw": (lot.get("dimensions_raw") or "").strip() or None,
        "bid_count": lot.get("bid_count"),
        "auction_name": _clean(lot.get("auction_name"), 255),
        "image_url": lot.get("image_url"),
        "source_url": lot.get("source_url"),
        "sold": lot.get("sold", True),
        "country": lot.get("country", "EE"),
    }
