"""Price Anchoring Guardrail: filters add-ons that exceed 30% of cart value."""

from typing import List, Dict, Any, Tuple


def get_price_threshold(cart_total: float) -> float:
    """
    Get the maximum allowed add-on price based on cart total.
    
    Rules:
    - cart < ₹200: max ₹60
    - ₹200-₹400: max ₹99
    - ₹400-₹700: max ₹149
    - ₹700+: max ₹199
    But never more than 30% of cart_total.
    """
    pct_limit = cart_total * 0.30
    if cart_total < 200:
        tier_limit = 60
    elif cart_total < 400:
        tier_limit = 99
    elif cart_total < 700:
        tier_limit = 149
    else:
        tier_limit = 199
    return min(pct_limit, tier_limit)


def filter_by_price(
    candidates: List[Dict[str, Any]],
    cart_total: float,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter candidates exceeding the price anchor threshold.
    
    Returns:
        (approved, blocked): approved candidates and blocked ones with reason.
    """
    threshold = get_price_threshold(cart_total)
    approved = []
    blocked = []

    for item in candidates:
        price = item.get("price", 0)
        if price <= threshold:
            approved.append(item)
        else:
            blocked.append({
                **item,
                "reason": (
                    f"BLOCKED — Price ₹{price} exceeds anchor threshold "
                    f"₹{threshold:.0f} (30% of ₹{cart_total:.0f} cart)"
                ),
            })

    return approved, blocked
