"""Streamlit component for time/weather/user context toggles."""

import streamlit as st
from typing import Dict, Any


def render_context_panel() -> Dict[str, Any]:
    """
    Render the context panel with time, weather, and user settings.
    
    Returns:
        Dict with hour, weather, is_weekend, is_veg, month.
    """
    st.sidebar.markdown("## ⚙️ Context Settings")
    
    # User preference
    st.sidebar.markdown("### 👤 User Profile")
    is_veg = st.sidebar.checkbox("Vegetarian User", value=False, key="is_veg")
    
    # Time context
    st.sidebar.markdown("### ⏰ Time Context")
    hour = st.sidebar.slider("Hour of Day", 0, 23, 19, key="hour")
    
    # Map hour to meal period for display
    if 6 <= hour < 10:
        meal_period = "🌅 Breakfast"
    elif 11 <= hour < 14:
        meal_period = "☀️ Lunch"
    elif 15 <= hour < 18:
        meal_period = "🕒 Snack"
    elif 18 <= hour < 22:
        meal_period = "🌙 Dinner"
    else:
        meal_period = "🌛 Late Night"
    
    st.sidebar.markdown(f"**Meal Period:** {meal_period}")
    
    is_weekend = st.sidebar.checkbox("Weekend", value=False, key="is_weekend")
    
    # Weather
    st.sidebar.markdown("### 🌤️ Weather")
    weather = st.sidebar.selectbox(
        "Current Weather",
        ["sunny", "rainy", "cold", "hot"],
        key="weather",
    )
    
    weather_emoji = {"sunny": "☀️", "rainy": "🌧️", "cold": "❄️", "hot": "🔥"}
    st.sidebar.markdown(f"**Weather:** {weather_emoji.get(weather, '')} {weather.capitalize()}")
    
    # Month/Season
    st.sidebar.markdown("### 📅 Season")
    month = st.sidebar.slider("Month", 1, 12, 3, key="month")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if month in (3, 4, 5):
        season = "🌞 Summer"
    elif month in (6, 7, 8, 9):
        season = "🌧️ Monsoon"
    elif month in (10, 11):
        season = "🍂 Autumn"
    else:
        season = "❄️ Winter"
    st.sidebar.markdown(f"**Month:** {months[month-1]} — {season}")
    
    return {
        "hour": hour,
        "weather": weather,
        "is_weekend": is_weekend,
        "is_veg": is_veg,
        "month": month,
    }
