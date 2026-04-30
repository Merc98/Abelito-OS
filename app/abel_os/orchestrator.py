from __future__ import annotations

import asyncio
import uuid
from collections.abc import Awaitable, Callable

from abel_os.schemas import PartialResult, TaskStatus, WorkflowClosure, WorkflowPlan, WorkflowState


Provider = Callable[[], Awaitable[PartialResult]]


class WorkflowOrchestrator:
    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowState] = {}

    def create_workflow(self, plan: WorkflowPlan) -> WorkflowState:
        workflow = WorkflowState(workflow_id=str(uuid.uuid4()), plan=plan)
        self._workflows[workflow.workflow_id] = workflow
        return workflow

    def get_workflow(self, workflow_id: str) -> WorkflowState | None:
        return self._workflows.get(workflow_id)

    def ingest_partial(self, workflow_id: str, result: PartialResult) -> WorkflowState:
        workflow = self._workflows[workflow_id]
        workflow.partial_results.append(result)
        self._close_if_sufficient(workflow)
        return workflow

    async def run_parallel(self, workflow_id: str, providers: dict[str, Provider]) -> WorkflowState:
        workflow = self._workflows[workflow_id]
        lane = workflow.plan.lane_policy
        tasks = {
            asyncio.create_task(provider()): provider_name
            for provider_name, provider in providers.items()
        }
        timeout_seconds = lane.deadline_hard_ms / 1000

        try:
            while tasks and not workflow.closed:
                done, pending = await asyncio.wait(
                    tasks.keys(),
                    timeout=timeout_seconds,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if not done:
                    timeout_result = PartialResult(
                        source="orchestrator",
                        status=TaskStatus.TIMEOUT_HARD,
                        confidence=0.0,
                        usable_for_decision=False,
                        fields_missing=["quorum"],
                    )
                    workflow.partial_results.append(timeout_result)
                    workflow.closure = WorkflowClosure.DEGRADED_BUT_USABLE
                    workflow.closed = True
                    for task in pending:
                        task.cancel()
                    break

                for task in done:
                    result = await task
                    workflow.partial_results.append(result)
                    self._close_if_sufficient(workflow)
                    tasks.pop(task, None)

                if workflow.closed:
                    for task in pending:
                        task.cancel()
                    for task, provider_name in list(tasks.items()):
                        workflow.partial_results.append(
                            PartialResult(
                                source=provider_name,
                                status=TaskStatus.CANCELLED_BY_WINNER,
                                confidence=0.0,
                                usable_for_decision=False,
                            )
                        )
                    break
        finally:
            return workflow

    def _close_if_sufficient(self, workflow: WorkflowState) -> None:
        if workflow.closed:
            return

        policy = workflow.plan.lane_policy
        usable = [
            result
            for result in workflow.partial_results
            if result.usable_for_decision and result.confidence >= policy.confidence_threshold
        ]

        if len(usable) >= policy.success_quorum:
            workflow.closure = WorkflowClosure.SUCCESS_QUORUM
            workflow.closed = True
            return

        any_usable = any(result.usable_for_decision for result in workflow.partial_results)
        any_failed = any(result.status == TaskStatus.FAILED for result in workflow.partial_results)

        if any_usable and len(workflow.partial_results) >= policy.success_quorum:
            workflow.closure = WorkflowClosure.SUCCESS_PARTIAL_SUFFICIENT
            workflow.closed = True
            return

        if any_failed and not any_usable:
            workflow.closure = WorkflowClosure.DEGRADED_BUT_USABLE
