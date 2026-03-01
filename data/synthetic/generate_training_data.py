"""Generate training data from synthetic orders for the conversion model."""

import json
import random
import os
import pandas as pd
import numpy as np
from pathlib import Path

CUISINE_MAP = {
    "North Indian": 0,
    "South Indian": 1,
    "Chinese": 2,
    "Italian": 3,
    "Continental": 4,
    "Street Food": 5,
    "Desserts": 6,
    "Beverages": 7,
}

CATEGORY_MAP = {
    "main_course": 0,
    "side": 1,
    "beverage": 2,
    "dessert": 3,
    "appetizer": 4,
}

WEATHER_MAP = {
    "sunny": 0,
    "rainy": 1,
    "cold": 2,
    "hot": 3,
}

ORDER_TYPE_MAP = {
    "solo": 0,
    "group": 1,
}

RESTAURANT_TYPE_MAP = {
    "QSR": 0,
    "Casual Dining": 1,
    "Fine Dining": 2,
    "Cloud Kitchen": 3,
    "Cafe": 4,
}

def load_json(path):
    with open(path) as f:
        return json.load(f)

def generate_training_data(output_path=None):
    """Generate ML training data from orders."""
    random.seed(42)
    np.random.seed(42)
    
    base = Path(__file__).parent
    
    orders_path = base / "orders.json"
    if not orders_path.exists():
        # Generate orders first
        from data.synthetic.generate_orders import generate_orders
        generate_orders()
    
    orders = load_json(orders_path)
    menu = load_json(base.parent / "raw" / "menu_items.json")
    
    item_by_name = {item["name"]: item for item in menu}
    item_by_id = {item["item_id"]: item for item in menu}
    
    rows = []
    
    for order in orders:
        cart_items = order["items"]
        cart_total = order["cart_total"]
        cart_item_count = len(cart_items)
        time_of_day = order["time_of_day"]
        is_weekend = int(order["is_weekend"])
        weather = order.get("weather", "sunny")
        order_type = order.get("order_type", "solo")
        restaurant_type = order.get("restaurant_type", "QSR")
        
        # Determine dominant cuisine from cart
        cart_cuisines = [item_by_name.get(item["name"], {}).get("cuisine", "North Indian")
                         for item in cart_items]
        if cart_cuisines:
            dominant_cuisine = max(set(cart_cuisines), key=cart_cuisines.count)
        else:
            dominant_cuisine = "North Indian"
        
        # Max KPT in cart
        cart_kpts = [item.get("kpt_minutes", 0) for item in cart_items]
        cart_max_kpt = max(cart_kpts) if cart_kpts else 0
        
        # Items already in cart (positive label)
        cart_item_names = {item["name"] for item in cart_items}
        cart_item_names_by_category = {}
        for item in cart_items:
            cart_item_names_by_category.setdefault(item["category"], set()).add(item["name"])
        
        # For each menu item not in main_course, decide if it's an addon
        for addon in menu:
            if addon["category"] == "main_course":
                continue
            
            addon_name = addon["name"]
            addon_price = addon["price"]
            addon_category = addon["category"]
            addon_kpt = addon["kpt_minutes"]
            addon_cuisine = addon.get("cuisine", "Beverages")
            
            # Target: 1 if added to this order
            target = 1 if addon_name in cart_item_names else 0
            
            price_ratio = addon_price / cart_total if cart_total > 0 else 0
            
            # Price fit: how well does this addon fit the cart total (closer to 15-20% is ideal)
            ideal_ratio = 0.17
            price_fit = max(0, 1 - abs(price_ratio - ideal_ratio) / ideal_ratio)
            
            row = {
                "cart_total": cart_total,
                "cart_item_count": cart_item_count,
                "cuisine_type": CUISINE_MAP.get(dominant_cuisine, 0),
                "time_of_day": time_of_day,
                "is_weekend": is_weekend,
                "weather": WEATHER_MAP.get(weather, 0),
                "addon_price": addon_price,
                "price_ratio": round(price_ratio, 4),
                "price_fit": round(price_fit, 4),
                "addon_category": CATEGORY_MAP.get(addon_category, 1),
                "order_type": ORDER_TYPE_MAP.get(order_type, 0),
                "restaurant_type": RESTAURANT_TYPE_MAP.get(restaurant_type, 0),
                "addon_popularity": addon.get("popularity_score", 0.5),
                "addon_kpt": addon_kpt,
                "cart_max_kpt": cart_max_kpt,
                "kpt_delta": max(0, addon_kpt - cart_max_kpt),
                "addon_margin": addon.get("margin_pct", 0.4),
                "target": target,
            }
            rows.append(row)
    
    df = pd.DataFrame(rows)
    
    if output_path is None:
        output_path = base / "training_data.csv"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} training rows -> {output_path}")
    print(f"Positive rate: {df['target'].mean():.3f}")
    return df

if __name__ == "__main__":
    generate_training_data()
