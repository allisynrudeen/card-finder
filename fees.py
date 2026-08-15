"""
eBay fee calculator for the Trading Cards category.

Rates as of Aug 2026 (non-Store seller tier), sourced from eBay's published fee
schedule. VERIFY THESE PERIODICALLY -- eBay changes fee rates, and sometimes
runs temporary discounted-fee promotions specifically for higher-value trading
cards. Update the constants below if your account is enrolled in a Store
subscription or a promo is active.
"""

from dataclasses import dataclass


# Non-Store seller, standard Trading Cards category rate.
FINAL_VALUE_FEE_RATE_TIER1 = 0.136   # 13.6% on the portion of sale <= $7,500
FINAL_VALUE_FEE_RATE_TIER2 = 0.0235  # 2.35% on the portion of sale > $7,500
TIER1_CAP = 7500.00

# eBay's fixed per-order fee (in addition to the percentage fee above).
FIXED_FEE_LOW = 0.30   # orders <= $10.00
FIXED_FEE_HIGH = 0.40  # orders > $10.00
FIXED_FEE_THRESHOLD = 10.00

# Top Rated Seller Plus members get a 10% discount on the *percentage* portion
# only (not the fixed fee). Set this True once you qualify.
IS_TOP_RATED_SELLER_PLUS = False


def ebay_final_value_fee(sale_price: float) -> float:
    """Return the total eBay fee (percentage + fixed) for a given sale price."""
    tier1_amount = min(sale_price, TIER1_CAP)
    tier2_amount = max(0.0, sale_price - TIER1_CAP)

    rate1 = FINAL_VALUE_FEE_RATE_TIER1
    rate2 = FINAL_VALUE_FEE_RATE_TIER2
    if IS_TOP_RATED_SELLER_PLUS:
        rate1 *= 0.90
        rate2 *= 0.90

    pct_fee = tier1_amount * rate1 + tier2_amount * rate2
    fixed_fee = FIXED_FEE_LOW if sale_price <= FIXED_FEE_THRESHOLD else FIXED_FEE_HIGH
    return round(pct_fee + fixed_fee, 2)


@dataclass
class DealMath:
    buy_price: float          # what you'd pay to acquire the card (item + its shipping to you)
    est_resale_price: float   # what you expect to sell it for
    resale_shipping_cost: float  # what it costs YOU to ship it when you resell (materials + postage)
    grading_cost: float = 0.0    # optional: PSA/BGS grading cost if the flip depends on grading

    @property
    def ebay_fee_on_resale(self) -> float:
        return ebay_final_value_fee(self.est_resale_price)

    @property
    def total_cost(self) -> float:
        return round(
            self.buy_price + self.resale_shipping_cost + self.grading_cost + self.ebay_fee_on_resale,
            2,
        )

    @property
    def net_profit(self) -> float:
        return round(self.est_resale_price - self.total_cost, 2)

    @property
    def margin_pct(self) -> float:
        if self.buy_price <= 0:
            return 0.0
        return round((self.net_profit / self.buy_price) * 100, 1)
