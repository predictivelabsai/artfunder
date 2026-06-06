"""Send Kanvas.ai art deals digest email via Postmark.

Usage:
    python -m scripts.daily_deals                       # uses env defaults (single recipient)
    python -m scripts.daily_deals --to user@example.com
    python -m scripts.daily_deals --all                  # send to all registered users
    python -m scripts.daily_deals --dry-run              # print HTML, don't send
    python -m scripts.daily_deals --deals 10             # top N deals per section

Schedule via cron (daily at 07:00 UTC):
    0 7 * * *  cd /path/to/kanvas && python -m scripts.daily_deals --all
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from utils.deals_scanner import (
    scan_bidding_wars, scan_value_finds, scan_market_movers, fetch_news,
    build_digest_html, build_digest_text,
)
from utils.email import send_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL = os.getenv("SERVICE_URL_KANVAS", os.getenv("SERVICE_URL", "https://kanvas.ai"))
UNSUB_SECRET = os.getenv("SECRET_KEY", "kanvas-unsub-2026")


def _unsubscribe_url(email: str) -> str:
    token = hmac.new(UNSUB_SECRET.encode(), email.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{BASE_URL}/unsubscribe?email={email}&token={token}"


def _get_newsletter_recipients() -> list[str]:
    """Return emails of all registered users who haven't unsubscribed from weekly digest."""
    from sqlalchemy import text
    from db import SessionLocal
    db = SessionLocal()
    try:
        rows = db.execute(text("""
            SELECT u.email
            FROM kanvas.chat_users u
            LEFT JOIN kanvas.user_profiles p ON p.user_id = u.id
            WHERE u.email NOT LIKE 'guest+%%'
              AND (p.notify_weekly_digest IS NULL OR p.notify_weekly_digest = TRUE)
        """)).fetchall()
        return [r.email for r in rows]
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Send Kanvas.ai art deals digest")
    parser.add_argument("--to", default=os.getenv("TO_EMAIL", "kanvas@predictivelabs.co.uk"))
    parser.add_argument("--from-email", default=os.getenv("FROM_EMAIL", "info@kanvas.ai"))
    parser.add_argument("--dry-run", action="store_true", help="Print HTML without sending")
    parser.add_argument("--all", action="store_true", help="Send to all registered users")
    parser.add_argument("--deals", type=int, default=10, help="Number of items per section")
    parser.add_argument("--news", type=int, default=6, help="Number of news items")
    args = parser.parse_args()

    log.info("Scanning bidding wars...")
    wars = scan_bidding_wars(limit=args.deals)
    log.info(f"Found {len(wars)} bidding war lots")

    log.info("Scanning value finds...")
    values = scan_value_finds(limit=args.deals)
    log.info(f"Found {len(values)} value finds")

    log.info("Scanning market movers...")
    movers = scan_market_movers(limit=args.deals)
    log.info(f"Found {len(movers)} market movers")

    log.info("Fetching art news...")
    news = fetch_news(max_items=args.news)
    log.info(f"Found {len(news)} news items")

    now = datetime.now()
    period = "Morning" if now.hour < 12 else ("Afternoon" if now.hour < 17 else "Evening")
    subject = f"Kanvas.ai {period} Art Deals -- {now.strftime('%b %d, %Y')}"

    if args.all:
        recipients = _get_newsletter_recipients()
        global_to = args.to
        if global_to not in recipients:
            recipients.append(global_to)
        log.info(f"Broadcasting to {len(recipients)} recipients")
    else:
        recipients = [args.to]

    if args.dry_run:
        html = build_digest_html(wars, values, movers, news,
                                 unsubscribe_url=_unsubscribe_url("test@example.com"))
        print(html)
        log.info(f"Dry run complete. Subject: {subject}")
        log.info(f"Would send to: {recipients}")
        return

    sent = 0
    failed = 0
    for email in recipients:
        unsub = _unsubscribe_url(email)
        html = build_digest_html(wars, values, movers, news, unsubscribe_url=unsub)
        text = build_digest_text(wars, values, movers, news, unsubscribe_url=unsub)

        log.info(f"Sending to {email}...")
        result = send_email(
            to=email,
            subject=subject,
            html_body=html,
            text_body=text,
            from_email=args.from_email,
            tag="art-deals",
        )

        if result.get("ErrorCode") == 0:
            log.info(f"Sent to {email}: {result.get('MessageID')}")
            sent += 1
        else:
            log.error(f"Failed for {email}: {result}")
            failed += 1

        if len(recipients) > 1:
            time.sleep(0.5)

    log.info(f"Done. Sent: {sent}, Failed: {failed}, Total: {len(recipients)}")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
