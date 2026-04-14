from __future__ import annotations

import asyncio
import os

from apps.osint_orchestrator.pipeline import run_osint
from core.memory import MemoryCore
from shared.nats_client import connect_nats_from_env
from shared.schemas import OsintReport, OsintRequest, TaskEnvelope


async def run() -> None:
        memory = MemoryCore(os.getenv("MEMORY_DB_PATH", "./data/abel_memory.db"))

    nc = await connect_nats_from_env(os.getenv("NATS_URL", "nats://nats:4222"))

    async def handle_task(msg) -> None:  # type: ignore[no-untyped-def]
                task = TaskEnvelope.model_validate_json(msg.data.decode("utf-8"))
                memory.record_event(task.workflow_id, "orchestrator", "RECEIVED", {"subject": task.subject})

        try:
                        req = OsintRequest.model_validate(task.payload)
                        # run_osint already records policy failures internally when workflow_id is given;
                        # do NOT call memory.record_failure again here for REJECTED_POLICY to avoid
                        # duplicate failure rows that corrupt audit history and recovery metrics.
                        report = await run_osint(req, workflow_id=task.workflow_id)
                        if report.status != "REJECTED_POLICY":
                                            memory.record_event(
                                                                    task.workflow_id,
                                                                    "orchestrator",
                                                                    "COMPLETED",
                                                                    {"status": report.status, "finding_count": len(report.findings)},
                                            )
        except Exception as exc:  # noqa: BLE001
                        memory.record_failure(
                                            task.workflow_id,
                                            "orchestrator",
                                            str(exc),
                                            fingerprint=exc.__class__.__name__,
                        )
                        report = OsintReport(
                            request=OsintRequest(
                                target="unknown",
                                target_type="username",
                                purpose="error_recovery",
                                consent_or_legal_basis="incident_handling",
                                mode="RECOMMEND_ONLY",
                            ),
                            status="FAILED_UNRECOVERABLE",
                            summary=f"Unhandled error: {exc}",
                            findings=[],
                            risk="high",
                            recommended_next_step="HITL",
                        )

        result_subject = f"abel.tasks.result.{task.workflow_id}"
        await nc.publish(result_subject, report.model_dump_json().encode("utf-8"))
        print(f"[osint] wf={task.workflow_id} status={report.status} findings={len(report.findings)}")

    await nc.subscribe("abel.tasks.short.osint.start", cb=handle_task)
    print("[osint] listening on abel.tasks.short.osint.start")

    while True:
                await asyncio.sleep(1)


if __name__ == "__main__":
        asyncio.run(run())
