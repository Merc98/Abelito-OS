from __future__ import annotations

from abel_os.schemas import BlockingScope, LanePolicy, LateResultPolicy, LatencyClass

DEFAULT_LANES: dict[LatencyClass, LanePolicy] = {
    LatencyClass.REALTIME: LanePolicy(
        latency_class=LatencyClass.REALTIME,
        blocking_scope=BlockingScope.DEVICE,
        success_quorum=1,
        confidence_threshold=0.85,
        deadline_soft_ms=350,
        deadline_hard_ms=1500,
        late_result_policy=LateResultPolicy.ATTACH_TO_AUDIT,
    ),
    LatencyClass.SHORT: LanePolicy(
        latency_class=LatencyClass.SHORT,
        blocking_scope=BlockingScope.WORKFLOW,
        success_quorum=1,
        confidence_threshold=0.75,
        deadline_soft_ms=1000,
        deadline_hard_ms=5000,
        late_result_policy=LateResultPolicy.ENRICH_GRAPH,
    ),
    LatencyClass.HEAVY: LanePolicy(
        latency_class=LatencyClass.HEAVY,
        blocking_scope=BlockingScope.WORKFLOW,
        success_quorum=1,
        confidence_threshold=0.70,
        deadline_soft_ms=3500,
        deadline_hard_ms=12000,
        late_result_policy=LateResultPolicy.RE_RANK_FUTURE_TASKS,
    ),
    LatencyClass.DURABLE: LanePolicy(
        latency_class=LatencyClass.DURABLE,
        blocking_scope=BlockingScope.SESSION,
        success_quorum=1,
        confidence_threshold=0.70,
        deadline_soft_ms=10000,
        deadline_hard_ms=60000,
        late_result_policy=LateResultPolicy.TRIGGER_FOLLOWUP_SUMMARY,
    ),
    LatencyClass.BACKGROUND: LanePolicy(
        latency_class=LatencyClass.BACKGROUND,
        blocking_scope=BlockingScope.NONE,
        success_quorum=1,
        confidence_threshold=0.50,
        deadline_soft_ms=30000,
        deadline_hard_ms=120000,
        late_result_policy=LateResultPolicy.ENRICH_GRAPH,
    ),
}
