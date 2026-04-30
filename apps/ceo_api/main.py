from __future__ import annotations

import os
import uuid
import logging
import inspect
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from nats.aio.client import Client as NATS

from core.memory import MemoryCore
from shared.nats_client import connect_nats_from_env
from shared.schemas import CEOMessage, OsintRequest, TaskEnvelope, WorkflowResponse
from .committees import build_chat_reply

logger = logging.getLogger("abel.ceo_api")
DASHBOARD_HTML = Path(__file__).resolve().parent / "dashboard" / "index.html"

_nats: Any | None = None
_memory: MemoryCore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _nats, _memory
    _nats = await connect_nats_from_env(os.getenv("NATS_URL", "nats://nats:4222"))
    _memory = MemoryCore(os.getenv("MEMORY_DB_PATH", "./data/abel_memory.db"))
    yield
    if _nats and _nats.is_connected:
        await _nats.close()


app = FastAPI(title="Abel OS+ CEO API", version="3.3.0", lifespan=lifespan)


@app.post("/task/route")
async def route_task(task: CEOMessage):
    """Router Agent: Analyzes task and assigns to specialist."""
    logger.info(f"Routing task: {task.text}")
    
    text = task.text.lower()
    specialist = "Generalist"
    
    if any(k in text for k in ["fix", "code", "refactor", "bug"]):
        specialist = "Coder"
    elif any(k in text for k in ["test", "verify", "security"]):
        specialist = "Reviewer"
    elif any(k in text for k in ["build", "deploy", "apk"]):
        specialist = "Builder"
    elif any(k in text for k in ["apk", "decompile", "rebuild"]):
        specialist = "Android Analyst"
    elif any(k in text for k in ["web", "browse", "navigate"]):
        specialist = "Browser Worker"
        
    logger.info(f"Assigned task to specialist: {specialist}")
    
    if _memory:
        _memory.store_knowledge(
            category=f"task_routing_{task.user_id}",
            content=f"User {task.user_id} requested '{task.text}'. Routed to {specialist}.",
            tags=["router", "log"]
        )
        
    return {"status": "ROUTED", "specialist": specialist, "task": task.text}

@app.get("/memory/curated")
async def get_curated_knowledge(topic: str):
    if not _memory:
        raise HTTPException(status_code=500, detail="Memory not initialized")
    
    results = _memory.search_knowledge(topic)
    return {"topic": topic, "results": results}


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

    # Enriched chat-style payload for dashboard/UI (non-breaking)
    chat = build_chat_reply(workflow_id, msg.text)

    return WorkflowResponse(
        workflow_id=workflow_id,
        accepted=True,
        status="QUEUED",
        detail="Workflow accepted; processing continues asynchronously.",
        **{k: v for k, v in chat.items() if k not in {"workflow_id", "accepted", "status", "detail"}}
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


# ── Auth endpoints ─────────────────────────────────────────────────────────────

from pydantic import BaseModel as _BM


class LoginRequest(_BM):
    user_id: str
    password: str


class LoginResponse(_BM):
    token: str
    role: str


@app.post("/v1/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest) -> LoginResponse:
    from shared.auth import UserStore
    store = UserStore(os.getenv("USERS_DB_PATH", "./data/abel_users.db"))
    token = store.authenticate(req.user_id, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    from shared.auth import verify_token
    payload = verify_token(token)
    return LoginResponse(token=token, role=payload.role.value)


# ── Provider endpoints ─────────────────────────────────────────────────────────

class SwitchProviderRequest(_BM):
    provider: str


@app.get("/v1/providers")
async def list_providers() -> list[dict]:
    from shared.providers.registry import build_default_registry
    registry = build_default_registry()
    return registry.list_providers()


@app.post("/v1/providers/switch")
async def switch_provider(req: SwitchProviderRequest) -> dict[str, str]:
    from shared.providers.registry import build_default_registry
    registry = build_default_registry()
    try:
        registry.set_active(req.provider)
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"active_provider": registry.active_name}


# ── Skills endpoints ───────────────────────────────────────────────────────────

class ExecuteSkillRequest(_BM):
    skill: str
    action: str
    params: dict[str, Any] = {}


@app.get("/v1/skills")
async def list_skills() -> list[dict]:
    from skills.__loader__ import registry
    return registry.list_available()


@app.post("/v1/skills/execute")
async def execute_skill(req: ExecuteSkillRequest) -> Any:
    from skills.__loader__ import registry
    try:
        skill_instance = registry.load_skill(req.skill)
        
        action_method = getattr(skill_instance, req.action, None)
        if not action_method or not callable(action_method):
            action_method = getattr(skill_instance, "execute_action", None)
            if not action_method:
                raise HTTPException(status_code=400, detail=f"Action '{req.action}' not found in skill '{req.skill}'")
            
            if inspect.iscoroutinefunction(action_method):
                return await action_method(req.action, req.params)
            else:
                return action_method(req.action, req.params)

        if inspect.iscoroutinefunction(action_method):
            return await action_method(**req.params)
        else:
            return action_method(**req.params)
            
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Skill '{req.skill}' not found")
    except Exception as e:
        logger.error(f"Skill execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
