"""
Real eBay Browse API client -- built exactly to eBay's documented REST API
contract, but NOT YET LIVE-TESTED. This cloud workspace's outbound network
access is restricted for security and can't reach api.ebay.com directly, so
this code needs to be run somewhere with normal internet access (your own
computer, or a free scheduled runner like GitHub Actions) before we know for
sure it's 100% correct. If eBay's docs are stale or a field name has since
changed, you may see an error the first time it actually runs -- that's
expected and fixable, not a sign something is fundamentally wrong.

Uses stdlib only (no `pip install` needed) so it runs anywhere with Python 3.

Docs referenced:
  https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search
  https://developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html
"""

import base64
import json
import os
import urllib.request
import urllib.parse
import urllib.error


def load_dotenv(path=".env"):
    """Tiny stdlib .env loader -- avoids needing `pip install python-dotenv`."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
SPORTS_TRADING_CARDS_CATEGORY_ID = "212"  # confirmed against ebay.com/b/Sports-Trading-Cards-Accessories/212/


def get_access_token(app_id: str, cert_id: str) -> str:
    """
    Client Credentials grant -- gets an application-level access token (no
    user login needed, since we're only reading public listings). Tokens are
    valid ~2 hours; for a once-a-day scan, just fetch a fresh one each run
    rather than bothering to cache/refresh it.
    """
    credentials = f"{app_id}:{cert_id}"
    basic_auth = base64.b64encode(credentials.encode()).decode()

    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Authorization", f"Basic {basic_auth}")

    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode())
    return payload["access_token"]


def search_listings(access_token: str, query: str, min_price: float = None, max_price: float = None, limit: int = 20) -> list:
    """
    Search active, Buy-It-Now sports trading card listings matching `query`.
    Returns eBay's raw itemSummaries list (not yet normalized/scored).
    """
    filters = ["buyingOptions:{FIXED_PRICE}"]
    if min_price is not None and max_price is not None:
        filters.append(f"price:[{min_price}..{max_price}],priceCurrency:USD")

    params = {
        "q": query,
        "category_ids": SPORTS_TRADING_CARDS_CATEGORY_ID,
        "filter": ",".join(filters),
        "limit": str(limit),
        "sort": "newlyListed",
    }
    url = f"{SEARCH_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("X-EBAY-C-MARKETPLACE-ID", "EBAY_US")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  eBay API error for query '{query}': {e.code} {e.read().decode()[:300]}")
        return []

    return payload.get("itemSummaries", [])


def normalize_listing(raw: dict, comp_key: str) -> dict:
    """
    Convert eBay's raw item summary into the shape scorer.py already expects
    (matches the fields used in sample_data.py).
    """
    price = raw.get("price", {})
    shipping_options = raw.get("shippingOptions", [])
    shipping_cost = 0.0
    if shipping_options:
        cost = shipping_options[0].get("shippingCost", {})
        shipping_cost = float(cost.get("value", 0.0))

    return {
        "itemId": raw.get("itemId"),
        "title": raw.get("title", ""),
        "price": {"value": price.get("value", "0"), "currency": price.get("currency", "USD")},
        "shippingCost": shipping_cost,
        "condition": raw.get("condition", "Unknown"),
        "itemWebUrl": raw.get("itemWebUrl", ""),
        "comp_key": comp_key,
        # eBay's Browse API doesn't return page-view counts; itemCreationDate
        # lets us compute listing age. watchCount is None until that extra
        # eBay permission (App Check ticket) is approved -- is_stale_listing()
        # and the resale-potential ranking already handle None gracefully.
        "daysListed": None,  # computed in run_live.py from itemCreationDate
        "watchCount": raw.get("watchCount"),  # will be None until approved
        "_itemCreationDate": raw.get("itemCreationDate"),
    }
