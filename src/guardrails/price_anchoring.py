"""Price Anchoring Guardrail: filters add-ons that exceed the price anchor threshold."""

from typing import List, Dict, Any, Tuple


def get_price_threshold(cart_total: float) -> float:
    """
    Get the maximum allowed add-on price based on cart total.

    Tiered thresholds ensure add-ons are priced appropriately:
    - cart < ₹200: max ₹69 addon
    - ₹200-₹400: max ₹99
    - ₹400-₹700: max ₹149
    - ₹700+: max ₹199 (or 30% of cart, whichever is higher)
    """
    if cart_total < 200:
        return 69.0
    elif cart_total < 400:
        return 99.0
    elif cart_total < 700:
        return 149.0
    else:
        return max(199.0, cart_total * 0.30)


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
                    f"₹{threshold:.0f} for ₹{cart_total:.0f} cart"
                ),
            })

    return approved, blocked
