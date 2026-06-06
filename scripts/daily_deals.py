"""Send Kanvas.ai art deals digest email via Postmark.

Usage:
    python -m scripts.daily_deals                       # uses env defaults
    python -m scripts.daily_deals --to user@example.com
    python -m scripts.daily_deals --dry-run              # print HTML, don't send
    python -m scripts.daily_deals --deals 10             # top N deals per section

Schedule via cron (daily at 07:00 UTC):
    0 7 * * *  cd /path/to/kanvas && python -m scripts.daily_deals
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
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


def main():
    parser = argparse.ArgumentParser(description="Send Kanvas.ai art deals digest")
    parser.add_argument("--to", default=os.getenv("TO_EMAIL", "kanvas@predictivelabs.co.uk"))
    parser.add_argument("--from-email", default=os.getenv("FROM_EMAIL", "info@kanvas.ai"))
    parser.add_argument("--dry-run", action="store_true", help="Print HTML without sending")
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

    html = build_digest_html(wars, values, movers, news)
    text = build_digest_text(wars, values, movers, news)

    now = datetime.now()
    period = "Morning" if now.hour < 12 else ("Afternoon" if now.hour < 17 else "Evening")
    subject = f"Kanvas.ai {period} Art Deals -- {now.strftime('%b %d, %Y')}"

    if args.dry_run:
        print(html)
        log.info(f"Dry run complete. Subject: {subject}")
        return

    log.info(f"Sending to {args.to} from {args.from_email}...")
    result = send_email(
        to=args.to,
        subject=subject,
        html_body=html,
        text_body=text,
        from_email=args.from_email,
        tag="art-deals",
    )

    if result.get("ErrorCode") == 0:
        log.info(f"Sent! MessageID: {result.get('MessageID')}")
    elif result.get("error"):
        log.error(f"Failed: {result['error']}")
        sys.exit(1)
    else:
        log.error(f"Postmark error: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
