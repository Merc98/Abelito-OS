from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

EventType = Literal[
    "abel.mobile.session.started", "abel.mobile.session.ended", "abel.mobile.device.connected",
    "abel.mobile.device.disconnected", "abel.mobile.screen.detected", "abel.mobile.ui_tree.received",
    "abel.mobile.screenshot.captured", "abel.mobile.offer.detected", "abel.mobile.offer.parsed",
    "abel.mobile.offer.scored", "abel.mobile.action.recommended", "abel.mobile.action.requested",
    "abel.mobile.action.approved", "abel.mobile.action.executed", "abel.mobile.action.blocked",
    "abel.mobile.kill_switch.enabled", "abel.mobile.kill_switch.triggered", "abel.mobile.selector.drift_detected",
    "abel.mobile.parser.low_confidence", "abel.mobile.telemetry.recorded",
]
Mode = Literal["observer", "recommend_only", "supervised_executor"]


def utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass
class MobileEvent:
    event_type: EventType
    agent: str = "MobileScreenAgent"
    timestamp: str = field(default_factory=utcnow)
    payload: dict[str, Any] = field(default_factory=dict)
