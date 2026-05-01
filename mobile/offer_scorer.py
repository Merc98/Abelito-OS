from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class OfferScore:
    score: float
    recommendation: str
    reasons: list[str]
    confidence: float


class OfferScorer:
    def __init__(self, rules: dict[str, Any]):
        self.rules = rules.get("mobile_offer_rules", rules)

    def score(self, fields: dict[str, Any]) -> OfferScore:
        required = ["fare", "pickup_minutes", "trip_miles"]
        if any(fields.get(k) in (None, "") for k in required):
            return OfferScore(0.4, "HUMAN_REVIEW", ["missing_required_fields"], 0.6)
        fare = float(fields["fare"])
        pickup = int(fields["pickup_minutes"])
        miles = float(fields["trip_miles"])
        ppm = fare / max(miles, 0.1)
        reasons = [f"pay_per_mile={ppm:.2f}"]
        if pickup >= self.rules["max_pickup_minutes"]:
            return OfferScore(0.2, "REJECT", reasons + ["pickup_too_long"], 0.95)
        if fare < self.rules["min_fare_absolute"]:
            return OfferScore(0.1, "REJECT", reasons + ["fare_below_absolute_min"], 0.97)
        if ppm >= self.rules["min_pay_per_mile"] and fare >= self.rules["min_fare"]:
            return OfferScore(0.92, "ACCEPT", reasons + ["meets_min_ppm_and_fare"], 0.94)
        return OfferScore(0.55, "HUMAN_REVIEW", reasons + ["ambiguous_offer"], 0.8)
