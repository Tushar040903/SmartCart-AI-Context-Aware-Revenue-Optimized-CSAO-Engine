"""A/B Test Simulator: compares 4 recommendation strategies."""

import sys
import random
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Callable

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.metrics import compute_all_metrics


def _load_menu():
    path = project_root / "data" / "raw" / "menu_items.json"
    with open(path) as f:
        return json.load(f)


def _load_orders():
    path = project_root / "data" / "synthetic" / "orders.json"
    if not path.exists():
        from data.synthetic.generate_orders import generate_orders
        generate_orders()
    with open(path) as f:
        return json.load(f)


# Strategy 1: Random Baseline
def random_strategy(cart_items, menu, context, n=3):
    non_main = [m for m in menu if m["category"] != "main_course"]
    cart_ids = {item["item_id"] for item in cart_items}
    candidates = [m for m in non_main if m["item_id"] not in cart_ids]
    sample = random.sample(candidates, min(n, len(candidates)))
    return [{"name": s["name"], "category": s["category"], 
             "price": s["price"], "kpt_minutes": s["kpt_minutes"]} for s in sample]


# Strategy 2: Apriori (generic pairings from data)
def apriori_strategy(cart_items, menu, context, n=3):
    path = project_root / "data" / "raw" / "food_pairings.json"
    with open(path) as f:
        pairings = json.load(f)
    
    cart_names = {item["name"] for item in cart_items}
    menu_by_name = {m["name"]: m for m in menu}
    pairing_map = {}
    for p in pairings:
        for item_name in [p["item1"], p["item2"]]:
            other = p["item2"] if item_name == p["item1"] else p["item1"]
            pairing_map.setdefault(item_name, []).append((other, p["pairing_strength"]))
    
    scored = {}
    for cart_item in cart_items:
        for paired, strength in pairing_map.get(cart_item["name"], []):
            if paired not in cart_names and paired in menu_by_name:
                scored[paired] = max(scored.get(paired, 0), strength)
    
    top = sorted(scored.items(), key=lambda x: x[1], reverse=True)[:n]
    results = []
    for name, _ in top:
        m = menu_by_name[name]
        results.append({"name": m["name"], "category": m["category"],
                        "price": m["price"], "kpt_minutes": m["kpt_minutes"]})
    return results


# Strategy 3: SmartCart v1 (ML only, no guardrails)
def smartcart_v1_strategy(cart_items, menu, context, n=3):
    from src.candidate_generation.knowledge_graph_recommender import KnowledgeGraphRecommender
    from src.ranking.conversion_model import ConversionModel
    
    recommender = KnowledgeGraphRecommender()
    model = ConversionModel()
    
    cart_ids = [item["item_id"] for item in cart_items]
    candidates = recommender.get_candidates(cart_ids, context=context, max_candidates=30)
    
    cart_total = sum(item.get("price", 0) for item in cart_items)
    cart_max_kpt = max((item.get("kpt_minutes", 0) for item in cart_items), default=0)
    
    features_list = []
    for c in candidates:
        addon_price = c.get("price", 0)
        price_ratio = addon_price / cart_total if cart_total > 0 else 0
        features_list.append({
            "cart_total": cart_total,
            "cart_item_count": len(cart_items),
            "cuisine_type": 0,
            "time_of_day": context.get("hour", 19),
            "is_weekend": int(context.get("is_weekend", False)),
            "weather": {"sunny": 0, "rainy": 1, "cold": 2, "hot": 3}.get(context.get("weather", "sunny"), 0),
            "addon_price": addon_price,
            "price_ratio": price_ratio,
            "price_fit": 0.5,
            "addon_category": 1,
            "order_type": 0,
            "restaurant_type": 0,
            "addon_popularity": c.get("popularity_score", 0.5),
            "addon_kpt": c.get("kpt_minutes", 0),
            "cart_max_kpt": cart_max_kpt,
            "kpt_delta": max(0, c.get("kpt_minutes", 0) - cart_max_kpt),
            "addon_margin": c.get("margin_pct", 0.4),
        })
    
    probs = model.predict_batch(features_list)
    scored = sorted(zip(candidates, probs), key=lambda x: x[1], reverse=True)[:n]
    return [{"name": c["name"], "category": c["category"],
             "price": c["price"], "kpt_minutes": c.get("kpt_minutes", 0)} 
            for c, _ in scored]


