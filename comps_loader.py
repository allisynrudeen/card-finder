"""
Loads YOUR manual price reference list from comps.csv.

This is the free-tier substitute for a paid pricing API (SportsCardsPro
Legendary, etc). You maintain comps.csv yourself -- open it in Excel/Numbers/
Google Sheets, add a row for every card you know well enough to price
confidently, and check the actual value periodically on 130point.com or
SportsCardsPro's free search.

Columns:
  card_name          -- must match a listing's `comp_key` exactly (see note below)
  target_resale_value -- what you're confident you could sell it for
  last_checked        -- date you last verified this price (YYYY-MM-DD)
  source               -- where you got the number (130point, SportsCardsPro, etc)
  notes                -- anything worth remembering (trending down, thin market, etc)

LIMITATION TO KNOW ABOUT: matching is exact-string only right now. A real
eBay listing title like "2018 Panini Prizm Luka Doncic PSA 9 HOT!! L@@K" won't
match "2018 Prizm Luka Doncic Rookie PSA 9" automatically -- the live version
needs a title-matching/normalization step (player name + set + grade) before
this lookup works against real listings. That's next on the list once eBay
access is live; for now this proves out the scoring logic end-to-end.
"""

import csv
import os

COMPS_CSV_PATH = os.path.join(os.path.dirname(__file__), "comps.csv")


def load_comps(csv_path: str = COMPS_CSV_PATH) -> dict:
    comps = {}
    if not os.path.exists(csv_path):
        return comps

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("card_name") or "").strip()
            value = (row.get("target_resale_value") or "").strip()
            if not name or not value:
                continue
            try:
                comps[name] = float(value)
            except ValueError:
                continue
    return comps
