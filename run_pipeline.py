#!/usr/bin/env python3
"""
SmartCart AI — CLI Pipeline Runner

Usage:
  python run_pipeline.py --cart "Chicken Biryani,Raita" --time 21 --weather sunny --user_type nonveg
  python run_pipeline.py --cart "Maggi" --time 23 --weather cold --user_type veg
  python run_pipeline.py --cart "Veg Burger,Chicken Burger,Paneer Butter Masala" --time 20 --weather sunny --user_type nonveg
"""

import sys
import json
import argparse
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def load_menu():
    path = project_root / "data" / "raw" / "menu_items.json"
    with open(path) as f:
        return json.load(f)


def get_cart_items(cart_str: str, menu: list) -> list:
    """Parse cart string into list of menu item dicts."""
    menu_by_name = {item["name"].lower(): item for item in menu}
    cart_names = [name.strip() for name in cart_str.split(",")]
    
    cart_items = []
    for name in cart_names:
        item = menu_by_name.get(name.lower())
        if item:
            cart_items.append(item)
        else:
            print(f"  Warning: '{name}' not found in menu, skipping.")
    return cart_items


def print_recommendations(result: dict):
    """Pretty-print the recommendation results."""
    cart_ctx = result["cart_context"]
    temporal_ctx = result["temporal_context"]
    
    print("\n" + "=" * 60)
    print("SMARTCART AI — RECOMMENDATION RESULTS")
    print("=" * 60)
    
    print(f"\n📦 Cart Context:")
    print(f"   Total: ₹{cart_ctx['cart_total']}")
    print(f"   Items: {cart_ctx['item_count']}")
    print(f"   Dominant Cuisine: {cart_ctx['dominant_cuisine']}")
    print(f"   Max KPT: {cart_ctx['max_kpt']} min")
    print(f"   Order Type: {result['order_type'].upper()}")
    
    print(f"\n⏰ Context:")
    print(f"   Meal Period: {temporal_ctx['meal_period']}")
    print(f"   Weather: {temporal_ctx['weather']}")
    print(f"   Weekend: {'Yes' if temporal_ctx['is_weekend'] else 'No'}")
    
    recs = result["recommendations"]
    if recs:
        print(f"\n🛒 Top {len(recs)} Recommended Add-ons:")
        for i, rec in enumerate(recs, 1):
            print(f"\n   {i}. {rec['name']} — ₹{rec['price']}")
            print(f"      Category: {rec.get('category', 'N/A')}")
            print(f"      KPT: {rec.get('kpt_minutes', 0)} min")
            print(f"      Conversion Prob: {rec.get('conversion_prob', 0):.2%}")
            print(f"      Rank Score: {rec.get('rank_score', 0):.4f}")
            if rec.get("reason"):
                print(f"      Reason: {rec['reason']}")
    else:
        print("\n⚠️  No recommendations available for this cart.")
    
    # Suppression log
    supp = result["suppression_log"]
    kpt_blocked = supp.get("kpt", [])
    if kpt_blocked:
        print(f"\n🚫 KPT Guardrail — {len(kpt_blocked)} item(s) blocked:")
        for item in kpt_blocked:
            print(f"   ❌ {item['item']}: {item['reason']}")
    
    dietary_blocked = supp.get("dietary", [])
    if dietary_blocked:
        print(f"\n🥗 Dietary Filter — {len(dietary_blocked)} item(s) blocked:")
        for item in dietary_blocked[:3]:
            print(f"   ❌ {item.get('name', item.get('item', 'Unknown'))}: {item['reason']}")
    
    price_blocked = supp.get("price", [])
    if price_blocked:
        print(f"\n💰 Price Guardrail — {len(price_blocked)} item(s) blocked:")
        for item in price_blocked[:3]:
            print(f"   ❌ {item.get('name', 'Unknown')}: {item['reason']}")


def main():
    parser = argparse.ArgumentParser(
        description="SmartCart AI — Context-Aware Add-On Recommendation Engine"
    )
    parser.add_argument(
        "--cart",
        type=str,
        required=True,
        help='Comma-separated list of item names, e.g. "Chicken Biryani,Raita"',
    )
    parser.add_argument(
        "--time",
        type=int,
        default=19,
        help="Hour of day (0-23), default 19",
    )
    parser.add_argument(
        "--weather",
        type=str,
        default="sunny",
        choices=["sunny", "rainy", "cold", "hot"],
        help="Current weather",
    )
    parser.add_argument(
        "--user_type",
        type=str,
        default="nonveg",
        choices=["veg", "nonveg"],
        help="User dietary preference",
    )
    parser.add_argument(
        "--weekend",
        action="store_true",
        help="Flag if today is a weekend",
    )
    parser.add_argument(
        "--restaurant_type",
        type=str,
        default="QSR",
        choices=["QSR", "Casual Dining", "Fine Dining", "Cloud Kitchen", "Cafe"],
        help="Type of restaurant",
    )
    
    args = parser.parse_args()
    
    print("Loading menu and engine...")
    menu = load_menu()
    cart_items = get_cart_items(args.cart, menu)
    
    if not cart_items:
        print("Error: No valid cart items found. Check item names.")
        sys.exit(1)
    
    print(f"Cart: {[item['name'] for item in cart_items]}")
    
    from src.pipeline.smartcart_engine import SmartCartEngine
    engine = SmartCartEngine()
    
    user_profile = {
        "is_veg": args.user_type == "veg",
        "avg_spend": 400,
    }
    
    result = engine.recommend(
        cart_items=cart_items,
        user_profile=user_profile,
        hour=args.time,
        weather=args.weather,
        is_weekend=args.weekend,
        restaurant_type=args.restaurant_type,
    )
    
    print_recommendations(result)


if __name__ == "__main__":
    main()
