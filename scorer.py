"""
Core scoring logic: turn (active listing + comp price) into a ranked deal.

This is the part that stays the same regardless of where the listings or
comps data actually comes from -- swap the data source, keep this logic.
"""

from dataclasses import dataclass
from typing import Optional

from fees import DealMath


# A deal must clear BOTH bars to show up: at least $20 of actual profit,
# AND at least a 20% margin on what you paid. The margin floor is the
# guardrail against deals that clear $20 only because a lot of your money
# is tied up (e.g. $500 in, $20 out = 4% margin -- thin and risk-prone).
MIN_NET_PROFIT = 20.00
MIN_MARGIN_PCT = 20.0

# Interest/staleness filter: a listing that's been up a long time with no
# one watching it is a signal nobody wants it at that price (wrong price,
# undesirable card, or a condition issue photos don't show). eBay doesn't
# expose raw "view counts" via the API anymore -- the two real signals are
# listing age (itemCreationDate, available immediately) and watch count
# (watchCount, requires a separate eBay permission request beyond the base
# API key). We filter on age now; once watchCount access is approved, the
# combined check below activates automatically.
MAX_DAYS_LISTED = 250
LOW_WATCH_COUNT_THRESHOLD = 2  # "basically no one is watching this"

# Sanity check, independent of title matching: a real margin this high on a
# graded sports card is rare. In practice this almost always means a title
# match went wrong somewhere (wrong player, wrong parallel/insert, wrong
# grade) rather than an actual windfall. We don't hide these -- you might be
# right and the tool wrong -- but they get flagged for a manual look instead
# of being presented as a clean, ready-to-buy deal.
SANITY_MARGIN_PCT = 150.0


def estimate_resale_shipping_cost(resale_price: float) -> float:
    """
    What it costs YOU to ship the card when you resell it -- packaging
    (toploader/sleeve, bubble mailer or small box) + postage + tracking, and
    insurance/signature once the card is valuable enough to need it.

    These are starting estimates, not quotes -- tune them against your actual
    USPS/eBay shipping receipts once you have a few sales under your belt.
    eBay requires signature confirmation on orders of $750+, which is reflected
    in the top tier.
    """
    if resale_price < 20:
        return 4.50   # padded envelope + tracked first class
    elif resale_price < 250:
        return 5.50   # small bubble mailer/box + tracking
    elif resale_price < 750:
        return 8.50   # sturdier box + tracking + basic insurance
    else:
        return 14.00  # signature confirmation (eBay-required) + full insurance


def is_stale_listing(days_listed: Optional[int], watch_count: Optional[int]) -> bool:
    """
    True if this listing looks like nobody wants it: sitting a long time
    with little/no watcher interest. Conservative by design -- if we don't
    have age data yet, we don't exclude it (missing data isn't evidence of
    disinterest).
    """
    if days_listed is None or days_listed <= MAX_DAYS_LISTED:
        return False

    if watch_count is None:
        # We don't have watch-count access yet -- age alone triggers the flag.
        # Once watchCount access is approved, this becomes the real combined
        # signal you asked for ("250+ days AND no views").
        return True

    return watch_count <= LOW_WATCH_COUNT_THRESHOLD


@dataclass
class ScoredDeal:
    title: str
    listing_url: str
    buy_price: float
    est_resale_price: float
    net_profit: float
    margin_pct: float
    days_listed: Optional[int]
    watch_count: Optional[int]
    needs_manual_verification: bool
    comp_source_note: str


def score_listing(listing: dict, comps: dict) -> Optional[ScoredDeal]:
    comp_key = listing.get("comp_key")
    est_resale_price = comps.get(comp_key)

    if est_resale_price is None:
        # No comp data found -- in production, log this so you can see what
        # your comps source is missing, but don't guess at a value.
        return None

    days_listed = listing.get("daysListed")
    watch_count = listing.get("watchCount")

    if is_stale_listing(days_listed, watch_count):
        return None

    buy_price = float(listing["price"]["value"]) + float(listing.get("shippingCost", 0.0))

    math = DealMath(
        buy_price=buy_price,
        est_resale_price=est_resale_price,
        resale_shipping_cost=estimate_resale_shipping_cost(est_resale_price),
    )

    return ScoredDeal(
        title=listing["title"],
        listing_url=listing["itemWebUrl"],
        buy_price=round(buy_price, 2),
        est_resale_price=est_resale_price,
        net_profit=math.net_profit,
        margin_pct=math.margin_pct,
        days_listed=days_listed,
        watch_count=watch_count,
        needs_manual_verification=math.margin_pct > SANITY_MARGIN_PCT,
        comp_source_note="from comps.csv",
    )


def _resale_potential_key(deal: "ScoredDeal"):
    """
    Rank by how likely the card is to actually resell, not just raw profit --
    a $200 card 20 people are watching moves faster than a $500 card no one's
    looking at, even if the second one nets more dollars. Watch count is the
    primary sort key (more watchers = more buyer demand right now); net
    profit breaks ties within the same demand level. Listings from before
    watchCount access is approved sort as if they have 0 watchers -- known
    demand should always outrank unknown demand.
    """
    watch_count = deal.watch_count if deal.watch_count is not None else 0
    return (-watch_count, -deal.net_profit)


def find_deals(listings: list, comps: dict) -> list:
    """Score every listing, filter to ones that clear the profit bar, rank by resale potential."""
    scored = [score_listing(l, comps) for l in listings]
    scored = [d for d in scored if d is not None]

    good_deals = [
        d for d in scored
        if d.net_profit >= MIN_NET_PROFIT and d.margin_pct >= MIN_MARGIN_PCT
    ]
    good_deals.sort(key=_resale_potential_key)
    return good_deals
