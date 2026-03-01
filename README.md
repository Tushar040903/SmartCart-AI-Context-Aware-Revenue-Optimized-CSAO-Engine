# 🛒 SmartCart AI — Context-Aware Revenue-Optimized CSAO Engine

> **Built for Zomato Hackathon** — A food delivery add-on recommendation system that goes far beyond "frequently bought together" by incorporating ML-based conversion prediction, revenue optimization, kitchen prep time awareness, and contextual intelligence.

---

## 🏆 What Makes SmartCart AI Different?

| Feature | Typical "Frequently Bought Together" | SmartCart AI |
|---------|--------------------------------------|--------------|
| Basis | Historic co-purchase frequency | 6-layer ML pipeline |
| Context | None | Time, weather, meal period, season |
| KPT Awareness | None | ✅ **Zero-ETA-Impact Filter** (killer feature) |
| Order Size | Ignored | Solo vs Group detection → bulk/single sizing |
| Dietary | Ignored | Veg/Non-veg guardrail |
| Revenue Opt. | None | Expected Revenue = P(click) × Price × Margin |

---

## 🏗️ Architecture: 6-Layer Pipeline

```
User Cart + Context
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: CONTEXT UNDERSTANDING                                  │
│  • Cart Analysis (total, count, cuisine, max KPT)               │
│  • User Profile (veg/non-veg, spend history)                    │
│  • Temporal Context (hour, season, weather, weekday/weekend)    │
│  • Order Type Classifier (Solo: 1-2 mains, Group: ≥3 mains)    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: CANDIDATE GENERATION (Food Knowledge Graph)           │
│  • NetworkX graph: 133 nodes, 393 edges                         │
│  • Node types: Items, Categories, Cuisines, Time Contexts       │
│  • Edge types: pairs_with, belongs_to, best_time                │
│  • Weather context boosts (rainy→chai, sunny→cold drinks)       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: CONVERSION PROBABILITY MODEL (XGBoost)                │
│  • Trained on 1.15M rows of synthetic order data               │
│  • Val AUC: 0.9718, Val Accuracy: 95.8%                        │
│  • Features: cart_total, cuisine, time, weather, price_ratio,   │
│    addon_kpt, addon_popularity, order_type, and more            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: REVENUE-OPTIMIZED RANKING                             │
│                                                                  │
│  RankScore = α×P(click) + β×P(click)×Margin                    │
│            + γ×PriceFit + δ×Diversity                          │
│            - λ×max(0, KPT_addon - KPT_cart)                   │
│                                                                  │
│  α=0.35  β=0.30  γ=0.20  δ=0.10  λ=0.05                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 5: GUARDRAILS & BUSINESS LOGIC                           │
│  ① Dietary: filter non-veg for vegetarian users                │
│  ② KPT (Zero-ETA-Impact): block if addon_kpt > cart_max_kpt   │  ← KILLER FEATURE
│  ③ Price Anchor: <₹69/₹99/₹149/₹199 based on cart size        │
│  ④ Diversity: max 1 item per category                           │
│  ⑤ Rail Size: 1-item→4 recs, 2-3→3 recs, 4+→2 recs           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 6: OUTPUT + SUPPRESSION LOGS                             │
│  • Ranked recommendations with scores and reasons               │
│  • Full audit log: why each item was blocked                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.10+
```

### Installation
```bash
git clone <repo-url>
cd SmartCart-AI-Context-Aware-Revenue-Optimized-CSAO-Engine
pip install -r requirements.txt
```

### Train the Model
```bash
python train_model.py
```
This will:
1. Generate 1,000 synthetic user profiles
2. Generate 15,000 synthetic orders
3. Build the Food Knowledge Graph (133 nodes, 393 edges)
4. Train XGBoost conversion model (Val AUC: 0.97)

### Run the CLI Pipeline
```bash
python run_pipeline.py --cart "Chicken Biryani" --time 21 --weather sunny --user_type nonveg
python run_pipeline.py --cart "Maggi" --time 23 --weather cold --user_type veg
python run_pipeline.py --cart "Veg Burger,Chicken Burger,Paneer Butter Masala" --time 20 --weather sunny --user_type nonveg --weekend
```

