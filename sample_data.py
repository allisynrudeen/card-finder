"""
Mock data standing in for two real data sources we don't have wired up yet:

1. `SAMPLE_LISTINGS` -- what the eBay Browse API search results will look like
   once we have API keys (active "Buy It Now" listings in Trading Cards).
2. `SAMPLE_COMPS` -- a price-guide lookup, keyed loosely by card name, standing
   in for whatever comps source we pick (PriceCharting API, manual list, etc).
   In a real run this would be a live lookup, not a hardcoded dict.

Field names roughly match what eBay's Browse API actually returns
(itemId, title, price.value, shippingOptions, itemWebUrl, condition) so
swapping in real API data later is mostly a find-and-replace of the fetch
function, not a rewrite of the scoring logic.
"""

SAMPLE_LISTINGS = [
    {
        "itemId": "v1|123456789|0",
        "title": "2018 Panini Prizm Luka Doncic Rookie PSA 9",
        "price": {"value": "130.00", "currency": "USD"},
        "shippingCost": 4.99,
        "condition": "Graded",
        "itemWebUrl": "https://www.ebay.com/itm/example1",
        "comp_key": "2018 Prizm Luka Doncic Rookie PSA 9",
        "daysListed": 12,
        "watchCount": 8,
    },
    {
        "itemId": "v1|223456789|0",
        "title": "2003 Topps Chrome LeBron James Rookie PSA 8",
        "price": {"value": "410.00", "currency": "USD"},
        "shippingCost": 6.50,
        "condition": "Graded",
        "itemWebUrl": "https://www.ebay.com/itm/example2",
        "comp_key": "2003 Topps Chrome LeBron James Rookie PSA 8",
        "daysListed": 25,
        "watchCount": 3,
    },
    {
        "itemId": "v1|323456789|0",
        "title": "2020 Prizm Justin Herbert Rookie PSA 10",
        "price": {"value": "95.00", "currency": "USD"},
        "shippingCost": 4.50,
        "condition": "Graded",
        "itemWebUrl": "https://www.ebay.com/itm/example3",
        "comp_key": "2020 Prizm Justin Herbert Rookie PSA 10",
        "daysListed": 40,
        "watchCount": 1,
    },
    {
        "itemId": "v1|423456789|0",
        "title": "2021 Bowman Chrome Wander Franco Auto PSA 9",
        "price": {"value": "60.00", "currency": "USD"},
        "shippingCost": 4.00,
        "condition": "Graded",
        "itemWebUrl": "https://www.ebay.com/itm/example4",
        "comp_key": "2021 Bowman Chrome Wander Franco Auto PSA 9",
        "daysListed": 90,
        "watchCount": 0,
    },
    {
        "itemId": "v1|523456789|0",
        "title": "2022 Bowman Chrome Julio Rodriguez Rookie Auto PSA 10",
        "price": {"value": "180.00", "currency": "USD"},
        "shippingCost": 5.00,
        "condition": "Graded",
        "itemWebUrl": "https://www.ebay.com/itm/example5",
        "comp_key": "2022 Bowman Chrome Julio Rodriguez Rookie Auto PSA 10",
        "daysListed": 6,
        "watchCount": 14,
    },
    {
        # Included to demonstrate demand-based ranking: this card nets MORE
        # raw profit than the Julio Rodriguez listing above, but almost no
        # one is watching it, so it should still rank BELOW a lower-profit,
        # higher-demand card -- easier to actually resell wins over bigger
        # profit on paper.
        "itemId": "v1|723456789|0",
        "title": "2021 Panini Mosaic Ja Morant PSA 10",
        "price": {"value": "150.00", "currency": "USD"},
        "shippingCost": 5.00,
        "condition": "Graded",
        "itemWebUrl": "https://www.ebay.com/itm/example7",
        "comp_key": "2021 Panini Mosaic Ja Morant PSA 10",
        "daysListed": 15,
        "watchCount": 3,
    },
    {
        # Included to demonstrate the staleness filter: this one LOOKS like a
        # great deal on price alone, but it's been sitting 310 days with zero
        # watchers -- exactly the "nobody's interested" pattern you flagged.
        # It gets excluded even though the raw profit math looks good.
        "itemId": "v1|623456789|0",
        "title": "2019 Panini Prizm Zion Williamson Rookie PSA 9",
        "price": {"value": "150.00", "currency": "USD"},
        "shippingCost": 5.00,
        "condition": "Graded",
        "itemWebUrl": "https://www.ebay.com/itm/example6",
        "comp_key": "2019 Panini Prizm Zion Williamson Rookie PSA 9",
        "daysListed": 310,
        "watchCount": 0,
    },
]

# Stand-in "market value" reference -- in production this comes from a live
# comps API/source (SportsCardsPro), not a hardcoded number.
SAMPLE_COMPS = {
    "2018 Prizm Luka Doncic Rookie PSA 9": 210.00,
    "2003 Topps Chrome LeBron James Rookie PSA 8": 520.00,
    "2020 Prizm Justin Herbert Rookie PSA 10": 115.00,
    "2021 Bowman Chrome Wander Franco Auto PSA 9": 58.00,   # Franco's value has fallen -- flagged as a bad flip below
    "2022 Bowman Chrome Julio Rodriguez Rookie Auto PSA 10": 280.00,
    "2021 Panini Mosaic Ja Morant PSA 10": 310.00,
    "2019 Panini Prizm Zion Williamson Rookie PSA 9": 250.00,
}
