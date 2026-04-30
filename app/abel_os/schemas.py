from __future__ import annotations

from enum import Enum
from typing import Literal

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


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT_SOFT = "TIMEOUT_SOFT"
    TIMEOUT_HARD = "TIMEOUT_HARD"
    CANCELLED_BY_WINNER = "CANCELLED_BY_WINNER"
    DEGRADED_BACKGROUND = "DEGRADED_BACKGROUND"


class WorkflowClosure(str, Enum):
    SUCCESS_FULL = "SUCCESS_FULL"
    SUCCESS_QUORUM = "SUCCESS_QUORUM"
    SUCCESS_PARTIAL_SUFFICIENT = "SUCCESS_PARTIAL_SUFFICIENT"
    DEGRADED_BUT_USABLE = "DEGRADED_BUT_USABLE"
    HITL_REQUIRED = "HITL_REQUIRED"
    FAILED_UNRECOVERABLE = "FAILED_UNRECOVERABLE"


class LateResultPolicy(str, Enum):
    DISCARD = "discard"
    ATTACH_TO_AUDIT = "attach_to_audit"
    ENRICH_GRAPH = "enrich_graph"
    RE_RANK_FUTURE_TASKS = "re-rank_future_tasks"
    TRIGGER_FOLLOWUP_SUMMARY = "trigger_followup_summary"


class RecommendedNextStep(str, Enum):
    ACT_NOW = "ACT_NOW"
    WAIT = "WAIT"
    ESCALATE = "ESCALATE"
    OCR = "OCR"
    VISION = "VISION"


class MobileMode(str, Enum):
    RECOMMEND_ONLY = "RECOMMEND_ONLY"
    SEMI_AUTO = "SEMI_AUTO"
    AUTO_DETERMINISTIC = "AUTO_DETERMINISTIC"
    AUTO_INTERNAL_LAB = "AUTO_INTERNAL_LAB"


class DecisionOutcome(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    HUMAN = "HUMAN"
    RECOMMEND_ONLY = "RECOMMEND_ONLY"


class LanePolicy(BaseModel):
    latency_class: LatencyClass
    blocking_scope: BlockingScope = BlockingScope.NONE
    success_quorum: int = Field(default=1, ge=1)
    confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    deadline_soft_ms: int = Field(default=500, ge=1)
    deadline_hard_ms: int = Field(default=5000, ge=1)
    late_result_policy: LateResultPolicy = LateResultPolicy.ENRICH_GRAPH


class PartialResult(BaseModel):
    source: str
    status: TaskStatus
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    fields_complete: list[str] = Field(default_factory=list)
    fields_missing: list[str] = Field(default_factory=list)
    usable_for_decision: bool = False
    recommended_next_step: RecommendedNextStep = RecommendedNextStep.WAIT
    payload: dict = Field(default_factory=dict)


class WorkflowPlan(BaseModel):
    workflow_name: str
    intent: str
    ministries: list[str]
    lane_policy: LanePolicy
    autonomy_level: Literal["LOW", "MEDIUM", "HIGH"]
    notes: list[str] = Field(default_factory=list)


class WorkflowState(BaseModel):
    workflow_id: str
    plan: WorkflowPlan
    partial_results: list[PartialResult] = Field(default_factory=list)
    closure: WorkflowClosure | None = None
    closed: bool = False

    @property
    def usable_results(self) -> list[PartialResult]:
        return [result for result in self.partial_results if result.usable_for_decision]


class MobileOffer(BaseModel):
    fare: float | None = Field(default=None, ge=0.0)
    pickup_eta_minutes: int | None = Field(default=None, ge=0)
    pickup_miles: float | None = Field(default=None, ge=0.0)
    trip_miles: float | None = Field(default=None, ge=0.0)
    destination_zone: str | None = None
    surge_multiplier: float | None = Field(default=None, ge=0.0)
    accept_button_visible: bool = True
    source_confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class MobileDecision(BaseModel):
    decision: DecisionOutcome
    recommended_action: Literal["ACCEPT", "REJECT", "WAIT", "ESCALATE"]
    execution_allowed: bool
    confidence: float = Field(ge=0.0, le=1.0)
    pay_per_mile: float | None = None
    reasons: list[str] = Field(default_factory=list)
    mode_applied: MobileMode