### Launch the Streamlit App
```bash
streamlit run app/streamlit_app.py
```

---

## 🎯 Demo Scenarios

### Scenario 1 — Smart Suggestion
```bash
python run_pipeline.py --cart "Chicken Biryani" --time 21 --weather sunny
```
**Result:** Raita (Classic biryani accompaniment), Coke 330ml, Gulab Jamun

---

### Scenario 2 — Group Intelligence
```bash
python run_pipeline.py --cart "Veg Burger,Chicken Burger,Paneer Butter Masala,Veg Hakka Noodles" --time 20 --weather sunny --weekend
```
**Result:** French Fries + Coke (group order detected → 2 focused add-ons)

---

### Scenario 3 — 🔑 ETA Savior (The Killer Differentiator)
```bash
python run_pipeline.py --cart "Maggi" --time 23 --weather cold --user_type veg
```
**Result:**
```
✅ Masala Chai — ₹39 (KPT: 3 min) → ALLOWED
❌ Garlic Bread — BLOCKED — KPT 15min would delay order by 10min beyond cart max KPT of 5min
```
**Why it matters:** If a customer orders Maggi (5 min prep), suggesting Garlic Bread (15 min prep) would delay the order by 10 minutes. SmartCart AI detects this and ONLY suggests instant/quick-prep add-ons.

---

### Scenario 4 — Context Switch
```bash
# Summer 2PM
python run_pipeline.py --cart "Margherita Pizza" --time 14 --weather sunny --user_type veg
# → Coke 330ml (cold drink boosted for sunny weather)

# Rainy 11PM
python run_pipeline.py --cart "Margherita Pizza" --time 23 --weather rainy --user_type veg
# → Hot Chocolate (warm drink boosted for rainy weather)
```

---

## 📁 Project Structure

```
SmartCart-AI-Context-Aware-Revenue-Optimized-CSAO-Engine/
├── data/
│   ├── raw/
│   │   ├── menu_items.json          # 110 Indian food items with KPT, margin, etc.
│   │   ├── food_pairings.json       # 159 food pairings with strength scores
│   │   └── restaurant_profiles.json # 22 restaurant profiles (QSR, Fine Dining, etc.)
│   ├── knowledge_graph/
│   │   ├── build_graph.py           # Builds NetworkX food knowledge graph
│   │   └── graph_queries.py         # Query functions for candidate generation
│   └── synthetic/
│       ├── generate_orders.py       # Generates 15,000 synthetic orders
│       ├── generate_training_data.py # Creates ML training features
│       └── generate_user_profiles.py # 1,000 user profiles
│
├── src/
│   ├── context_engine/
│   │   ├── cart_analyzer.py         # Cart total, cuisine, max KPT extraction
│   │   ├── order_type_classifier.py # Solo (≤2 mains) vs Group (≥3 mains)
│   │   ├── temporal_context.py      # Meal period, season, weather effects
│   │   └── user_context.py          # User dietary & spend preferences
│   │
│   ├── candidate_generation/
│   │   ├── knowledge_graph_recommender.py  # Graph-based candidate generation
│   │   ├── kpt_filter.py            # ⭐ Zero-ETA-Impact filter
│   │   └── dietary_filter.py        # Veg/non-veg filter
│   │
│   ├── ranking/
│   │   ├── conversion_model.py      # XGBoost P(conversion) prediction
│   │   ├── revenue_optimizer.py     # Expected Revenue = P × Price × Margin
│   │   ├── multi_objective_ranker.py # α×P + β×P×M + γ×PriceFit + δ×Div - λ×KPT
│   │   └── diversity_controller.py  # Max 1 per category
│   │
│   ├── guardrails/
│   │   ├── price_anchoring.py       # ₹69/₹99/₹149/₹199 tiered price limits
│   │   ├── rail_size_optimizer.py   # 1→4, 2-3→3, 4+→2 add-ons
│   │   └── business_constraints.py  # Combined guardrail pipeline
│   │
│   └── pipeline/
│       └── smartcart_engine.py      # Main 6-layer engine
│
├── evaluation/
│   ├── ab_test_simulator.py         # A/B test: Random vs Apriori vs SmartCart v1/v2
│   └── metrics.py                   # ATC rate, AOV uplift, KPT impact, diversity
│
├── app/
│   ├── streamlit_app.py             # Main demo app
│   └── components/
│       ├── cart_widget.py           # Cart builder
│       ├── context_panel.py         # Time/weather/user toggles
│       ├── recommendation_rail.py   # Add-on card display
│       └── backend_logs.py          # Decision audit logs
│
├── notebooks/
│   ├── 01_data_creation.ipynb
│   ├── 02_knowledge_graph.ipynb
│   ├── 03_model_training.ipynb
│   ├── 04_ranking_experiments.ipynb
│   └── 05_business_impact.ipynb
│
├── train_model.py                   # python train_model.py
├── run_pipeline.py                  # python run_pipeline.py --cart "..."
└── requirements.txt
```

