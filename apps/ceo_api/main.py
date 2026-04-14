from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from nats.aio.client import Client as NATS

from core.memory import MemoryCore
from shared.nats_client import connect_nats_from_env
from shared.schemas import CEOMessage, OsintRequest, TaskEnvelope, WorkflowResponse

app = FastAPI(title="Abel OS+ CEO API", version="3.3.0")

_nats: NATS | None = None
_memory: MemoryCore | None = None


@app.on_event("startup")
async def startup() -> None:
    global _nats, _memory
    _nats = await connect_nats_from_env(os.getenv("NATS_URL", "nats://nats:4222"))
    _memory = MemoryCore(os.getenv("MEMORY_DB_PATH", "./data/abel_memory.db"))


@app.on_event("shutdown")
async def shutdown() -> None:
    if _nats and _nats.is_connected:
        await _nats.close()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ceo-api"}


@app.post("/v1/message", response_model=WorkflowResponse)
async def ingest_message(msg: CEOMessage) -> WorkflowResponse:
    workflow_id = f"wf-{uuid.uuid4()}"
    subject = "abel.tasks.short.ceo.classify"
    payload = {"user_id": msg.user_id, "text": msg.text, "channel": msg.channel}

    task = TaskEnvelope(
        task_id=f"task-{uuid.uuid4()}",
        workflow_id=workflow_id,
        subject=subject,
        payload=payload,
        latency_class="SHORT",
        success_quorum=1,
    )
    assert _nats is not None
    await _nats.publish(task.subject, task.model_dump_json().encode("utf-8"))

    return WorkflowResponse(
        workflow_id=workflow_id,
        accepted=True,
        status="QUEUED",
        detail="Workflow accepted; processing continues asynchronously.",
    )


@app.post("/v1/osint/start", response_model=WorkflowResponse)
async def start_osint(req: OsintRequest) -> WorkflowResponse:
    if req.mode == "AUTO" and req.target_type in {"phone", "plate", "image"}:
        raise HTTPException(
            status_code=400,
            detail="AUTO mode is disabled for sensitive target types. Use RECOMMEND_ONLY.",
        )

    workflow_id = f"wf-{uuid.uuid4()}"
    task = TaskEnvelope(
        task_id=f"task-{uuid.uuid4()}",
        workflow_id=workflow_id,
        subject="abel.tasks.short.osint.start",
        payload=req.model_dump(),
        latency_class="SHORT",
        success_quorum=1,
        late_result_policy="attach_to_audit",
    )
    assert _nats is not None
    await _nats.publish(task.subject, task.model_dump_json().encode("utf-8"))

    if _memory:
        _memory.record_event(workflow_id, "ceo-api", "QUEUED", {"target_type": req.target_type})

    return WorkflowResponse(
        workflow_id=workflow_id,
        accepted=True,
        status="QUEUED",
        detail="OSINT workflow queued in RECOMMEND/HITL-safe mode.",
    )


@app.get("/v1/memory/{workflow_id}")
async def memory_snapshot(workflow_id: str) -> dict[str, Any]:
    if not _memory:
        raise HTTPException(status_code=503, detail="memory core unavailable")
    return _memory.reconstruct_workflow(workflow_id)


@app.get("/v1/lanes")
async def lane_defaults() -> dict[str, dict[str, int | str]]:
    return {
        "REALTIME": {"deadline_soft_ms": 200, "deadline_hard_ms": 1500},
        "SHORT": {"deadline_soft_ms": 500, "deadline_hard_ms": 5000},
        "HEAVY": {"deadline_soft_ms": 4000, "deadline_hard_ms": 15000},
        "DURABLE": {"deadline_soft_ms": 10000, "deadline_hard_ms": 300000},
        "BACKGROUND": {"deadline_soft_ms": 20000, "deadline_hard_ms": 600000},
    }
