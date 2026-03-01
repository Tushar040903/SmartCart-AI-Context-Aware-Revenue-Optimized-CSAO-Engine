"""Business Constraints: combines all guardrails into one pipeline."""

import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from guardrails.price_anchoring import filter_by_price
from guardrails.rail_size_optimizer import apply_rail_size
from candidate_generation.kpt_filter import filter_by_kpt
from candidate_generation.dietary_filter import filter_by_dietary
from ranking.diversity_controller import apply_diversity


def apply_all_guardrails(
    candidates: List[Dict[str, Any]],
    cart_total: float,
    cart_max_kpt: int,
    cart_item_count: int,
    is_veg: bool,
    order_type: str = "solo",
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Apply all business guardrails in sequence:
    1. Dietary filter (veg/non-veg)
    2. KPT filter (Zero-ETA-Impact)
    3. Price anchor filter
    4. Diversity filter (max 1 per category)
    5. Rail size optimizer
    
    Args:
        candidates: ranked list of candidate add-ons.
        cart_total: total value of the cart.
        cart_max_kpt: maximum KPT of items in cart.
        cart_item_count: number of items in cart.
        is_veg: user dietary preference.
        order_type: 'solo' or 'group'.
    
    Returns:
        (final_recommendations, suppression_log) where suppression_log has keys:
        'dietary', 'kpt', 'price', 'diversity'.
    """
    suppression_log: Dict[str, List] = {
        "dietary": [],
        "kpt": [],
        "price": [],
        "diversity": [],
    }

    # 1. Dietary filter
    candidates, dietary_blocked = filter_by_dietary(candidates, is_veg)
    suppression_log["dietary"] = dietary_blocked

    # 2. KPT filter
    candidates, kpt_blocked = filter_by_kpt(candidates, cart_max_kpt)
    suppression_log["kpt"] = kpt_blocked

    # 3. Price anchor
    candidates, price_blocked = filter_by_price(candidates, cart_total)
    suppression_log["price"] = price_blocked

    # 4. Diversity
    candidates = apply_diversity(candidates, max_per_category=1)

    # 5. Rail size
    candidates = apply_rail_size(candidates, cart_item_count)

    return candidates, suppression_log
