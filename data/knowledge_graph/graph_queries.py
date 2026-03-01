"""Query functions for the Food Knowledge Graph."""

import pickle
import networkx as nx
from pathlib import Path

def load_graph(graph_path=None):
    """Load the food knowledge graph."""
    if graph_path is None:
        graph_path = Path(__file__).parent / "food_graph.pkl"
    with open(graph_path, "rb") as f:
        return pickle.load(f)

def get_candidate_addons(G, cart_item_ids, max_candidates=50):
    """Get candidate add-ons for items in cart using graph traversal."""
    candidates = {}
    
    for item_id in cart_item_ids:
        if not G.has_node(item_id):
            continue
        # Find neighbors connected by pairs_with edge
        for neighbor in G.neighbors(item_id):
            edge_data = G.edges[item_id, neighbor]
            if edge_data.get("edge_type") == "pairs_with":
                node_data = G.nodes[neighbor]
                if node_data.get("node_type") == "item":
                    # Skip if already in cart
                    if neighbor in cart_item_ids:
                        continue
                    score = edge_data.get("weight", 0.5)
                    reason = edge_data.get("reason", "")
                    if neighbor not in candidates or candidates[neighbor]["score"] < score:
                        candidates[neighbor] = {
                            "item_id": neighbor,
                            "name": node_data.get("name", ""),
                            "category": node_data.get("category", ""),
                            "cuisine": node_data.get("cuisine", ""),
                            "price": node_data.get("price", 0),
                            "is_veg": node_data.get("is_veg", True),
                            "kpt_minutes": node_data.get("kpt_minutes", 0),
                            "margin_pct": node_data.get("margin_pct", 0.4),
                            "popularity_score": node_data.get("popularity_score", 0.5),
                            "score": score,
                            "reason": reason,
                            "source_item_id": item_id,
                        }
    
    # Sort by score and return top candidates
    sorted_candidates = sorted(candidates.values(), key=lambda x: x["score"], reverse=True)
    return sorted_candidates[:max_candidates]

def get_pairings_for_item(G, item_id):
    """Get all items that pair with the given item."""
    if not G.has_node(item_id):
        return []
    pairings = []
    for neighbor in G.neighbors(item_id):
        edge_data = G.edges[item_id, neighbor]
        if edge_data.get("edge_type") == "pairs_with":
            node_data = G.nodes[neighbor]
            if node_data.get("node_type") == "item":
                pairings.append({
                    "item_id": neighbor,
                    "name": node_data.get("name"),
                    "strength": edge_data.get("weight", 0.5),
                    "reason": edge_data.get("reason", ""),
                })
    return sorted(pairings, key=lambda x: x["strength"], reverse=True)

def get_items_by_context(G, time_period=None, is_veg=None, max_kpt=None):
    """Get items filtered by context: time, dietary preference, KPT."""
    results = []
    
    for node_id, data in G.nodes(data=True):
        if data.get("node_type") != "item":
            continue
        
        # Filter by veg preference
        if is_veg is not None and data.get("is_veg") != is_veg:
            continue
        
        # Filter by KPT
        if max_kpt is not None and data.get("kpt_minutes", 0) > max_kpt:
            continue
        
        # Filter by time context
        if time_period is not None:
            time_node = f"time_{time_period}"
            if G.has_node(time_node) and not G.has_edge(node_id, time_node):
                continue
        
        results.append({
            "item_id": node_id,
            "name": data.get("name"),
            "category": data.get("category"),
            "price": data.get("price", 0),
            "is_veg": data.get("is_veg", True),
            "kpt_minutes": data.get("kpt_minutes", 0),
        })
    
    return results

def get_items_for_time_context(G, time_period):
    """Get items best suited for a given time period."""
    time_node = f"time_{time_period}"
    if not G.has_node(time_node):
        return []
    
    results = []
    for neighbor in G.neighbors(time_node):
        node_data = G.nodes[neighbor]
        if node_data.get("node_type") == "item":
            edge_data = G.edges[neighbor, time_node]
            results.append({
                "item_id": neighbor,
                "name": node_data.get("name"),
                "category": node_data.get("category"),
                "score": edge_data.get("weight", 0.5),
            })
    return sorted(results, key=lambda x: x["score"], reverse=True)
