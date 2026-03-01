"""Generate 15,000+ synthetic orders with realistic patterns."""

import json
import random
import os
from pathlib import Path
from datetime import datetime, timedelta

def load_menu(menu_path=None):
    if menu_path is None:
        menu_path = Path(__file__).parent.parent / "raw" / "menu_items.json"
    with open(menu_path) as f:
        return json.load(f)

def load_pairings(pairings_path=None):
    if pairings_path is None:
        pairings_path = Path(__file__).parent.parent / "raw" / "food_pairings.json"
    with open(pairings_path) as f:
        return json.load(f)

def load_restaurants(restaurants_path=None):
    if restaurants_path is None:
        restaurants_path = Path(__file__).parent.parent / "raw" / "restaurant_profiles.json"
    with open(restaurants_path) as f:
        return json.load(f)

def generate_orders(n=15000, output_path=None):
    """Generate n synthetic orders with realistic patterns."""
    random.seed(42)
    
    menu = load_menu()
    pairings = load_pairings()
    restaurants = load_restaurants()
    
    # Build lookup maps
    item_by_name = {item["name"]: item for item in menu}
    items_by_category = {}
    for item in menu:
        cat = item["category"]
        items_by_category.setdefault(cat, []).append(item)
    
    # Build pairing map: item_name -> list of (paired_item_name, strength)
    pairing_map = {}
    for p in pairings:
        item1, item2 = p["item1"], p["item2"]
        strength = p["pairing_strength"]
        pairing_map.setdefault(item1, []).append((item2, strength))
        pairing_map.setdefault(item2, []).append((item1, strength))
    
    weathers = ["sunny", "rainy", "cold", "hot"]
    weather_weights = [0.45, 0.20, 0.15, 0.20]
    
    orders = []
    
    for i in range(1, n + 1):
        # Time context
        hour = random.choices(
            list(range(24)),
            weights=[1,1,1,1,1,1,2,3,4,5,4,4,6,6,4,3,3,5,7,8,7,6,4,2]
        )[0]
        day_of_week = random.randint(0, 6)
        is_weekend = day_of_week >= 5
        weather = random.choices(weathers, weights=weather_weights)[0]
        restaurant = random.choice(restaurants)
        
        # Determine order type (solo vs group)
        is_group = random.random() < 0.30 if is_weekend else random.random() < 0.15
        
        # Select main courses
        main_items = items_by_category.get("main_course", [])
        veg_mains = [x for x in main_items if x["is_veg"]]
        nonveg_mains = [x for x in main_items if not x["is_veg"]]
        
        user_is_veg = random.random() < 0.45
        
        if is_group:
            num_mains = random.randint(3, 5)
        else:
            num_mains = random.randint(1, 2)
        
        if user_is_veg:
            selected_mains = random.sample(veg_mains, min(num_mains, len(veg_mains)))
        else:
            # mix veg and non-veg
            n_nonveg = random.randint(1, min(num_mains, len(nonveg_mains)))
            n_veg = num_mains - n_nonveg
            selected_mains = (
                random.sample(nonveg_mains, n_nonveg) +
                random.sample(veg_mains, min(n_veg, len(veg_mains)))
            )
        
        order_items = [{"item_id": m["item_id"], "name": m["name"], 
                        "category": m["category"], "price": m["price"],
                        "is_veg": m["is_veg"], "kpt_minutes": m["kpt_minutes"]} 
                       for m in selected_mains]
        
        # Add side/beverage/dessert based on pairings
        addons_added = set()
        addon_categories = ["side", "beverage", "dessert"]
        
        for main in selected_mains:
            paired = pairing_map.get(main["name"], [])
            for paired_name, strength in paired:
                # Context boost
                if hour >= 22 and "Red Bull" in paired_name:
                    strength = min(1.0, strength + 0.2)
                if weather == "rainy" and ("Soup" in paired_name or "Chai" in paired_name):
                    strength = min(1.0, strength + 0.2)
                if weather in ["sunny", "hot"] and any(
                    x in paired_name for x in ["Cold Coffee", "Coke", "Lassi", "Ice Cream", "Mango"]):
                    strength = min(1.0, strength + 0.15)
                
                if random.random() < strength and paired_name in item_by_name:
                    paired_item = item_by_name[paired_name]
                    if paired_name not in addons_added:
                        # For group orders, prefer 2L versions
                        if is_group and paired_item.get("group_alternative_id"):
                            alt_id = paired_item["group_alternative_id"]
                            alt_items = [x for x in menu if x["item_id"] == alt_id]
                            if alt_items:
                                paired_item = alt_items[0]
                                paired_name = paired_item["name"]
                        
                        if paired_name not in addons_added:
                            order_items.append({
                                "item_id": paired_item["item_id"],
                                "name": paired_item["name"],
                                "category": paired_item["category"],
                                "price": paired_item["price"],
                                "is_veg": paired_item["is_veg"],
                                "kpt_minutes": paired_item["kpt_minutes"]
                            })
                            addons_added.add(paired_name)
        
        cart_total = sum(item["price"] for item in order_items)
        
        # Determine order type label
        main_count = sum(1 for item in order_items if item["category"] == "main_course")
        order_type = "group" if main_count >= 3 else "solo"
        
        orders.append({
            "order_id": f"order_{i:05d}",
            "user_id": f"user_{random.randint(1, 1000):04d}",
            "restaurant_id": restaurant["restaurant_id"],
            "restaurant_type": restaurant["type"],
            "items": order_items,
            "cart_total": cart_total,
            "time_of_day": hour,
            "is_weekend": is_weekend,
            "weather": weather,
            "order_type": order_type,
        })
    
    if output_path is None:
        output_path = Path(__file__).parent / "orders.json"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(orders, f, indent=2)
    
    print(f"Generated {len(orders)} orders -> {output_path}")
    return orders

if __name__ == "__main__":
    generate_orders()
