"""Streamlit component showing backend decision logs."""

import streamlit as st
from typing import Dict, List, Any


def render_backend_logs(
    suppression_log: Dict[str, List],
    cart_context: Dict[str, Any],
    temporal_context: Dict[str, Any],
    order_type: str,
):
    """
    Render backend decision logs showing why items were selected or suppressed.
    
    Args:
        suppression_log: dict with 'kpt', 'dietary', 'price', 'diversity' lists.
        cart_context: cart analysis results.
        temporal_context: time/weather context.
        order_type: 'solo' or 'group'.
    """
    st.markdown("### 🔍 Backend Decision Logs")
    
    with st.expander("📊 Cart Context Analysis", expanded=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Cart Total", f"₹{cart_context.get('cart_total', 0)}")
        col2.metric("Items in Cart", cart_context.get("item_count", 0))
        col3.metric("Max KPT", f"{cart_context.get('max_kpt', 0)} min")
        
        col4, col5, col6 = st.columns(3)
        col4.metric("Dominant Cuisine", cart_context.get("dominant_cuisine", "N/A"))
        col5.metric("Order Type", order_type.upper())
        col6.metric("Meal Period", temporal_context.get("meal_period", "N/A"))
    
    # KPT Guardrail Logs (most important)
    kpt_blocked = suppression_log.get("kpt", [])
    if kpt_blocked:
        with st.expander(f"🚫 KPT Guardrail — {len(kpt_blocked)} item(s) BLOCKED (Zero-ETA-Impact)", expanded=True):
            st.markdown("**Zero-ETA-Impact Filter: Blocking items that would delay the order**")
            for item in kpt_blocked:
                st.error(f"❌ **{item['item']}** — {item['reason']}")
    else:
        with st.expander("✅ KPT Guardrail — All items pass"):
            st.success("No items blocked by KPT filter. All recommendations are instant-prep compatible!")
    
    # Dietary Logs
    dietary_blocked = suppression_log.get("dietary", [])
    if dietary_blocked:
        with st.expander(f"🥗 Dietary Filter — {len(dietary_blocked)} item(s) filtered"):
            for item in dietary_blocked:
                name = item.get("name", item.get("item", "Unknown"))
                st.warning(f"🚫 **{name}** — {item.get('reason', 'Dietary mismatch')}")
    
    # Price Guardrail Logs
    price_blocked = suppression_log.get("price", [])
    if price_blocked:
        with st.expander(f"💰 Price Guardrail — {len(price_blocked)} item(s) filtered"):
            for item in price_blocked:
                name = item.get("name", "Unknown")
                st.warning(f"💸 **{name}** — {item.get('reason', 'Price too high')}")
    
    # Weather context
    with st.expander("🌤️ Context Boosts Applied"):
        weather = temporal_context.get("weather", "sunny")
        effects = temporal_context.get("weather_effects", {})
        boosted = effects.get("boosted_items", [])
        
        st.markdown(f"**Weather:** {weather.capitalize()}")
        if boosted:
            st.markdown(f"**Boosted Items:** {', '.join(boosted[:5])}")
        
        meal_period = temporal_context.get("meal_period", "dinner")
        st.markdown(f"**Meal Period:** {meal_period.replace('_', ' ').title()}")
