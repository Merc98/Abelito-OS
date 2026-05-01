from __future__ import annotations

import uuid
from typing import Any

COMMITTEES: dict[str, dict[str, Any]] = {
    "intelligence": {
        "name": "Intelligence Committee",
        "agents": ["osint-orchestrator", "memory-curator", "guardrails"],
        "keywords": ["osint", "investigar", "buscar", "dominio", "email", "usuario", "recon"],
    },
    "mobile": {
        "name": "Mobile Committee",
        "agents": ["android-builder", "device-bridge", "release-runner"],
        "keywords": ["android", "apk", "móvil", "movil", "teléfono", "telefono", "app", "webview"],
    },
    "engineering": {
        "name": "Engineering Committee",
        "agents": ["coder", "reviewer", "test-runner"],
        "keywords": ["fix", "bug", "código", "codigo", "refactor", "test", "github", "commit"],
    },
    "security": {
        "name": "Security & Governance Committee",
        "agents": ["policy-checker", "audit-logger", "risk-reviewer"],
        "keywords": ["seguridad", "riesgo", "legal", "guardrail", "policy", "permiso", "compliance"],
    },
    "operations": {
        "name": "Operations Committee",
        "agents": ["router", "generalist", "memory-curator"],
        "keywords": [],
    },
}


def select_committee(text: str) -> str:
    normalized = text.lower()
    for committee_id, committee in COMMITTEES.items():
        if committee_id == "operations":
            continue
        if any(keyword in normalized for keyword in committee["keywords"]):
            return committee_id
    return "operations"


def build_tasks(workflow_id: str, text: str, committee_id: str) -> list[dict[str, Any]]:
    committee = COMMITTEES[committee_id]
    return [
        {
            "task_id": f"task-{uuid.uuid4()}",
            "workflow_id": workflow_id,
            "committee": committee_id,
            "agent": agent,
            "description": text,
            "input": {"text": text},
            "status": "QUEUED",
        }
        for agent in committee["agents"]
    ]


def build_chat_reply(workflow_id: str, text: str) -> dict[str, Any]:
    committee_id = select_committee(text)
    committee = COMMITTEES[committee_id]
    tasks = build_tasks(workflow_id, text, committee_id)
    results = [
        {
            "task_id": task["task_id"],
            "agent": task["agent"],
            "status": "ACCEPTED",
            "summary": f"{task['agent']} recibió la tarea dentro de {committee['name']}.",
        }
        for task in tasks
    ]
    reply = (
        f"[CEO]\n"
        f"Asigné tu mensaje al comité: {committee['name']}.\n"
        f"Agentes activos: {', '.join(committee['agents'])}.\n\n"
        f"Workflow: {workflow_id}\n"
        f"Estado: QUEUED\n\n"
        "Siguiente paso: los workers procesan por bus NATS y la memoria queda consultable desde el whiteboard."
    )
    return {
        "workflow_id": workflow_id,
        "accepted": True,
        "status": "QUEUED",
        "detail": "Workflow accepted by CEO chat core.",
        "reply": reply,
        "committee": committee_id,
        "committee_name": committee["name"],
        "agents": committee["agents"],
        "tasks": tasks,
        "results": results,
    }
