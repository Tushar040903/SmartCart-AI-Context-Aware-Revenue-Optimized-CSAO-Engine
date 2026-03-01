"""Rail Size Optimizer: determines how many add-ons to show based on cart size."""

from typing import List, Dict, Any


def get_rail_size(cart_item_count: int) -> int:
    """
    Determine number of add-ons to show based on cart item count.
    
    - 1 item cart → 4 add-ons
    - 2-3 items → 3 add-ons
    - 4 items → 2 add-ons
    - 5+ items → 1-2 add-ons
    """
    if cart_item_count == 1:
        return 4
    elif cart_item_count <= 3:
        return 3
    else:
        return 2


def apply_rail_size(
    candidates: List[Dict[str, Any]],
    cart_item_count: int,
) -> List[Dict[str, Any]]:
    """
    Trim the candidate list to the optimal rail size.
    
    Args:
        candidates: ranked/filtered list of candidates.
        cart_item_count: number of items in cart.
    
    Returns:
        Trimmed list.
    """
    size = get_rail_size(cart_item_count)
    return candidates[:size]
