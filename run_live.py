"""
The real daily scan -- searches live eBay listings for every card in your
comps.csv, scores them, and writes today's report + dashboard data.

NOT YET LIVE-TESTED (see ebay_client.py docstring) -- this cloud workspace
can't reach api.ebay.com to test it here. Run this on a machine with normal
internet access. First run: `pip install` isn't even needed, just Python 3.

Usage:
    python3 run_live.py
"""

import datetime
import sys

from ebay_client import load_dotenv, get_access_token, search_listings, normalize_listing
from comps_loader import load_comps, load_comps_full
from matching import title_matches_comp
from scorer import find_deals
from report import render_html_report

MIN_SEARCH_PRICE = 10
MAX_SEARCH_PRICE = 2000  # comfortably above the $750 signature-required tier


def days_since(iso_date_str: str) -> int:
    if not iso_date_str:
        return None
    try:
        created = datetime.datetime.fromisoformat(iso_date_str.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        return (now - created).days
    except ValueError:
        return None


def main():
    load_dotenv()
    import os
    app_id = os.environ.get("EBAY_APP_ID")
    cert_id = os.environ.get("EBAY_CERT_ID")
    if not app_id or not cert_id:
        print("Missing EBAY_APP_ID / EBAY_CERT_ID -- check your .env file.")
        sys.exit(1)

    comps = load_comps()
    comps_full = load_comps_full()
    if not comps:
        print("comps.csv is empty -- add at least one card before running a live scan.")
        sys.exit(1)

    print(f"Getting eBay access token...")
    token = get_access_token(app_id, cert_id)

    all_listings = []
    rejected_count = 0
    for card_name in comps:
        meta = comps_full.get(card_name)
        if meta is None:
            print(f"  Skipping '{card_name}': needs a player_name column value in comps.csv to match safely.")
            continue

        print(f"Searching: {card_name}")
        raw_results = search_listings(token, query=card_name, min_price=MIN_SEARCH_PRICE, max_price=MAX_SEARCH_PRICE)
        for raw in raw_results:
            title = raw.get("title", "")
            if not title_matches_comp(title, meta["player_name"], meta["grade"], meta["exclude_keywords"]):
                rejected_count += 1
                continue
            listing = normalize_listing(raw, comp_key=card_name)
            listing["daysListed"] = days_since(listing.pop("_itemCreationDate", None))
            all_listings.append(listing)

    print(f"\nFetched listings across {len(comps)} cards you're tracking.")
    print(f"Rejected {rejected_count} listings as likely mismatches (wrong player, wrong grade, or an excluded insert/parallel).")
    print(f"{len(all_listings)} listings passed the title-match check and moved on to scoring.")

    deals = find_deals(all_listings, comps)

    verified = [d for d in deals if not d.needs_manual_verification]
    flagged = [d for d in deals if d.needs_manual_verification]

    print(f"\nFound {len(deals)} deals clearing $20+ profit and 20%+ margin ({len(flagged)} flagged for manual verification due to unusually high margin):\n")
    for d in deals:
        flag = "  [VERIFY MANUALLY -- unusually high margin, double-check this is really the right card]" if d.needs_manual_verification else ""
        print(f"  {d.title}{flag}")
        print(f"    Buy: ${d.buy_price:.2f}  ->  Resale: ${d.est_resale_price:.2f}  |  Net profit: ${d.net_profit:.2f} ({d.margin_pct:.1f}% margin)  |  {d.days_listed}d listed, {d.watch_count} watchers\n")

    html = render_html_report(deals)
    with open("daily_report.html", "w") as f:
        f.write(html)
    print("Wrote daily_report.html")


if __name__ == "__main__":
    main()
