from __future__ import annotations
import re
from typing import Any
from suites.mobile.device_manager import list_devices


def _extract(text: str, pattern: str) -> float | None:
    m = re.search(pattern, text, re.I)
    return float(m.group(1)) if m else None


def decide_offer(page_source: str) -> dict[str, Any]:
    fare = _extract(page_source, r"\$\s*([0-9]+(?:\.[0-9]+)?)")
    pickup = _extract(page_source, r"pickup\D*([0-9]+(?:\.[0-9]+)?)\s*min")
    km = _extract(page_source, r"([0-9]+(?:\.[0-9]+)?)\s*km")
    if fare is None or pickup is None or km is None:
        return {"decision": "HUMAN_REVIEW", "reason": "missing_fields", "confidence": 0.4}
    ratio = fare / max(km, 0.1)
    if pickup > 10 or fare < 6:
        return {"decision": "REJECT", "reason": "threshold_block", "confidence": 0.98, "fare": fare, "pickup": pickup, "km": km}
    if ratio > 2.5 and fare >= 12:
        return {"decision": "ACCEPT", "reason": "high_value", "confidence": 0.96, "fare": fare, "pickup": pickup, "km": km}
    return {"decision": "HUMAN_REVIEW", "reason": "ambiguous", "confidence": 0.7, "fare": fare, "pickup": pickup, "km": km}


def execute(page_source: str) -> dict[str, Any]:
    devices = list_devices()
    if not devices:
        return {"status": "no_device"}
    result = decide_offer(page_source)
    return {"status": "evaluated", "devices": devices, "result": result}
