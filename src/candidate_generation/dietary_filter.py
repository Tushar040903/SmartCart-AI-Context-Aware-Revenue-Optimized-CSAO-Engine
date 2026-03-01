"""Dietary Filter: filters add-ons based on user dietary preferences."""

from typing import List, Dict, Any, Tuple


def filter_by_dietary(
    candidates: List[Dict[str, Any]],
    is_veg: bool,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter candidates by dietary preference.
    
    Args:
        candidates: list of candidate dicts with 'is_veg' field.
        is_veg: True if user is vegetarian (filter out non-veg items).
    
    Returns:
        (approved, filtered_out): approved items and filtered-out items.
    """
    if not is_veg:
        # Non-veg users can have both veg and non-veg items
        return candidates, []
    
    approved = []
    filtered_out = []
    for item in candidates:
        if item.get("is_veg", True):
            approved.append(item)
        else:
            filtered_out.append({
                **item,
                "reason": "BLOCKED — Non-veg item filtered for vegetarian user",
            })
    return approved, filtered_out
