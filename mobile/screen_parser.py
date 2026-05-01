from __future__ import annotations
import re
from typing import Any


class ScreenParser:
    fare_pattern = re.compile(r"\$\s*(\d+(?:\.\d{1,2})?)")
    miles_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(?:mi|miles)", re.IGNORECASE)
    pickup_pattern = re.compile(r"(\d+)\s*(?:min|mins|minutes)", re.IGNORECASE)

    def parse(self, ui_tree: str, ocr_text: str | None = None) -> dict[str, Any]:
        text = ui_tree or ""
        source = "ui_tree"
        if not text and ocr_text:
            text = ocr_text
            source = "ocr"
        fare = self._extract_float(self.fare_pattern, text)
        miles = self._extract_float(self.miles_pattern, text)
        pickup = self._extract_int(self.pickup_pattern, text)
        fields = {"fare": fare, "trip_miles": miles, "pickup_minutes": pickup, "destination": None}
        missing = [k for k, v in fields.items() if k in ("fare", "trip_miles", "pickup_minutes") and v is None]
        screen_type = "offer" if len(missing) < 3 else "unknown"
        conf = 0.9 if not missing else 0.65 if len(missing) <= 1 else 0.4
        return {"screen_type": screen_type, "fields": fields, "confidence": conf, "missing_fields": missing, "source": source, "warnings": []}

    def _extract_float(self, pattern: re.Pattern[str], text: str) -> float | None:
        m = pattern.search(text)
        return float(m.group(1)) if m else None

    def _extract_int(self, pattern: re.Pattern[str], text: str) -> int | None:
        m = pattern.search(text)
        return int(m.group(1)) if m else None
