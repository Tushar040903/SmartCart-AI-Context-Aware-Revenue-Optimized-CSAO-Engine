"""Temporal Context: extracts meal period, season, and weather effects."""

from typing import Dict, Any


MEAL_PERIODS = {
    "breakfast": (6, 10),
    "lunch": (11, 14),
    "snack": (15, 17),
    "dinner": (18, 22),
    "late_night": (22, 6),  # wraps around midnight
}


def get_meal_period(hour: int) -> str:
    """Map hour (0-23) to a meal period string."""
    for period, (start, end) in MEAL_PERIODS.items():
        if start <= end:
            if start <= hour < end:
                return period
        else:
            # wraps midnight
            if hour >= start or hour < end:
                return period
    return "dinner"


def get_season(month: int) -> str:
    """Map month (1-12) to an Indian season."""
    if month in (3, 4, 5):
        return "summer"
    elif month in (6, 7, 8, 9):
        return "monsoon"
    elif month in (10, 11):
        return "autumn"
    else:  # 12, 1, 2
        return "winter"


def get_weather_effects(weather: str) -> Dict[str, Any]:
    """
    Return a dict of category/item boosts for the given weather.
    
    Args:
        weather: one of 'sunny', 'rainy', 'cold', 'hot'
    
    Returns:
        Dict with boosted_categories and boosted_items lists plus reduction_categories.
    """
    effects = {
        "sunny": {
            "boosted_categories": ["beverage"],
            "boosted_items": ["Coke 330ml", "Mango Lassi", "Fresh Lime Soda",
                              "Watermelon Juice", "Lassi", "Cold Coffee"],
            "reduced_categories": [],
            "hot_drinks_penalty": 0.3,
        },
        "hot": {
            "boosted_categories": ["beverage", "dessert"],
            "boosted_items": ["Coke 330ml", "Mango Lassi", "Ice Cream Cup",
                              "Mango Shake", "Kulfi", "Fresh Lime Soda"],
            "reduced_categories": [],
            "hot_drinks_penalty": 0.4,
        },
        "rainy": {
            "boosted_categories": ["beverage", "appetizer"],
            "boosted_items": ["Masala Chai", "Hot Chocolate", "Veg Soup",
                              "Tomato Soup", "Chicken Soup", "Hot Coffee"],
            "reduced_categories": [],
            "cold_drinks_penalty": 0.3,
        },
        "cold": {
            "boosted_categories": ["beverage", "appetizer"],
            "boosted_items": ["Masala Chai", "Hot Coffee", "Hot Chocolate",
                              "Veg Soup", "Tomato Soup"],
            "reduced_categories": [],
            "cold_drinks_penalty": 0.3,
        },
    }
    return effects.get(weather, {"boosted_categories": [], "boosted_items": [],
                                  "reduced_categories": []})


def extract_temporal_context(hour: int, month: int = 3, weather: str = "sunny",
                              is_weekend: bool = False) -> Dict[str, Any]:
    """
    Extract full temporal context.
    
    Returns:
        Dict with meal_period, season, weather_effects, is_weekend, hour.
    """
    return {
        "hour": hour,
        "meal_period": get_meal_period(hour),
        "season": get_season(month),
        "weather": weather,
        "weather_effects": get_weather_effects(weather),
        "is_weekend": is_weekend,
    }
