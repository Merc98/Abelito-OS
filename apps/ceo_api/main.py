from __future__ import annotations

import os
import uuid
import logging
import inspect
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core.memory import MemoryCore
from core.native_tools import NativeTools
from core.response_compressor import response_compressor
from shared.nats_client import connect_nats_from_env
from shared.auth import require_auth
from shared.schemas import CEOMessage, OsintRequest, TaskEnvelope, WorkflowResponse
from .committees import COMMITTEES, select_committee, build_chat_reply

logger = logging.getLogger("abel.ceo_api")
DASHBOARD_HTML = Path(__file__).resolve().parent / "dashboard" / "index.html"

_nats: Any | None = None
_memory: MemoryCore | None = None
_native: NativeTools | None = None


class SmartSearchRequest(BaseModel):
    query: str
    mode: str = "auto"


class WebSearchRequest(BaseModel):
    query: str
    engines: list[str] = Field(default_factory=lambda: ["bing", "yahoo", "startpage", "aol"])


class LearnRequest(BaseModel):
    title: str
    content: str
    type: str
    files: list[str]
    tags: list[str]
    confidence: float = 0.85


class RecallRequest(BaseModel):
    query: str
    type: str | None = None
    mode: str = "auto"


class CustomizeRequest(BaseModel):
    feature_desc: str
    base_url: str = "http://127.0.0.1:8080"
    log_path: str = "./logs/server.log"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _nats, _memory, _native
    _nats = None
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    try:
        async def try_connect():
            return await connect_nats_from_env(nats_url)
        _nats = await asyncio.wait_for(try_connect(), timeout=3.0)
        logger.info(f"NATS conectado exitosamente en {nats_url}")
    except Exception as e:
        logger.warning(f"NATS no disponible ({e}). Ejecutando en modo local sin cola de mensajes.")
        _nats = None
    _memory = MemoryCore(os.getenv("MEMORY_DB_PATH", "./data/abel_memory.db"))
    _native = NativeTools(".")
    yield
    if _nats and _nats.is_connected:
        await _nats.close()


app = FastAPI(title="Abel OS+ CEO API", version="3.4.0", lifespan=lifespan)


@app.get("/v1/committees")
async def list_committees() -> dict[str, Any]:
    return COMMITTEES


