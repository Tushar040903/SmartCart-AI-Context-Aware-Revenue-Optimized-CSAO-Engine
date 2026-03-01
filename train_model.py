#!/usr/bin/env python3
"""
SmartCart AI — Model Training Script

Run with: python train_model.py

This script:
1. Generates synthetic user profiles (if not present)
2. Generates synthetic orders (if not present)
3. Generates training data from orders (if not present)
4. Trains the XGBoost conversion model
5. Saves the model to models/conversion_model.joblib
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    print("=" * 60)
    print("SmartCart AI — Model Training Pipeline")
    print("=" * 60)

    # Step 1: Generate user profiles
    profiles_path = project_root / "data" / "synthetic" / "user_profiles.json"
    if not profiles_path.exists():
        print("\n[1/5] Generating user profiles...")
        from data.synthetic.generate_user_profiles import generate_user_profiles
        generate_user_profiles()
    else:
        print(f"\n[1/5] User profiles already exist at {profiles_path}")

    # Step 2: Generate orders
    orders_path = project_root / "data" / "synthetic" / "orders.json"
    if not orders_path.exists():
        print("\n[2/5] Generating synthetic orders...")
        from data.synthetic.generate_orders import generate_orders
        generate_orders()
    else:
        print(f"\n[2/5] Orders already exist at {orders_path}")

    # Step 3: Generate training data
    training_path = project_root / "data" / "synthetic" / "training_data.csv"
    if not training_path.exists():
        print("\n[3/5] Generating training data...")
        from data.synthetic.generate_training_data import generate_training_data
        generate_training_data()
    else:
        print(f"\n[3/5] Training data already exists at {training_path}")

    # Step 4: Build knowledge graph
    graph_path = project_root / "data" / "knowledge_graph" / "food_graph.pkl"
    if not graph_path.exists():
        print("\n[4/5] Building food knowledge graph...")
        from data.knowledge_graph.build_graph import build_food_knowledge_graph
        build_food_knowledge_graph()
    else:
        print(f"\n[4/5] Knowledge graph already exists at {graph_path}")

    # Step 5: Train model
    print("\n[5/5] Training conversion model...")
    from src.ranking.conversion_model import ConversionModel
    model = ConversionModel()
    metrics = model.train(training_data_path=training_path)

    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"  Validation AUC:      {metrics.get('val_auc', 0):.4f}")
    print(f"  Validation Accuracy: {metrics.get('val_accuracy', 0):.4f}")
    print("=" * 60)
    print(f"\nModel saved to: {project_root / 'models' / 'conversion_model.joblib'}")


if __name__ == "__main__":
    main()
