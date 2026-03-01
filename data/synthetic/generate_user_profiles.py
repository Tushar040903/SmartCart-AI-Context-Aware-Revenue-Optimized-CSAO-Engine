"""Generate 1000+ synthetic user profiles."""

import json
import random
import os
from pathlib import Path

def generate_user_profiles(n=1000, output_path=None):
    """Generate n synthetic user profiles."""
    random.seed(42)
    
    cuisines = ["North Indian", "South Indian", "Chinese", "Italian", "Continental", "Street Food"]
    
    profiles = []
    for i in range(1, n + 1):
        is_veg = random.random() < 0.45  # 45% veg users
        avg_spend = random.randint(150, 1200)
        order_freq = random.randint(1, 20)  # orders per month
        num_cuisines = random.randint(1, 4)
        preferred = random.sample(cuisines, num_cuisines)
        
        profiles.append({
            "user_id": f"user_{i:04d}",
            "is_veg": is_veg,
            "avg_spend": avg_spend,
            "order_frequency": order_freq,
            "preferred_cuisines": preferred,
            "price_sensitivity": round(random.uniform(0.2, 0.9), 2),
            "addon_acceptance_rate": round(random.uniform(0.1, 0.7), 2),
        })
    
    if output_path is None:
        output_path = Path(__file__).parent / "user_profiles.json"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(profiles, f, indent=2)
    
    print(f"Generated {len(profiles)} user profiles -> {output_path}")
    return profiles

if __name__ == "__main__":
    generate_user_profiles()