@app.post("/task/route")
async def route_task(task: CEOMessage):
    from shared.agent_modes import get_mode

    try:
        mode = get_mode(task.mode)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    committee_id = select_committee(task.text)
    committee = COMMITTEES[committee_id]

    return {
        "status": "ROUTED",
        "committee": committee_id,
        "committee_name": committee["name"],
        "agents": committee["agents"],
        "task": task.text,
        "mode": mode.name,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ceo-api"}


@app.get("/dashboard")
async def dashboard() -> FileResponse:
    if not DASHBOARD_HTML.exists():
        raise HTTPException(status_code=404, detail="dashboard unavailable")
    return FileResponse(DASHBOARD_HTML)


@app.post("/v1/message", response_model=WorkflowResponse)
async def ingest_message(msg: CEOMessage) -> WorkflowResponse:
    workflow_id = f"wf-{uuid.uuid4()}"

    chat_reply = build_chat_reply(workflow_id, msg.text)

    dispatch_receipts = []

    for task in chat_reply["tasks"]:
        subject = f"abel.tasks.request.{task['committee']}"

        if _nats:
            envelope = TaskEnvelope(
                task_id=task["task_id"],
                workflow_id=workflow_id,
                subject=subject,
                payload=task,
                latency_class="SHORT",
                success_quorum=1,
            )
            await _nats.publish(subject, envelope.model_dump_json().encode("utf-8"))
            status = "DISPATCHED"
        else:
            status = "SKIPPED_NO_NATS"

        dispatch_receipts.append({
            "task_id": task["task_id"],
            "subject": subject,
            "status": status,
        })

    if _memory:
        _memory.record_event(
            workflow_id,
            "ceo-api",
            "QUEUED",
            {
                "user_id": msg.user_id,
                "channel": msg.channel,
                "text": msg.text,
                "committee": chat_reply["committee"],
                "agents": chat_reply["agents"],
                "task_ids": [t["task_id"] for t in chat_reply["tasks"]],
                "dispatch_receipts": dispatch_receipts,
            },
        )

    return WorkflowResponse(
        workflow_id=workflow_id,
        accepted=True,
        status="QUEUED",
        detail="Workflow aceptado; tasks despachadas por comité.",
        reply=chat_reply["reply"],
        committee=chat_reply["committee"],
        committee_name=chat_reply["committee_name"],
        agents=chat_reply["agents"],
        tasks=chat_reply["tasks"],
        results=dispatch_receipts,
    )


@app.post("/v1/osint/start", response_model=WorkflowResponse)
async def start_osint(req: OsintRequest) -> WorkflowResponse:
    if req.mode == "AUTO" and req.target_type in {"phone", "plate", "image"}:
        raise HTTPException(
            status_code=400,
            detail="AUTO mode is disabled for sensitive target types. Use RECOMMEND_ONLY.",
        )

    if not _nats:
        raise HTTPException(status_code=503, detail="NATS no disponible")

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

    await _nats.publish(task.subject, task.model_dump_json().encode("utf-8"))

    if _memory:
        _memory.record_event(workflow_id, "ceo-api", "QUEUED", {"target_type": req.target_type})

    return WorkflowResponse(
        workflow_id=workflow_id,
        accepted=True,
        status="QUEUED",
        detail="OSINT workflow queued.",
    )


@app.websocket("/v1/ws/workflow/{workflow_id}")
async def workflow_updates(websocket: WebSocket, workflow_id: str):
    await websocket.accept()
    if not _memory:
        await websocket.send_json({"error": "memory core unavailable"})
        await websocket.close()
        return

    try:
        while True:
            snapshot = _memory.reconstruct_workflow(workflow_id)
            await websocket.send_json(snapshot)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        return


@app.get("/v1/memory/{workflow_id}")
async def memory_snapshot(workflow_id: str) -> dict[str, Any]:
    if not _memory:
        raise HTTPException(status_code=503, detail="memory core unavailable")
    return _memory.reconstruct_workflow(workflow_id)


@app.post("/v1/agent/smart-search")
async def agent_smart_search(req: SmartSearchRequest) -> dict[str, Any]:
    if not _native:
        raise HTTPException(status_code=503, detail="native tools unavailable")
    hits = await _native.smart_search(req.query, req.mode)
    return {"results": hits}


@app.post("/v1/agent/web-search")
async def agent_web_search(req: WebSearchRequest) -> dict[str, Any]:
    if not _native:
        raise HTTPException(status_code=503, detail="native tools unavailable")
    results = await _native.web_search(req.query, req.engines)
    return {"results": results}


@app.post("/v1/agent/memory/learn")
async def agent_memory_learn(req: LearnRequest) -> dict[str, Any]:
    if not _native:
        raise HTTPException(status_code=503, detail="native tools unavailable")
    entry_id = _native.learn(req.title, req.content, req.type, req.files, req.tags, req.confidence)
    return {"id": entry_id}


@app.post("/v1/agent/memory/recall")
async def agent_memory_recall(req: RecallRequest) -> dict[str, Any]:
    if not _native:
        raise HTTPException(status_code=503, detail="native tools unavailable")
    return {"results": await _native.recall(req.query, req.type, req.mode)}


@app.post("/v1/agent/setup")
async def agent_setup() -> dict[str, Any]:
    if not _native:
        raise HTTPException(status_code=503, detail="native tools unavailable")
    return _native.agent_setup()


@app.post("/v1/agent/deploy")
async def agent_deploy(base_url: str = "http://127.0.0.1:8080", log_path: str = "./logs/server.log") -> dict[str, Any]:
    if not _native:
        raise HTTPException(status_code=503, detail="native tools unavailable")
    return await _native.agent_deploy(base_url=base_url, log_path=log_path)


@app.post("/v1/agent/customize")
async def agent_customize(req: CustomizeRequest) -> dict[str, Any]:
    if not _native:
        raise HTTPException(status_code=503, detail="native tools unavailable")
    return await _native.agent_customize(req.feature_desc, req.base_url, req.log_path)


@app.post("/v1/agent/compress")
async def agent_compress(data: str, max_tokens: int = 2000) -> dict[str, str]:
    return {"compressed": response_compressor(data, max_tokens=max_tokens)}
