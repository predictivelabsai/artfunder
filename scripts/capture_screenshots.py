"""Capture product tour screenshots for the home page GIF.

Drives a real browser via Playwright against the live site.
Waits for LLM responses (up to 60s) to get rich content in each frame.

Usage:
    python -m scripts.capture_screenshots
    # or against local:
    KANVAS_URL=http://localhost:5009 python -m scripts.capture_screenshots
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

BASE_URL = os.environ.get("KANVAS_URL", "https://kanvas.ai")
VIEWPORT = {"width": 1400, "height": 900}

WAIT_FOR_RESPONSE = 30


def _wait_for_chat_response(page, timeout_s=60):
    """Wait until assistant response finishes streaming."""
    page.wait_for_function(
        """() => {
            const m = document.querySelector('#messages');
            if (!m) return false;
            const bubbles = m.querySelectorAll('.msg-assistant .msg-bubble, .msg:not(.msg-user) .msg-bubble');
            if (!bubbles.length) return false;
            const last = bubbles[bubbles.length-1];
            return last && (last.textContent||'').length > 80;
        }""",
        timeout=timeout_s * 1000,
    )
    time.sleep(WAIT_FOR_RESPONSE)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    SHOTS.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
        page = ctx.new_page()

        # --- Frame 1: Chat with market analyst query ---
        log.info("Frame 1: Chat — market analyst query")
        page.goto(f"{BASE_URL}/app", wait_until="networkidle", timeout=30_000)
        page.wait_for_selector("#chat-input", timeout=10_000)
        time.sleep(2)

        page.fill("#chat-input", "market: top 10 selling Estonian artists by total auction sales")
        page.keyboard.press("Enter")
        log.info("  sent chat message, waiting %ds for response...", WAIT_FOR_RESPONSE)
        try:
            _wait_for_chat_response(page)
        except Exception as e:
            log.warning("  chat response wait: %s — taking screenshot anyway", e)
            time.sleep(5)

        out = SHOTS / "gif-01-chat.png"
        page.screenshot(path=str(out), full_page=False)
        log.info("  saved %s", out.name)

        # --- Frame 2: Art Guru game ---
        log.info("Frame 2: Art Guru — character select + round 1")
        page.goto(f"{BASE_URL}/app/art-guru", wait_until="networkidle", timeout=30_000)
        page.wait_for_selector("#chat-input", timeout=10_000)
        time.sleep(2)

        page.fill("#chat-input", "1")
        page.keyboard.press("Enter")
        log.info("  selected character 1, waiting %ds for game intro...", WAIT_FOR_RESPONSE)
        try:
            _wait_for_chat_response(page, timeout_s=90)
        except Exception as e:
            log.warning("  art guru response wait: %s — taking screenshot anyway", e)
            time.sleep(5)

        out = SHOTS / "gif-02-art-guru.png"
        page.screenshot(path=str(out), full_page=False)
        log.info("  saved %s", out.name)

        # --- Frame 3: Market Map (treemap) ---
        log.info("Frame 3: Market Map")
        page.goto(f"{BASE_URL}/app/market-map", wait_until="networkidle", timeout=30_000)
        time.sleep(2)

        try:
            page.wait_for_function(
                """() => {
                    const el = document.getElementById('treemap-chart');
                    return el && el.querySelector('.plotly');
                }""",
                timeout=20_000,
            )
            time.sleep(3)
        except Exception as e:
            log.warning("  treemap render wait: %s — taking screenshot anyway", e)
            time.sleep(5)

        out = SHOTS / "gif-03-market-map.png"
        page.screenshot(path=str(out), full_page=False)
        log.info("  saved %s", out.name)

        # --- Frame 4: Market Map scrolled to trends ---
        log.info("Frame 4: Market Map — price trends")
        page.evaluate("document.getElementById('trend-chart').scrollIntoView({behavior:'instant'})")
        time.sleep(2)

        try:
            page.wait_for_function(
                """() => {
                    const el = document.getElementById('trend-chart');
                    return el && el.querySelector('.plotly');
                }""",
                timeout=15_000,
            )
            time.sleep(2)
        except Exception as e:
            log.warning("  trends render wait: %s", e)

        out = SHOTS / "gif-04-trends.png"
        page.screenshot(path=str(out), full_page=False)
        log.info("  saved %s", out.name)

        browser.close()

    log.info("Done — 4 frames in %s", SHOTS)


if __name__ == "__main__":
    main()
