from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class LatencyClass(str, Enum):
    REALTIME = "REALTIME"
    SHORT = "SHORT"
    HEAVY = "HEAVY"
    DURABLE = "DURABLE"
    BACKGROUND = "BACKGROUND"


class BlockingScope(str, Enum):
    NONE = "NONE"
    WORKFLOW = "WORKFLOW"
    DEVICE = "DEVICE"
    SESSION = "SESSION"


class TaskEnvelope(BaseModel):
    task_id: str
    workflow_id: str
    subject: str
    payload: dict[str, Any] = Field(default_factory=dict)
    latency_class: LatencyClass = LatencyClass.SHORT
    blocking_scope: BlockingScope = BlockingScope.NONE
    success_quorum: int = 1
    deadline_soft_ms: int = 500
    deadline_hard_ms: int = 5000
    late_result_policy: str = "enrich_graph"


class CEOMessage(BaseModel):
    user_id: str
    text: str
    channel: str = "api"


class WorkflowResponse(BaseModel):
    workflow_id: str
    accepted: bool
    status: str
    detail: str
    reply: str | None = None
    committee: str | None = None
    committee_name: str | None = None
    agents: list[str] = Field(default_factory=list)
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    results: list[dict[str, Any]] = Field(default_factory=list)


class OsintRequest(BaseModel):
    target: str
    target_type: Literal["email", "username", "domain", "phone", "plate", "image"]
    purpose: str
    consent_or_legal_basis: str
    mode: Literal["RECOMMEND_ONLY", "SEMI_AUTO", "AUTO"] = "RECOMMEND_ONLY"


class Finding(BaseModel):
    source: str
    category: str
    value: str
    confidence: float
    public_data_only: bool = True


class OsintReport(BaseModel):
    request: OsintRequest
    status: str
    summary: str
    findings: list[Finding]
    risk: Literal["low", "medium", "high"]
    recommended_next_step: str
