"""Build the Food Knowledge Graph using NetworkX."""

import json
import networkx as nx
import pickle
import os
from pathlib import Path

def build_food_knowledge_graph(
    menu_path=None,
    pairings_path=None,
    restaurants_path=None,
    output_path=None,
):
    """Build and save the food knowledge graph."""
    base = Path(__file__).parent.parent
    
    if menu_path is None:
        menu_path = base / "raw" / "menu_items.json"
    if pairings_path is None:
        pairings_path = base / "raw" / "food_pairings.json"
    if restaurants_path is None:
        restaurants_path = base / "raw" / "restaurant_profiles.json"
    if output_path is None:
        output_path = Path(__file__).parent / "food_graph.pkl"
    
    with open(menu_path) as f:
        menu = json.load(f)
    with open(pairings_path) as f:
        pairings = json.load(f)
    with open(restaurants_path) as f:
        restaurants = json.load(f)
    
    G = nx.Graph()
    
    # Add Item nodes
    for item in menu:
        G.add_node(item["item_id"], 
                   node_type="item",
                   name=item["name"],
                   category=item["category"],
                   cuisine=item.get("cuisine", ""),
                   price=item["price"],
                   is_veg=item["is_veg"],
                   kpt_minutes=item["kpt_minutes"],
                   margin_pct=item.get("margin_pct", 0.4),
                   popularity_score=item.get("popularity_score", 0.5),
                   available_sizes=item.get("available_sizes", ["Regular"]),
                   group_alternative_id=item.get("group_alternative_id"),
                   description=item.get("description", ""))
    
    # Add Category nodes
    categories = set(item["category"] for item in menu)
    for cat in categories:
        G.add_node(f"cat_{cat}", node_type="category", name=cat)
    
    # Add Cuisine nodes
    cuisines = set(item.get("cuisine", "") for item in menu if item.get("cuisine"))
    for cuisine in cuisines:
        G.add_node(f"cuisine_{cuisine.replace(' ', '_')}", node_type="cuisine", name=cuisine)
    
    # Add Restaurant Type nodes
    rtypes = set(r["type"] for r in restaurants)
    for rtype in rtypes:
        G.add_node(f"rtype_{rtype.replace(' ', '_')}", node_type="restaurant_type", name=rtype)
    
    # Add Time Context nodes
    time_contexts = ["breakfast", "lunch", "snack", "dinner", "late_night"]
    for tc in time_contexts:
        G.add_node(f"time_{tc}", node_type="time_context", name=tc)
    
    # Item -> Category edges (belongs_to)
    for item in menu:
        G.add_edge(item["item_id"], f"cat_{item['category']}", 
                   edge_type="belongs_to", weight=1.0)
    
    # Item -> Cuisine edges (belongs_to_cuisine)
    for item in menu:
        if item.get("cuisine"):
            cnode = f"cuisine_{item['cuisine'].replace(' ', '_')}"
            if G.has_node(cnode):
                G.add_edge(item["item_id"], cnode, 
                           edge_type="belongs_to_cuisine", weight=1.0)
    
    # Build name->id map
    name_to_id = {item["name"]: item["item_id"] for item in menu}
    
    # Pairing edges (pairs_with)
    for p in pairings:
        id1 = name_to_id.get(p["item1"])
        id2 = name_to_id.get(p["item2"])
        if id1 and id2:
            G.add_edge(id1, id2, 
                       edge_type="pairs_with",
                       weight=p["pairing_strength"],
                       reason=p.get("reason", ""),
                       context=p.get("context", ""))
    
    # Item -> Time context edges (best_time)
    time_mapping = {
        "breakfast": (6, 10),
        "lunch": (11, 14),
        "snack": (15, 18),
        "dinner": (18, 22),
        "late_night": (22, 6),
    }
    
    breakfast_items = ["Masala Dosa", "Idli Sambar", "Aloo Paratha", "Masala Chai", 
                       "Filter Coffee", "Hot Coffee", "Paneer Dosa"]
    lunch_items = ["Chicken Biryani", "Mutton Biryani", "Paneer Butter Masala",
                   "Dal Makhani", "Chole Bhature", "Veg Pulao"]
    dinner_items = ["Butter Chicken", "Tandoori Chicken", "Margherita Pizza",
                    "Pepperoni Pizza", "Pasta Alfredo"]
    late_night_items = ["Maggi", "Veg Burger", "Chicken Burger", "Red Bull",
                        "Veg Hakka Noodles", "Chicken Fried Rice"]
    snack_items = ["Samosa", "Pani Puri", "Aloo Tikki", "Masala Chai", "Veg Soup"]
    
    time_item_map = {
        "breakfast": breakfast_items,
        "lunch": lunch_items,
        "dinner": dinner_items,
        "late_night": late_night_items,
        "snack": snack_items,
    }
    
    for time_ctx, item_names in time_item_map.items():
        time_node = f"time_{time_ctx}"
        for item_name in item_names:
            item_id = name_to_id.get(item_name)
            if item_id:
                G.add_edge(item_id, time_node, edge_type="best_time", weight=0.8)
    
    # KPT-based edges (prep_requires)
    for item in menu:
        kpt = item["kpt_minutes"]
        if kpt == 0:
            G.nodes[item["item_id"]]["instant_prep"] = True
        elif kpt <= 5:
            G.nodes[item["item_id"]]["instant_prep"] = False
            G.nodes[item["item_id"]]["quick_prep"] = True
        else:
            G.nodes[item["item_id"]]["instant_prep"] = False
            G.nodes[item["item_id"]]["quick_prep"] = False
    
    # Save graph
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(G, f)
    
    print(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"Saved to {output_path}")
    return G

if __name__ == "__main__":
    build_food_knowledge_graph()
