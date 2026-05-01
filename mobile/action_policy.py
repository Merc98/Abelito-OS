from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    required_fixes: list[str]
    downgrade_mode: str | None = None


def evaluate_action_request(request: dict[str, Any], context: dict[str, Any]) -> PolicyDecision:
    if context.get("mode") != "supervised_executor":
        return PolicyDecision(False, "mode_not_supervised_executor", ["switch_mode"])
    checks = [
        ("session_permission", "missing_session_permission"),
        ("ceo_delegation", "missing_ceo_delegation"),
        ("governance_approved", "missing_governance_approval"),
        ("kill_switch_active", "kill_switch_inactive"),
        ("audit_log_enabled", "audit_log_unavailable"),
        ("device_health_ok", "device_unhealthy"),
        ("selector_validated", "selector_not_validated"),
    ]
    for key, reason in checks:
        if not context.get(key):
            return PolicyDecision(False, reason, [key])
    if context.get("selector_drift_detected"):
        return PolicyDecision(False, "selector_drift_detected", ["refresh_selectors"], downgrade_mode="observer")
    if request.get("confidence", 0) < context.get("min_action_confidence", 0.9):
        return PolicyDecision(False, "confidence_below_threshold", ["improve_confidence"])
    if request.get("screen_type") != "offer":
        return PolicyDecision(False, "invalid_screen_type", ["reparse_screen"])
    return PolicyDecision(True, "allowed", [])
