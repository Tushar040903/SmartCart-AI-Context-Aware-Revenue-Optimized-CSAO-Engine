"""User Context: loads and manages user profile and preferences."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


DEFAULT_PROFILE = {
    "user_id": "guest",
    "is_veg": False,
    "avg_spend": 400,
    "order_frequency": 5,
    "preferred_cuisines": ["North Indian"],
    "price_sensitivity": 0.5,
    "addon_acceptance_rate": 0.3,
}


class UserContext:
    """Manages user profile and provides dietary/spend context."""

    def __init__(self, profile: Optional[Dict[str, Any]] = None):
        """Initialize with an optional profile dict."""
        self.profile = profile or DEFAULT_PROFILE.copy()

    @classmethod
    def from_user_id(cls, user_id: str, profiles_path: Optional[Path] = None):
        """Load a user profile by user_id from the profiles JSON file."""
        if profiles_path is None:
            profiles_path = (
                Path(__file__).parent.parent.parent
                / "data" / "synthetic" / "user_profiles.json"
            )
        try:
            with open(profiles_path) as f:
                profiles = json.load(f)
            for p in profiles:
                if p.get("user_id") == user_id:
                    return cls(profile=p)
        except FileNotFoundError:
            pass
        return cls()

    @property
    def is_veg(self) -> bool:
        return self.profile.get("is_veg", False)

    @property
    def avg_spend(self) -> float:
        return self.profile.get("avg_spend", 400)

    @property
    def price_sensitivity(self) -> float:
        return self.profile.get("price_sensitivity", 0.5)

    @property
    def addon_acceptance_rate(self) -> float:
        return self.profile.get("addon_acceptance_rate", 0.3)

    @property
    def preferred_cuisines(self):
        return self.profile.get("preferred_cuisines", [])

    def to_dict(self) -> Dict[str, Any]:
        return self.profile.copy()
