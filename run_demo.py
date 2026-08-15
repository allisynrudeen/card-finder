"""
Demo run using sample data, to show what the end-to-end pipeline produces.

Comps come from YOUR comps.csv (the free manual price list) when it has
entries -- falls back to the built-in sample dict otherwise, so this still
runs before you've filled anything in. Once eBay API credentials are wired
in, SAMPLE_LISTINGS gets replaced by a live fetch_listings() call; the comps
side already reads from comps.csv, which is the real free-tier setup.
"""

from sample_data import SAMPLE_LISTINGS, SAMPLE_COMPS
from comps_loader import load_comps
from scorer import find_deals
from report import render_html_report

if __name__ == "__main__":
    csv_comps = load_comps()
    comps = csv_comps if csv_comps else SAMPLE_COMPS
    comps_source = "comps.csv" if csv_comps else "built-in sample dict (comps.csv is empty)"

    deals = find_deals(SAMPLE_LISTINGS, comps)

    print(f"Using comps from: {comps_source}")
    print(f"Scanned {len(SAMPLE_LISTINGS)} sample listings, found {len(deals)} deals clearing $20+ profit and 20%+ margin:\n")
    for d in deals:
        print(f"  {d.title}")
        print(f"    Buy: ${d.buy_price:.2f}  ->  Resale: ${d.est_resale_price:.2f}  |  Net profit: ${d.net_profit:.2f} ({d.margin_pct:.1f}% margin)  |  {d.days_listed}d listed, {d.watch_count} watchers\n")

    html = render_html_report(deals)
    with open("daily_report_sample.html", "w") as f:
        f.write(html)
    print("Wrote daily_report_sample.html")
