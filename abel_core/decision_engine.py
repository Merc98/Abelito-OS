from __future__ import annotations
from typing import Any

class DecisionEngine:
    def classify(self, message: str) -> str:
        low = message.lower()
        if any(x in low for x in ["scan", "osint", "whois", "dns"]):
            return "osint"
        if any(x in low for x in ["test", "pytest", "refactor", "code"]):
            return "dev"
        if any(x in low for x in ["ride", "uber", "lyft", "pickup"]):
            return "mobile"
        if "github.com/" in low or "git clone" in low or "repo" in low:
            return "github_operation"
        return "general"

    def decompose(self, message: str) -> list[dict[str, Any]]:
        cls = self.classify(message)
        return [{"task": cls, "message": message}]
