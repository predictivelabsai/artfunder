"""Capture a tour of the Kanvas.ai app into ./screenshots.

Drives a real browser via Playwright against a locally-running server.
Produces deterministic frames for `make_gif.py`.

Usage:
    # server already running on :5009
    python -m scripts.capture_screenshots
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

log = logging.getLogger("capture")

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"

BASE_URL = os.environ.get("KANVAS_URL", "http://localhost:5009")
VIEWPORT = {"width": 1400, "height": 900}

TOUR = [
    # (filename, url, wait_selector, full_page, post_action)
    ("01-home-full.png",              "/",                "text=Your AI Art Advisor",       True,  None),
    ("02-home-agents.png",            "/",                "text=8 Specialist Agents",       True,  None),
    ("03-investors-full.png",         "/investors",       "h1",                             True,  None),
    ("04-artists-full.png",           "/artists",         "h1",                             True,  None),
    # Chat screens
    ("05-chat-empty.png",             "/app",             "#chat-input",                    False, None),
    ("06-chat-artist.png",            "/app",             "#chat-input",                    False, "artist"),
    ("07-chat-market.png",            "/app",             "#chat-input",                    False, "market"),
    ("08-chat-advise.png",            "/app",             "#chat-input",                    False, "advise"),
    # Analytics
    ("09-analytics-empty.png",        "/app/analytics",   "#analytics-q",                   False, None),
    ("10-analytics-artists.png",      "/app/analytics",   "#analytics-q",                   False, "top_artists"),
    ("11-analytics-category.png",     "/app/analytics",   "#analytics-q",                   False, "by_category"),
]

CHAT_MSGS = {
    "artist": "artist: Konrad Magi",
    "market": "market: top selling Estonian artists by total sales",
    "advise": "advise: I have EUR 50,000 budget for Estonian art, what should I buy?",
}

ANALYTICS_QUERIES = {
    "top_artists":  "Top 10 artists by total auction sales",
    "by_category":  "Average end price by art category",
}


def _run_chat(page, msg: str) -> None:
    page.fill("#chat-input", msg)
    page.keyboard.press("Enter")
    page.wait_for_function(
        """() => {
            const m = document.querySelector('#messages');
            if (!m) return false;
            const bubbles = m.querySelectorAll('.msg-assistant .msg-bubble');
            if (!bubbles.length) return false;
            const last = bubbles[bubbles.length-1];
            return last && (last.textContent||'').length > 100
                   && !last.classList.contains('streaming');
        }""",
        timeout=120_000,
    )
    time.sleep(0.5)


def _run_analytics(page, question: str) -> None:
    page.fill("#analytics-q", question)
    page.evaluate("() => runAnalytics()")
    page.wait_for_function(
        """() => {
            const r = document.getElementById('analytics-result');
            if (!r) return false;
            return r.querySelector('table, .plotly, pre') !== null;
        }""",
        timeout=60_000,
    )
    time.sleep(1.0)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    SHOTS.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1)
        page = ctx.new_page()

        for fname, path, wait_for, full_page, action in TOUR:
            url = BASE_URL + path
            log.info("-> %s", url)
            try:
                page.goto(url, wait_until="networkidle", timeout=30_000)
            except Exception as e:
                log.warning("goto failed %s: %s -- retrying with 'load'", url, e)
                page.goto(url, wait_until="load", timeout=30_000)

            if wait_for:
                try:
                    page.wait_for_selector(wait_for, timeout=10_000)
                except Exception:
                    log.warning("selector %r didn't appear on %s", wait_for, path)

            if action:
                if action in CHAT_MSGS:
                    _run_chat(page, CHAT_MSGS[action])
                elif action in ANALYTICS_QUERIES:
                    _run_analytics(page, ANALYTICS_QUERIES[action])
                time.sleep(0.4)

            out = SHOTS / fname
            page.screenshot(path=str(out), full_page=full_page)
            log.info("  saved %s", out.relative_to(ROOT))

        browser.close()
    log.info("done -- %d frames in %s", len(TOUR), SHOTS)


if __name__ == "__main__":
    main()
