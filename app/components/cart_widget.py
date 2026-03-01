"""Streamlit component for building the cart."""

import streamlit as st
import json
from pathlib import Path
from typing import List, Dict, Any


@st.cache_data
def load_menu() -> List[Dict]:
    """Load menu items from JSON."""
    menu_path = Path(__file__).parent.parent.parent / "data" / "raw" / "menu_items.json"
    with open(menu_path) as f:
        return json.load(f)


def render_cart_widget() -> List[Dict[str, Any]]:
    """
    Render a cart builder widget.
    
    Returns:
        List of selected cart item dicts.
    """
    menu = load_menu()
    
    # Group items by category for display
    categories = ["main_course", "side", "beverage", "dessert", "appetizer"]
    cat_labels = {
        "main_course": "🍛 Main Course",
        "side": "🍞 Sides",
        "beverage": "🥤 Beverages",
        "dessert": "🍮 Desserts",
        "appetizer": "🥗 Appetizers",
    }
    
    st.markdown("### 🛒 Build Your Cart")
    st.markdown("Select items to add to your cart:")
    
    # Select restaurant type
    restaurant_type = st.selectbox(
        "Restaurant Type",
        ["QSR", "Casual Dining", "Fine Dining", "Cloud Kitchen", "Cafe"],
        key="restaurant_type",
    )
    
    selected_items = []
    
    # Quick demo scenarios
    st.markdown("**Quick Scenarios:**")
    col1, col2, col3, col4 = st.columns(4)
    
    scenario_items = {
        "Scenario 1\n(Biryani Solo)": ["Chicken Biryani"],
        "Scenario 2\n(Group Order)": ["Veg Burger", "Chicken Burger", "Paneer Butter Masala", "Veg Hakka Noodles"],
        "Scenario 3\n(ETA Savior)": ["Maggi"],
        "Scenario 4\n(Pizza Context)": ["Margherita Pizza"],
    }
    
    cols = [col1, col2, col3, col4]
    for i, (label, items) in enumerate(scenario_items.items()):
        if cols[i].button(label, key=f"scenario_{i}"):
            st.session_state["selected_item_names"] = items
    
    # Multi-select for cart items
    all_main_course = [m for m in menu if m["category"] == "main_course"]
    item_options = {m["name"]: m for m in menu}
    main_names = [m["name"] for m in all_main_course]
    
    # Filter options
    show_veg_only = st.checkbox("Show Veg Only", key="veg_filter")
    if show_veg_only:
        display_names = [m["name"] for m in menu if m["is_veg"] and m["category"] == "main_course"]
    else:
        display_names = main_names
    
    default_selection = st.session_state.get("selected_item_names", ["Chicken Biryani"])
    # Filter defaults to valid options
    valid_defaults = [d for d in default_selection if d in display_names]
    if not valid_defaults:
        valid_defaults = [display_names[0]] if display_names else []
    
    selected_names = st.multiselect(
        "Select Main Course Items",
        options=display_names,
        default=valid_defaults,
        key="cart_items",
    )
    
    for name in selected_names:
        if name in item_options:
            selected_items.append(item_options[name])
    
    # Show cart summary
    if selected_items:
        total = sum(item["price"] for item in selected_items)
        max_kpt = max(item["kpt_minutes"] for item in selected_items)
        st.markdown(f"**Cart Total:** ₹{total} | **Items:** {len(selected_items)} | **Max KPT:** {max_kpt} min")
    
    return selected_items, restaurant_type
