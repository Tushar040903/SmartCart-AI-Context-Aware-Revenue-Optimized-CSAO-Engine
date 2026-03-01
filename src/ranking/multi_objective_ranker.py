"""Multi-Objective Ranker: combines conversion, revenue, price fit, diversity, and KPT."""

import math
from typing import List, Dict, Any


# Standard deviation for the Gaussian price-fit curve; controls acceptable
# variance around the ideal price ratio (±8 percentage points at 1σ).
PRICE_FIT_SIGMA = 0.08

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


def rank_candidates(
    candidates: List[Dict[str, Any]],
    cart_total: float,
    cart_max_kpt: int,
    weights: Dict[str, float] = None,
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

        price_fit = calculate_price_fit(price, cart_total)
        diversity = calculate_diversity_score(candidate, already_shown)
        kpt_penalty = max(0, kpt - cart_max_kpt)

        rank_score = (
            alpha * prob
            + beta * prob * margin
            + gamma * price_fit
            + delta * diversity
            - lam * kpt_penalty
        )

        ranked.append({
            **candidate,
            "rank_score": round(rank_score, 4),
            "price_fit": round(price_fit, 4),
            "diversity_score": round(diversity, 4),
        })
        already_shown.append(candidate)

    return sorted(ranked, key=lambda x: x["rank_score"], reverse=True)
