"""
Loads YOUR manual price reference list from comps.csv.

This is the free-tier substitute for a paid pricing API (SportsCardsPro
Legendary, etc). You maintain comps.csv yourself -- open it in Excel/Numbers/
Google Sheets, add a row for every card you know well enough to price
confidently, and check the actual value periodically on 130point.com or
SportsCardsPro's free search.

Columns:
  card_name           -- the full label, also used as the eBay search query
  player_name          -- REQUIRED for matching -- every word must appear in
                           a listing's title, or it's rejected (this is what
                           catches "CJ Rodriguez" showing up for a "Julio
                           Rodriguez" search)
  grade                 -- e.g. "PSA 10" -- must appear in the listing title
  target_resale_value  -- what you're confident you could sell it for
  exclude_keywords     -- comma-separated insert/parallel names that mean a
                           listing is a DIFFERENT product than your comp
                           (e.g. "Stare Masters,Straight Fire" for a base
                           Mosaic card) -- any match here rejects the listing
  last_checked          -- date you last verified this price (YYYY-MM-DD)
  source                 -- where you got the number (130point, SportsCardsPro, etc)
  notes                  -- anything worth remembering (trending down, thin market, etc)
"""

import csv
import os

COMPS_CSV_PATH = os.path.join(os.path.dirname(__file__), "comps.csv")


def load_comps(csv_path: str = COMPS_CSV_PATH) -> dict:
    """Simple card_name -> target_resale_value dict, for scoring."""
    comps = {}
    for row in _read_rows(csv_path):
        name = row.get("card_name")
        value = row.get("target_resale_value")
        if not name or not value:
            continue
        try:
            comps[name] = float(value)
        except ValueError:
            continue
    return comps


def load_comps_full(csv_path: str = COMPS_CSV_PATH) -> dict:
    """
    card_name -> {value, player_name, grade, exclude_keywords}, for the
    title-matching validation step before a listing is trusted.
    """
    comps = {}
    for row in _read_rows(csv_path):
        name = (row.get("card_name") or "").strip()
        value = (row.get("target_resale_value") or "").strip()
        player_name = (row.get("player_name") or "").strip()
        if not name or not value or not player_name:
            continue
        try:
            value = float(value)
        except ValueError:
            continue

        exclude_raw = (row.get("exclude_keywords") or "").strip()
        exclude_keywords = [w.strip() for w in exclude_raw.split(",") if w.strip()]

        comps[name] = {
            "value": value,
            "player_name": player_name,
            "grade": (row.get("grade") or "").strip(),
            "exclude_keywords": exclude_keywords,
        }
    return comps


def _read_rows(csv_path: str):
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
