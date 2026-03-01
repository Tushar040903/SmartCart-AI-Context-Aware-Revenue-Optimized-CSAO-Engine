"""Diversity Controller: ensures diverse add-on recommendations."""

from typing import List, Dict, Any


def apply_diversity(
    candidates: List[Dict[str, Any]],
    max_per_category: int = 1,
) -> List[Dict[str, Any]]:
    """
    Apply diversity constraint: max 1 item per category.
    
    Iterates candidates in rank order, keeping the top item per category.
    
    Args:
        candidates: ranked list of candidate dicts with 'category'.
        max_per_category: max number of items per category to keep.
    
    Returns:
        Filtered list respecting the diversity constraint.
    """
    seen_categories: Dict[str, int] = {}
    result = []
    
    for item in candidates:
        cat = item.get("category", "other")
        count = seen_categories.get(cat, 0)
        if count < max_per_category:
            result.append(item)
            seen_categories[cat] = count + 1
    
    return result