# Strategy 4: SmartCart v2 (Full system)
def smartcart_v2_strategy(cart_items, menu, context, n=3):
    from src.pipeline.smartcart_engine import SmartCartEngine
    engine = SmartCartEngine()
    result = engine.recommend(
        cart_items=cart_items,
        hour=context.get("hour", 19),
        weather=context.get("weather", "sunny"),
        is_weekend=context.get("is_weekend", False),
    )
    recs = result["recommendations"]
    return [{"name": r["name"], "category": r["category"],
             "price": r["price"], "kpt_minutes": r.get("kpt_minutes", 0)} 
            for r in recs[:n]]


def simulate_session(
    cart_items: List[Dict],
    strategy_fn: Callable,
    menu: List[Dict],
    context: Dict,
    user_accept_rate: float = 0.35,
) -> Dict:
    """
    Simulate one user session for a given strategy.
    Returns a session dict with metrics.
    """
    try:
        recs = strategy_fn(cart_items, menu, context, n=3)
    except Exception:
        recs = []
    
    cart_max_kpt = max((item.get("kpt_minutes", 0) for item in cart_items), default=0)
    cart_total = sum(item.get("price", 0) for item in cart_items)
    
    # Simulate user acceptance
    added = False
    addon_value = 0
    addon_revenue = 0
    kpt_delay = 0
    
    for rec in recs:
        # Acceptance probability influenced by price ratio
        price = rec.get("price", 0)
        ratio = price / cart_total if cart_total > 0 else 0
        accept_prob = user_accept_rate * (1.2 if ratio < 0.2 else 0.8)
        if random.random() < accept_prob:
            added = True
            addon_value += price
            addon_revenue += price * rec.get("margin_pct", 0.4)
            kpt_delay = max(kpt_delay, max(0, rec.get("kpt_minutes", 0) - cart_max_kpt))
            break  # assume user adds first accepted item
    
    return {
        "addon_added": added,
        "addon_value": addon_value,
        "addon_revenue": addon_revenue,
        "kpt_delay": kpt_delay,
        "recommendations": recs,
    }


def run_ab_test(n_sessions: int = 5000) -> Dict[str, Any]:
    """
    Run a simulated A/B test comparing 4 strategies.
    
    Returns dict with metrics per strategy.
    """
    random.seed(42)
    np.random.seed(42)
    
    menu = _load_menu()
    orders = _load_orders()
    
    strategies = {
        "Random Baseline": random_strategy,
        "Apriori (Generic)": apriori_strategy,
        "SmartCart v1 (ML Only)": smartcart_v1_strategy,
        "SmartCart v2 (Full)": smartcart_v2_strategy,
    }
    
    # Sample sessions from real orders
    sample_orders = random.choices(orders, k=n_sessions)
    
    results = {}
    
    for strategy_name, strategy_fn in strategies.items():
        print(f"Running strategy: {strategy_name}...")
        sessions = []
        
        for order in sample_orders:
            cart_items = order.get("items", [])
            if not cart_items:
                continue
            
            # Filter to main course items only as starting cart
            main_items = [i for i in cart_items if i.get("category") == "main_course"]
            if not main_items:
                continue
            
            context = {
                "hour": order.get("time_of_day", 19),
                "is_weekend": order.get("is_weekend", False),
                "weather": order.get("weather", "sunny"),
            }
            
            session = simulate_session(main_items, strategy_fn, menu, context)
            sessions.append(session)
        
        results[strategy_name] = compute_all_metrics(sessions)
        print(f"  -> ATC Rate: {results[strategy_name]['add_to_cart_rate']:.3f}, "
              f"AOV Uplift: ₹{results[strategy_name]['aov_uplift_inr']:.2f}")
    
    return results


if __name__ == "__main__":
    results = run_ab_test(n_sessions=2000)
    print("\n=== A/B Test Results ===")
    for strategy, metrics in results.items():
        print(f"\n{strategy}:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
