"""Metrics calculation for SmartCart AI evaluation."""

from typing import List, Dict, Any
import numpy as np


def add_to_cart_rate(sessions: List[Dict]) -> float:
    """Calculate the fraction of sessions where an add-on was added."""
    if not sessions:
        return 0.0
    added = sum(1 for s in sessions if s.get("addon_added", False))
    return added / len(sessions)


def aov_uplift(sessions: List[Dict]) -> float:
    """Calculate average order value uplift from add-ons in INR."""
    if not sessions:
        return 0.0
    uplifts = [s.get("addon_value", 0) for s in sessions if s.get("addon_added", False)]
    return float(np.mean(uplifts)) if uplifts else 0.0


def kpt_impact_score(sessions: List[Dict]) -> float:
    """
    Calculate average KPT delay introduced by recommended add-ons (minutes).
    Lower is better. Zero means Zero-ETA-Impact.
    """
    if not sessions:
        return 0.0
    delays = [s.get("kpt_delay", 0) for s in sessions]
    return float(np.mean(delays))


def diversity_score(sessions: List[Dict]) -> float:
    """
    Calculate average number of unique categories in recommendations.
    Higher is better.
    """
    if not sessions:
        return 0.0
    diversities = []
    for s in sessions:
        recs = s.get("recommendations", [])
        if recs:
            cats = set(r.get("category", "") for r in recs)
            diversities.append(len(cats))
    return float(np.mean(diversities)) if diversities else 0.0


def revenue_per_order(sessions: List[Dict]) -> float:
    """Calculate average revenue per order from add-ons."""
    if not sessions:
        return 0.0
    revenues = [s.get("addon_revenue", 0) for s in sessions]
    return float(np.mean(revenues))


def compute_all_metrics(sessions: List[Dict]) -> Dict[str, float]:
    """Compute all evaluation metrics for a set of sessions."""
    return {
        "add_to_cart_rate": round(add_to_cart_rate(sessions), 4),
        "aov_uplift_inr": round(aov_uplift(sessions), 2),
        "kpt_impact_minutes": round(kpt_impact_score(sessions), 2),
        "diversity_score": round(diversity_score(sessions), 2),
        "revenue_per_order": round(revenue_per_order(sessions), 2),
    }
