"""
SmartCart AI — Context-Aware Revenue-Optimized CSAO Engine
Streamlit Demo App

Run with: streamlit run app/streamlit_app.py
"""

import sys
import json
import streamlit as st
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.components.cart_widget import render_cart_widget, load_menu
from app.components.context_panel import render_context_panel
from app.components.recommendation_rail import render_recommendation_rail
from app.components.backend_logs import render_backend_logs


# Page configuration
st.set_page_config(
    page_title="SmartCart AI — CSAO Engine",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #ff6b35, #f7c948);
        border-radius: 10px;
        margin-bottom: 1rem;
        color: white;
    }
    .metric-card {
        background: white;
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .stButton button {
        background-color: #ff6b35;
        color: white;
        border: none;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_engine():
    """Load the SmartCart engine (cached for performance)."""
    from src.pipeline.smartcart_engine import SmartCartEngine
    return SmartCartEngine()


def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🛒 SmartCart AI</h1>
        <p>Context-Aware Revenue-Optimized CSAO Engine</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar context panel
    context = render_context_panel()
    
    # Main content area
    col_cart, col_recs = st.columns([1, 2])
    
    with col_cart:
        result = render_cart_widget()
        cart_items, restaurant_type = result if isinstance(result, tuple) else (result, "QSR")
    
    # Run engine whenever cart or context changes
    with col_recs:
        if cart_items:
            with st.spinner("🤖 SmartCart AI analyzing your cart..."):
                try:
                    engine = get_engine()
                    user_profile = {
                        "is_veg": context["is_veg"],
                        "avg_spend": 400,
                        "user_id": "demo_user",
                    }
                    
                    recommendation_result = engine.recommend(
                        cart_items=cart_items,
                        user_profile=user_profile,
                        hour=context["hour"],
                        month=context["month"],
                        weather=context["weather"],
                        is_weekend=context["is_weekend"],
                        restaurant_type=restaurant_type,
                    )
                    
                    # Recommendation Rail
                    render_recommendation_rail(
                        recommendations=recommendation_result["recommendations"],
                        order_type=recommendation_result["order_type"],
                        cart_total=recommendation_result["cart_context"]["cart_total"],
                    )
                    
                    # Metrics Dashboard
                    st.markdown("---")
                    st.markdown("### 📊 Live Metrics")
                    
                    recs = recommendation_result["recommendations"]
                    cart_total = recommendation_result["cart_context"]["cart_total"]
                    
                    m1, m2, m3, m4 = st.columns(4)
                    
                    potential_uplift = sum(r.get("price", 0) for r in recs)
                    avg_prob = sum(r.get("conversion_prob", 0) for r in recs) / len(recs) if recs else 0
                    kpt_impact = max(
                        (max(0, r.get("kpt_minutes", 0) - recommendation_result["cart_context"]["max_kpt"])
                         for r in recs),
                        default=0,
                    )
                    diversity = len(set(r.get("category", "") for r in recs))
                    
                    m1.metric("Potential AOV Uplift", f"₹{potential_uplift}")
                    m2.metric("Avg Conv. Probability", f"{avg_prob:.0%}")
                    m3.metric("KPT Impact", f"{kpt_impact} min", 
                              delta="✅ Zero Impact" if kpt_impact == 0 else f"+{kpt_impact}min delay",
                              delta_color="normal" if kpt_impact == 0 else "inverse")
                    m4.metric("Category Diversity", f"{diversity} categories")
                    
                    # Suppression stats
                    supp = recommendation_result["suppression_log"]
                    total_blocked = sum(len(v) for v in supp.values())
                    if total_blocked > 0:
                        st.info(f"ℹ️ {total_blocked} item(s) were filtered by guardrails — see Backend Logs below.")
                    
                except Exception as e:
                    st.error(f"Engine error: {e}")
                    st.exception(e)
                    recommendation_result = {
                        "recommendations": [],
                        "suppression_log": {"kpt": [], "dietary": [], "price": [], "diversity": []},
                        "cart_context": {"cart_total": 0, "item_count": 0, "dominant_cuisine": "N/A",
                                         "max_kpt": 0, "is_all_veg": True},
                        "temporal_context": {"meal_period": "dinner", "weather": "sunny",
                                             "weather_effects": {}, "is_weekend": False},
                        "order_type": "solo",
                    }
        else:
            st.info("👆 Add items to your cart to get personalized add-on recommendations!")
            recommendation_result = {
                "recommendations": [],
                "suppression_log": {"kpt": [], "dietary": [], "price": [], "diversity": []},
                "cart_context": {"cart_total": 0, "item_count": 0, "dominant_cuisine": "N/A",
                                 "max_kpt": 0, "is_all_veg": True},
                "temporal_context": {"meal_period": "dinner", "weather": "sunny",
                                     "weather_effects": {}, "is_weekend": False},
                "order_type": "solo",
            }
    
    # Backend Logs (full width)
    if cart_items:
        st.markdown("---")
        render_backend_logs(
            suppression_log=recommendation_result["suppression_log"],
            cart_context=recommendation_result["cart_context"],
            temporal_context=recommendation_result["temporal_context"],
            order_type=recommendation_result["order_type"],
        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.9em;">
        🛒 SmartCart AI — Built for Zomato Hackathon | 
        6-Layer Pipeline: Context → Graph → ML → Revenue Optimizer → Guardrails → Output
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
