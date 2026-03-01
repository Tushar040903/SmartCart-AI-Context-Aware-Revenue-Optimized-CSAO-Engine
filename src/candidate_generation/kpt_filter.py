"""KPT Filter: Zero-ETA-Impact filter — the key differentiator."""

from typing import List, Dict, Any, Tuple


def filter_by_kpt(
    candidates: List[Dict[str, Any]],
    cart_max_kpt: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter add-on candidates by Kitchen Prep Time (KPT).
    
    Only allows add-ons whose KPT <= cart_max_kpt to ensure Zero-ETA-Impact.
    Any add-on that would delay the order is suppressed and logged.
    
    Args:
        candidates: list of candidate item dicts, each with 'kpt_minutes'.
        cart_max_kpt: the maximum KPT of items already in the cart.
    
    Returns:
        (approved, suppressed_log):
            approved: items that pass the KPT guardrail.
            suppressed_log: list of dicts explaining why items were blocked.
    """
    approved = []
    suppressed_log = []

    for item in candidates:
        item_kpt = item.get("kpt_minutes", 0)
        if item_kpt <= cart_max_kpt:
            approved.append(item)
        else:
            delay = item_kpt - cart_max_kpt
            suppressed_log.append({
                "item": item.get("name", "Unknown"),
                "item_id": item.get("item_id", ""),
                "reason": (
                    f"BLOCKED — KPT {item_kpt}min would delay order by "
                    f"{delay}min beyond cart max KPT of {cart_max_kpt}min"
                ),
                "addon_kpt": item_kpt,
                "cart_max_kpt": cart_max_kpt,
                "delay_minutes": delay,
            })

    return approved, suppressed_log