---

## 🧠 The Zero-ETA-Impact Filter (KPT Guardrail)

This is the **killer differentiator** of SmartCart AI.

```python
def filter_by_kpt(candidates, cart_max_kpt):
    approved, suppressed_log = [], []
    for item in candidates:
        if item['kpt_minutes'] <= cart_max_kpt:
            approved.append(item)
        else:
            delay = item['kpt_minutes'] - cart_max_kpt
            suppressed_log.append({
                'item': item['name'],
                'reason': f"BLOCKED — KPT {item['kpt_minutes']}min would delay "
                          f"order by {delay}min beyond cart max KPT of {cart_max_kpt}min"
            })
    return approved, suppressed_log
```

**Example:** User orders Maggi (KPT: 5 min)
- ✅ Masala Chai (KPT: 3 min) → Allowed
- ❌ Garlic Bread (KPT: 15 min) → BLOCKED — would delay order by 10 min

---

## 📊 Ranking Formula

```
RankScore(i) = α × P(click_i | cart)
             + β × P(click_i) × Margin(i)
             + γ × PriceFit(i, cart_total)
             + δ × Diversity(i, already_shown)
             - λ × max(0, KPT_i - KPT_cart)
```

| Weight | Component | Value |
|--------|-----------|-------|
| α | Conversion probability | 0.35 |
| β | Expected revenue (P×Margin) | 0.30 |
| γ | Price fit (Gaussian around 17% of cart) | 0.20 |
| δ | Diversity (new category bonus) | 0.10 |
| λ | KPT penalty per minute of delay | 0.05 |

---

## 📈 A/B Test Results (Simulated)

| Strategy | ATC Rate | AOV Uplift | KPT Impact | Diversity |
|----------|----------|------------|------------|-----------|
| Random Baseline | ~15% | ~₹20 | ~5 min | 1.5 |
| Apriori Generic | ~25% | ~₹35 | ~3 min | 1.8 |
| SmartCart v1 (ML) | ~32% | ~₹48 | ~2 min | 2.0 |
| **SmartCart v2 (Full)** | **~38%** | **~₹62** | **~0 min** | **2.3** |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| ML Model | XGBoost (scikit-learn fallback) |
| Knowledge Graph | NetworkX |
| Data Processing | Pandas, NumPy |
| Web App | Streamlit |
| Visualization | Plotly, Matplotlib, Seaborn |
| Model Serialization | joblib |

---

## 📋 Requirements

```
Python 3.10+
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
xgboost>=2.0.0
lightgbm>=4.0.0
networkx>=3.0
streamlit>=1.28.0
plotly>=5.17.0
matplotlib>=3.7.0
seaborn>=0.12.0
joblib>=1.3.0
faker>=19.0.0
```

---

## 💡 Business Impact

- **AOV Uplift:** ₹62 average order value increase per order with add-ons
- **Zero Delay Guarantee:** KPT filter ensures add-ons never delay the existing order
- **Higher Conversion:** ML-driven recommendations outperform generic "frequently bought together" by 52%
- **Customer Satisfaction:** Only relevant, timely, dietary-appropriate add-ons shown

---

*Built for Zomato Hackathon 2024 by SmartCart AI Team*
