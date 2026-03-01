"""SmartCart Engine: the main pipeline chaining all 6 layers."""

import math
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure project root on path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.context_engine.cart_analyzer import CartAnalyzer
from src.context_engine.order_type_classifier import classify_order_type
from src.context_engine.temporal_context import extract_temporal_context
from src.context_engine.user_context import UserContext
from src.candidate_generation.knowledge_graph_recommender import KnowledgeGraphRecommender
from src.ranking.conversion_model import ConversionModel
from src.ranking.revenue_optimizer import calculate_expected_revenue
from src.ranking.multi_objective_ranker import rank_candidates
from src.guardrails.business_constraints import apply_all_guardrails


class SmartCartEngine:
    """
    The main SmartCart AI engine.
    
    Chains all 6 layers:
    1. Context Understanding
    2. Candidate Generation (Knowledge Graph)
    3. Conversion Probability (ML Model)
    4. Revenue-Optimized Ranking
    5. Guardrails & Business Logic
    6. Final Output with Suppression Logs
    """

    def __init__(self):
        self.cart_analyzer = CartAnalyzer()
        self.graph_recommender = KnowledgeGraphRecommender()
        self.conversion_model = ConversionModel()

    def recommend(
        self,
        cart_items: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None,
        hour: int = 19,
        month: int = 3,
        weather: str = "sunny",
        is_weekend: bool = False,
        restaurant_type: str = "QSR",
    ) -> Dict[str, Any]:
        """
        Generate add-on recommendations for the current cart.
        
        Args:
            cart_items: list of item dicts (item_id, name, category, cuisine,
                        price, is_veg, kpt_minutes).
            user_profile: optional dict with 'is_veg', 'avg_spend', etc.
            hour: hour of day (0-23).
            month: month (1-12) for season detection.
            weather: 'sunny', 'rainy', 'cold', or 'hot'.
            is_weekend: whether today is a weekend.
            restaurant_type: type of restaurant.
        
        Returns:
            Dict with keys:
            - 'recommendations': final ranked add-on list
            - 'suppression_log': items blocked and why
            - 'cart_context': extracted cart context
            - 'temporal_context': time/weather context
            - 'order_type': 'solo' or 'group'
        """
        # Layer 1: Context Understanding
        cart_context = self.cart_analyzer.analyze(cart_items)
        order_type = classify_order_type(cart_items)
        temporal_ctx = extract_temporal_context(hour, month, weather, is_weekend)

        user_ctx = UserContext(profile=user_profile) if user_profile else UserContext()

        # Layer 2: Candidate Generation
        candidates = self.graph_recommender.get_candidates(
            cart_item_ids=cart_context["item_ids"],
            context={
                "weather": weather,
                "weather_effects": temporal_ctx["weather_effects"],
                "meal_period": temporal_ctx["meal_period"],
                "is_veg": user_ctx.is_veg,
            },
            max_candidates=50,
        )

        # Layer 3: Conversion Probability
        features_list = []
        for c in candidates:
            cart_total = cart_context["cart_total"]
            addon_price = c.get("price", 0)
            price_ratio = addon_price / cart_total if cart_total > 0 else 0
            ideal_ratio = 0.17
            # Gaussian price fit consistent with multi_objective_ranker (sigma=0.20)
            price_fit = math.exp(-((price_ratio - ideal_ratio) ** 2) / (2 * 0.20 ** 2))

            features_list.append({
                "cart_total": cart_total,
                "cart_item_count": cart_context["item_count"],
                "cuisine_type": self._encode_cuisine(cart_context["dominant_cuisine"]),
                "time_of_day": hour,
                "is_weekend": int(is_weekend),
                "weather": self._encode_weather(weather),
                "addon_price": addon_price,
                "price_ratio": price_ratio,
                "price_fit": price_fit,
                "addon_category": self._encode_category(c.get("category", "side")),
                "order_type": 1 if order_type == "group" else 0,
                "restaurant_type": self._encode_restaurant(restaurant_type),
                "addon_popularity": c.get("popularity_score", 0.5),
                "addon_kpt": c.get("kpt_minutes", 0),
                "cart_max_kpt": cart_context["max_kpt"],
                "kpt_delta": max(0, c.get("kpt_minutes", 0) - cart_context["max_kpt"]),
                "addon_margin": c.get("margin_pct", 0.4),
            })

        probs = self.conversion_model.predict_batch(features_list)

        # Apply weather context boosts to conversion probabilities
        weather_effects = temporal_ctx.get("weather_effects", {})
        boosted_items = set(weather_effects.get("boosted_items", []))
        for i, c in enumerate(candidates):
            if c.get("name") in boosted_items:
                probs[i] = min(0.95, probs[i] * 2.0 + 0.15)

        candidates = calculate_expected_revenue(candidates, probs)

        # Layer 4: Revenue-Optimized Ranking
        candidates = rank_candidates(
            candidates,
            cart_total=cart_context["cart_total"],
            cart_max_kpt=cart_context["max_kpt"],
        )

        # Layer 5: Guardrails
        final_recs, suppression_log = apply_all_guardrails(
            candidates=candidates,
            cart_total=cart_context["cart_total"],
            cart_max_kpt=cart_context["max_kpt"],
            cart_item_count=cart_context["item_count"],
            is_veg=user_ctx.is_veg,
            order_type=order_type,
        )

        return {
            "recommendations": final_recs,
            "suppression_log": suppression_log,
            "cart_context": cart_context,
            "temporal_context": temporal_ctx,
            "order_type": order_type,
        }

    def _encode_cuisine(self, cuisine: str) -> int:
        mapping = {"North Indian": 0, "South Indian": 1, "Chinese": 2,
                   "Italian": 3, "Continental": 4, "Street Food": 5,
                   "Desserts": 6, "Beverages": 7}
        return mapping.get(cuisine, 0)

    def _encode_weather(self, weather: str) -> int:
        return {"sunny": 0, "rainy": 1, "cold": 2, "hot": 3}.get(weather, 0)

    def _encode_category(self, category: str) -> int:
        return {"main_course": 0, "side": 1, "beverage": 2,
                "dessert": 3, "appetizer": 4}.get(category, 1)

    def _encode_restaurant(self, rtype: str) -> int:
        return {"QSR": 0, "Casual Dining": 1, "Fine Dining": 2,
                "Cloud Kitchen": 3, "Cafe": 4}.get(rtype, 0)
