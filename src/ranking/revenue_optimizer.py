"""Revenue Optimizer: calculates expected revenue lift for add-on candidates."""

from typing import List, Dict, Any


def calculate_expected_revenue(
    candidates: List[Dict[str, Any]],
    conversion_probs: List[float],
) -> List[Dict[str, Any]]:
    """
    Calculate expected revenue lift for each candidate.
    
    Expected Revenue = P(conversion) × Price × Margin
    
    Args:
        candidates: list of candidate item dicts with 'price' and 'margin_pct'.
        conversion_probs: list of conversion probabilities (same order as candidates).
    
    Returns:
        Candidates with 'expected_revenue' and 'conversion_prob' fields added.
    """
    result = []
    for candidate, prob in zip(candidates, conversion_probs):
        price = candidate.get("price", 0)
        margin = candidate.get("margin_pct", 0.4)
        expected_rev = prob * price * margin
        result.append({
            **candidate,
            "conversion_prob": round(prob, 4),
            "expected_revenue": round(expected_rev, 2),
        })
    return result


def rank_by_revenue(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort candidates by expected revenue descending."""
    return sorted(candidates, key=lambda x: x.get("expected_revenue", 0), reverse=True)
