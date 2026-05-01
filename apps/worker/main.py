from __future__ import annotations

import asyncio
import os

from shared.nats_client import connect_nats_from_env
from shared.schemas import TaskEnvelope


async def run() -> None:
    nc = await connect_nats_from_env(os.getenv("NATS_URL", "nats://nats:4222"))

    async def handle_task(msg) -> None:  # type: ignore[no-untyped-def]
        task = TaskEnvelope.model_validate_json(msg.data.decode("utf-8"))
        print(
            f"[worker] task={task.task_id} wf={task.workflow_id} "
            f"lane={task.latency_class} subject={task.subject}"
        )
        await asyncio.sleep(0.1)

    async def handle_result(msg) -> None:  # type: ignore[no-untyped-def]
        print(f"[worker] result={msg.subject} payload={msg.data.decode('utf-8')[:240]}")

    await nc.subscribe("abel.tasks.short.ceo.classify", cb=handle_task)
    await nc.subscribe("abel.tasks.result.>", cb=handle_result)
    print("[worker] listening on classify + results")
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run())
