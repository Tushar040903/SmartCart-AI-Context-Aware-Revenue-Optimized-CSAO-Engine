"""Order Type Classifier: Solo vs Group order detection."""

from typing import List, Dict, Any


def classify_order_type(cart_items: List[Dict[str, Any]]) -> str:
    """
    Classify the order as 'solo' or 'group' based on cart contents.
    
    A group order has 3 or more main_course items.
    
    Args:
        cart_items: List of cart item dicts with at least a 'category' key.
    
    Returns:
        'group' if main_course count >= 3, else 'solo'.
    """
    main_count = sum(
        1 for item in cart_items if item.get("category") == "main_course"
    )
    return "group" if main_count >= 3 else "solo"
