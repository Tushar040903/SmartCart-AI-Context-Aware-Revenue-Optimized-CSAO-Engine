"""Cart Analyzer: extracts key features from the current cart."""

from typing import List, Dict, Any

class CartAnalyzer:
    """Analyzes cart contents to extract context features."""

    def analyze(self, cart_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the cart and return a context dictionary.
        
        Args:
            cart_items: List of item dicts with keys: item_id, name, category,
                        cuisine, price, is_veg, kpt_minutes.
        
        Returns:
            Dict with cart_total, item_count, dominant_cuisine, max_kpt,
            cart_categories, is_all_veg.
        """
        if not cart_items:
            return {
                "cart_total": 0,
                "item_count": 0,
                "dominant_cuisine": "North Indian",
                "max_kpt": 0,
                "cart_categories": [],
                "is_all_veg": True,
                "item_names": [],
                "item_ids": [],
            }

        cart_total = sum(item.get("price", 0) for item in cart_items)
        item_count = len(cart_items)
        
        # Dominant cuisine
        cuisines = [item.get("cuisine", "North Indian") for item in cart_items
                    if item.get("cuisine")]
        if cuisines:
            dominant_cuisine = max(set(cuisines), key=cuisines.count)
        else:
            dominant_cuisine = "North Indian"
        
        # Max KPT
        kpts = [item.get("kpt_minutes", 0) for item in cart_items]
        max_kpt = max(kpts) if kpts else 0
        
        # Categories in cart
        cart_categories = list(set(item.get("category", "") for item in cart_items))
        
        # Dietary check
        is_all_veg = all(item.get("is_veg", True) for item in cart_items)
        
        return {
            "cart_total": cart_total,
            "item_count": item_count,
            "dominant_cuisine": dominant_cuisine,
            "max_kpt": max_kpt,
            "cart_categories": cart_categories,
            "is_all_veg": is_all_veg,
            "item_names": [item.get("name", "") for item in cart_items],
            "item_ids": [item.get("item_id", "") for item in cart_items],
        }
