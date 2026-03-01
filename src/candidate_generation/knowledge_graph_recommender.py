"""Knowledge Graph Recommender: generates candidate add-ons from the food graph."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from data.knowledge_graph.build_graph import build_food_knowledge_graph
from data.knowledge_graph.graph_queries import (
    load_graph,
    get_candidate_addons,
    get_items_by_context,
)


class KnowledgeGraphRecommender:
    """Uses the food knowledge graph to generate candidate add-ons."""

    def __init__(self, graph_path: Optional[Path] = None):
        """Load or build the graph."""
        if graph_path is None:
            graph_path = (
                Path(__file__).parent.parent.parent
                / "data" / "knowledge_graph" / "food_graph.pkl"
            )
        self.graph_path = graph_path
        self._load_or_build()

    def _load_or_build(self):
        """Load the graph if it exists; otherwise build and save it."""
        if self.graph_path.exists():
            self.G = load_graph(self.graph_path)
        else:
            self.G = build_food_knowledge_graph(output_path=self.graph_path)

    def get_candidates(
        self,
        cart_item_ids: List[str],
        context: Optional[Dict[str, Any]] = None,
        max_candidates: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get candidate add-ons for the current cart.
        
        Args:
            cart_item_ids: list of item_id strings currently in cart.
            context: optional dict with 'weather', 'meal_period', 'is_veg' keys.
            max_candidates: max number of candidates to return.
        
        Returns:
            List of candidate dicts with item details and pairing score.
        """
        candidates = get_candidate_addons(self.G, cart_item_ids, max_candidates)
        
        # Apply context boosts
        if context:
            weather = context.get("weather", "sunny")
            weather_effects = context.get("weather_effects", {})
            boosted_items = weather_effects.get("boosted_items", [])
            
            for c in candidates:
                if c["name"] in boosted_items:
                    c["score"] = min(1.0, c["score"] + 0.15)
                    c["context_boosted"] = True
        
        # Sort by score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:max_candidates]
