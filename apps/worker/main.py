from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from core.memory import MemoryCore
from shared.nats_client import connect_nats_from_env
from shared.schemas import TaskEnvelope


def _result_for(task: TaskEnvelope) -> dict[str, Any]:
    payload = task.payload if isinstance(task.payload, dict) else {}
    return {
        "task_id": task.task_id,
        "workflow_id": task.workflow_id,
        "agent": payload.get("agent", "worker"),
        "committee": payload.get("committee", "unknown"),
        "status": "COMPLETED",
        "summary": "Accepted and processed by generic committee worker.",
    }


async def run() -> None:
    nc = await connect_nats_from_env(os.getenv("NATS_URL", "nats://nats:4222"))
    memory = MemoryCore(os.getenv("MEMORY_DB_PATH", "./data/abel_memory.db"))

    async def handle_task(msg) -> None:  # type: ignore[no-untyped-def]
        task = TaskEnvelope.model_validate_json(msg.data.decode("utf-8"))
        payload = task.payload if isinstance(task.payload, dict) else {}

        memory.record_event(
            task.workflow_id,
            payload.get("agent", "worker"),
            "RECEIVED",
            {
                "task_id": task.task_id,
                "subject": msg.subject,
                "committee": payload.get("committee"),
                "agent": payload.get("agent"),
                "input": payload.get("input"),
            },
        )

        result = _result_for(task)

        memory.record_event(
            task.workflow_id,
            result["agent"],
            "COMPLETED",
            result,
        )

        result_subject = f"abel.tasks.result.{task.workflow_id}"
        await nc.publish(result_subject, json.dumps(result).encode("utf-8"))
        print(f"[worker] completed task={task.task_id} wf={task.workflow_id} subject={msg.subject}")

    async def handle_result(msg) -> None:  # type: ignore[no-untyped-def]
        print(f"[worker] result={msg.subject} payload={msg.data.decode('utf-8')[:240]}")

    await nc.subscribe("abel.tasks.request.*", cb=handle_task)
    await nc.subscribe("abel.tasks.result.*", cb=handle_result)
    print("[worker] listening on abel.tasks.request.* + abel.tasks.result.*")

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run())
