from __future__ import annotations

import asyncio
import os

from nats.aio.client import Client as NATS

from core.memory import MemoryCore


async def run() -> None:
    memory = MemoryCore(os.getenv("MEMORY_DB_PATH", "./data/abel_memory.db"))

    nc = NATS()
    await nc.connect(os.getenv("NATS_URL", "nats://nats:4222"))

    async def on_result(msg) -> None:  # type: ignore[no-untyped-def]
        workflow_id = msg.subject.split("abel.tasks.result.")[-1]
        memory.record_event(
            workflow_id=workflow_id,
            stage="sandbox_runtime",
            status="RESULT_OBSERVED",
            payload={"subject": msg.subject, "payload": msg.data.decode("utf-8")[:500]},
        )

    await nc.subscribe("abel.tasks.result.>", cb=on_result)
    print("[sandbox-runtime] observing abel.tasks.result.>")

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run())
