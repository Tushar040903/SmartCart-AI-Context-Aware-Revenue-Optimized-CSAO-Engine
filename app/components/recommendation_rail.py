"""Streamlit component showing the CSAO recommendation rail."""

import streamlit as st
from typing import List, Dict, Any


def render_recommendation_rail(
    recommendations: List[Dict[str, Any]],
    order_type: str,
    cart_total: float,
):
    """
    Render the add-on recommendation rail with item cards.
    
    Args:
        recommendations: list of recommended add-on dicts.
        order_type: 'solo' or 'group'.
        cart_total: current cart total in INR.
    """
    order_badge = "👥 GROUP ORDER" if order_type == "group" else "👤 SOLO ORDER"
    
    st.markdown(f"### 🎯 Recommended Add-Ons  `{order_badge}`")
    
    if not recommendations:
        st.info("No add-ons recommended for this cart. Try adding a main course item!")
        return
    
    cols = st.columns(len(recommendations))
    
    for i, rec in enumerate(recommendations):
        with cols[i]:
            # Card styling
            price = rec.get("price", 0)
            name = rec.get("name", "Unknown")
            category = rec.get("category", "")
            kpt = rec.get("kpt_minutes", 0)
            prob = rec.get("conversion_prob", 0)
            score = rec.get("rank_score", 0)
            reason = rec.get("reason", "")
            
            # Category icon
            cat_icons = {
                "side": "🍞",
                "beverage": "🥤",
                "dessert": "🍮",
                "appetizer": "🥗",
                "main_course": "🍛",
            }
            icon = cat_icons.get(category, "🍽️")
            
            # Price as % of cart
            pct = (price / cart_total * 100) if cart_total > 0 else 0
            
            st.markdown(f"""
            <div style="border: 2px solid #ff6b35; border-radius: 10px; padding: 12px; 
                        text-align: center; background: #fff9f5; margin: 4px;">
                <div style="font-size: 2em;">{icon}</div>
                <div style="font-weight: bold; font-size: 1.1em; color: #333;">{name}</div>
                <div style="color: #ff6b35; font-size: 1.3em; font-weight: bold;">₹{price}</div>
                <div style="color: #888; font-size: 0.85em;">{pct:.0f}% of cart</div>
                <div style="color: #28a745; font-size: 0.8em;">✅ KPT: {kpt} min</div>
                <div style="color: #666; font-size: 0.8em;">Conv: {prob:.0%}</div>
                <div style="color: #555; font-size: 0.75em; font-style: italic; margin-top: 4px;">{reason[:50] + '...' if len(reason) > 50 else reason}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add to cart button
            if st.button(f"➕ Add {name}", key=f"add_{i}_{name}"):
                st.success(f"Added {name} to cart!")
