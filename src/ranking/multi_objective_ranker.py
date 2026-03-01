"""Multi-Objective Ranker: combines conversion, revenue, price fit, diversity, and KPT."""

import math
from typing import List, Dict, Any


# Standard deviation for the Gaussian price-fit curve; controls acceptable
# variance around the ideal price ratio (±8 percentage points at 1σ).
PRICE_FIT_SIGMA = 0.20

# Default weights for the ranking formula
DEFAULT_WEIGHTS = {
    "alpha": 0.35,   # conversion probability
    "beta": 0.30,    # expected revenue (P × Margin)
    "gamma": 0.20,   # price fit
    "delta": 0.10,   # diversity
    "lambda": 0.05,  # KPT penalty
}


def calculate_price_fit(addon_price: float, cart_total: float) -> float:
    """
    Calculate how well the add-on price fits the cart total.
    Ideal is 15-20% of cart total.
    """
    if cart_total <= 0:
        return 0.0
    ratio = addon_price / cart_total
    ideal = 0.17
    # Gaussian around ideal ratio
    fit = math.exp(-((ratio - ideal) ** 2) / (2 * PRICE_FIT_SIGMA ** 2))
    return fit


def calculate_diversity_score(
    candidate: Dict[str, Any],
    already_shown: List[Dict[str, Any]],
) -> float:
    """
    Compute diversity bonus: higher if this item's category hasn't been shown yet.
    """
    if not already_shown:
        return 1.0
    shown_categories = {item.get("category", "") for item in already_shown}
    if candidate.get("category", "") not in shown_categories:
        return 1.0
    return 0.2


def _temporal_boost(candidate: Dict[str, Any], hour: int, weather: str) -> float:
    """
    Compute a temporal boost/penalty based on time of day and weather.

    Positive values push the item up; negative values push it down.
    """
    boost = 0.0
    name = candidate.get("name", "")

    hot_beverages = {
        "Masala Chai", "Hot Chocolate", "Hot Coffee",
        "Veg Soup", "Tomato Soup", "Chicken Soup",
    }
    cold_beverages = {
        "Cold Coffee", "Mango Lassi", "Fresh Lime Soda", "Coke 330ml",
        "Lassi", "Watermelon Juice", "Lemon Iced Tea", "Mango Shake",
    }

    # Weather-based boosts / penalties
    if weather in ("rainy", "cold"):
        if name in hot_beverages:
            boost += 0.25
        if name in cold_beverages:
            boost -= 0.25
    elif weather in ("sunny", "hot"):
        if name in cold_beverages:
            boost += 0.25
        if name in hot_beverages:
            boost -= 0.25

    # Hour-based boosts / penalties
    if hour >= 22 or hour < 6:  # late night
        comfort_items = {
            "Brownie", "Chocolate Brownie", "Cheese Fries",
            "Cheesy Fries", "French Fries",
        }
        salad_items = {"Green Salad", "Caesar Salad", "Raita", "Cucumber Salad"}
        if name in comfort_items:
            boost += 0.20
        if name in salad_items:
            boost -= 0.20
    elif 11 <= hour < 14:  # lunch
        light_sides = {"Green Salad", "Caesar Salad", "Raita", "Cucumber Salad"}
        heavy_desserts = {
            "Brownie", "Chocolate Brownie", "Gulab Jamun",
            "Ice Cream Cup", "Kulfi",
        }
        if name in light_sides:
            boost += 0.15
        if name in heavy_desserts:
            boost -= 0.10

    return boost


def rank_candidates(
    candidates: List[Dict[str, Any]],
    cart_total: float,
    cart_max_kpt: int,
    weights: Dict[str, float] = None,
    hour: int = 19,
    weather: str = "sunny",
) -> List[Dict[str, Any]]:
    """
    Apply the multi-objective ranking formula:
    
    RankScore(i) = α × P(click_i | cart)
                 + β × P(click_i) × Margin(i)
                 + γ × PriceFit(i, cart_total)
                 + δ × Diversity(i, already_shown)
                 - λ × max(0, KPT_i - KPT_cart)
    
    Args:
        candidates: list of candidate dicts with 'conversion_prob', 'margin_pct',
                    'price', 'kpt_minutes', 'category'.
        cart_total: total value of the current cart.
        cart_max_kpt: maximum KPT in the cart.
        weights: optional override for α, β, γ, δ, λ.
    
    Returns:
        Sorted list of candidates with 'rank_score' field added.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    alpha = weights.get("alpha", 0.35)
    beta = weights.get("beta", 0.30)
    gamma = weights.get("gamma", 0.20)
    delta = weights.get("delta", 0.10)
    lam = weights.get("lambda", 0.05)

    ranked = []
    already_shown = []

    for candidate in candidates:
        prob = candidate.get("conversion_prob", 0.3)
        margin = candidate.get("margin_pct", 0.4)
        price = candidate.get("price", 0)
        kpt = candidate.get("kpt_minutes", 0)
        # Include context/pairing score as additional signal (0.0-1.0)
        context_score = candidate.get("score", 0.5)

        price_fit = calculate_price_fit(price, cart_total)
        diversity = calculate_diversity_score(candidate, already_shown)
        kpt_penalty = max(0, kpt - cart_max_kpt)
        temporal = _temporal_boost(candidate, hour, weather)

        rank_score = (
            alpha * prob
            + beta * prob * margin
            + gamma * price_fit
            + delta * diversity
            - lam * kpt_penalty
            + 0.15 * context_score  # context/pairing score boost
            + temporal               # time/weather boost
        )

        ranked.append({
            **candidate,
            "rank_score": round(rank_score, 4),
            "price_fit": round(price_fit, 4),
            "diversity_score": round(diversity, 4),
        })
        already_shown.append(candidate)

    return sorted(ranked, key=lambda x: x["rank_score"], reverse=True)
