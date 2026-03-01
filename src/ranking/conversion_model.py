"""Conversion Probability Model: XGBoost classifier for add-on conversion prediction."""

import os
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

FEATURE_COLS = [
    "cart_total", "cart_item_count", "cuisine_type", "time_of_day",
    "is_weekend", "weather", "addon_price", "price_ratio", "price_fit",
    "addon_category", "order_type", "restaurant_type",
    "addon_popularity", "addon_kpt", "cart_max_kpt", "kpt_delta", "addon_margin",
]

CUISINE_MAP = {"North Indian": 0, "South Indian": 1, "Chinese": 2,
               "Italian": 3, "Continental": 4, "Street Food": 5,
               "Desserts": 6, "Beverages": 7}
CATEGORY_MAP = {"main_course": 0, "side": 1, "beverage": 2, "dessert": 3, "appetizer": 4}
WEATHER_MAP = {"sunny": 0, "rainy": 1, "cold": 2, "hot": 3}
ORDER_TYPE_MAP = {"solo": 0, "group": 1}
RESTAURANT_TYPE_MAP = {"QSR": 0, "Casual Dining": 1, "Fine Dining": 2,
                       "Cloud Kitchen": 3, "Cafe": 4}


class ConversionModel:
    """Train and serve an XGBoost conversion probability model."""

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or (
            Path(__file__).parent.parent.parent / "models" / "conversion_model.joblib"
        )
        self.model = None
        self._try_load()

    def _try_load(self):
        """Attempt to load a pre-trained model."""
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)

    def train(self, training_data_path: Optional[Path] = None) -> Dict[str, float]:
        """
        Train the XGBoost model on training data.
        
        Returns dict with train/val metrics.
        """
        if training_data_path is None:
            training_data_path = (
                Path(__file__).parent.parent.parent
                / "data" / "synthetic" / "training_data.csv"
            )

        df = pd.read_csv(training_data_path)

        # Ensure all feature columns exist
        for col in FEATURE_COLS:
            if col not in df.columns:
                df[col] = 0

        X = df[FEATURE_COLS].fillna(0)
        y = df["target"]

        from sklearn.model_selection import train_test_split
        from sklearn.metrics import roc_auc_score, accuracy_score

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        if HAS_XGBOOST:
            self.model = XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                eval_metric="logloss",
                random_state=42,
                n_jobs=-1,
            )
        else:
            from sklearn.ensemble import GradientBoostingClassifier
            self.model = GradientBoostingClassifier(
                n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42
            )

        self.model.fit(X_train, y_train)

        val_preds = self.model.predict(X_val)
        val_proba = self.model.predict_proba(X_val)[:, 1]
        metrics = {
            "val_accuracy": float(accuracy_score(y_val, val_preds)),
            "val_auc": float(roc_auc_score(y_val, val_proba)),
        }

        os.makedirs(self.model_path.parent, exist_ok=True)
        joblib.dump(self.model, self.model_path)
        print(f"Model saved to {self.model_path}")
        print(f"Val AUC: {metrics['val_auc']:.4f}, Val Accuracy: {metrics['val_accuracy']:.4f}")
        return metrics

    def predict(self, features: Dict[str, Any]) -> float:
        """
        Predict conversion probability for a single add-on.
        
        Args:
            features: dict with all FEATURE_COLS keys.
        
        Returns:
            float probability 0.0-1.0
        """
        if self.model is None:
            # Fallback: heuristic-based probability
            return self._heuristic_probability(features)

        row = [features.get(col, 0) for col in FEATURE_COLS]
        X = pd.DataFrame([row], columns=FEATURE_COLS)
        prob = float(self.model.predict_proba(X)[0][1])
        return prob

    def predict_batch(self, features_list: List[Dict[str, Any]]) -> List[float]:
        """Predict conversion probabilities for a list of add-ons."""
        if self.model is None:
            return [self._heuristic_probability(f) for f in features_list]

        rows = [[f.get(col, 0) for col in FEATURE_COLS] for f in features_list]
        X = pd.DataFrame(rows, columns=FEATURE_COLS)
        return [float(p) for p in self.model.predict_proba(X)[:, 1]]

    def _heuristic_probability(self, features: Dict[str, Any]) -> float:
        """Fallback heuristic when model is not available."""
        score = 0.3
        price_ratio = features.get("price_ratio", 0.2)
        if 0.05 <= price_ratio <= 0.25:
            score += 0.2
        score += features.get("addon_popularity", 0.5) * 0.2
        if features.get("kpt_delta", 0) == 0:
            score += 0.1
        return min(0.95, max(0.05, score))
