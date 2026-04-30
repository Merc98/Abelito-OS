from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentMode:
    name: str
    description: str
    system_prompt: str
    capabilities: tuple[str, ...] = ()
    guardrails: tuple[str, ...] = ()


DECEPTICON_MODE = AgentMode(
    name="decepticon",
    description=(
        "Modo táctico de red-team adaptado para planificación autónoma, "
        "encadenamiento por fases y mejora defensiva continua."
    ),
    system_prompt=(
        "You are Decepticon mode for Abelito OS. "
        "Operate as a disciplined autonomous red-team planner: build mission packages, "
        "work in explicit phases, minimize assumptions, and convert each finding into "
        "defensive hardening actions. Never exceed authorized scope."
    ),
    capabilities=(
        "mission_package_generation",
        "phase_based_execution",
        "context_aware_reasoning",
        "defensive_feedback_loop",
    ),
    guardrails=(
        "authorized_scope_only",
        "human_approval_for_high_risk_steps",
        "legal_and_policy_compliance_required",
    ),
)


DEFAULT_MODE = AgentMode(
    name="default",
    description="Modo generalista de Abelito para tareas multipropósito.",
    system_prompt="You are Abelito OS assistant. Be helpful, accurate, and action-oriented.",
    capabilities=("general_assistance",),
)


_MODES: dict[str, AgentMode] = {
    DEFAULT_MODE.name: DEFAULT_MODE,
    DECEPTICON_MODE.name: DECEPTICON_MODE,
}


def list_modes() -> list[dict[str, Any]]:
    return [
        {
            "name": mode.name,
            "description": mode.description,
            "capabilities": list(mode.capabilities),
            "guardrails": list(mode.guardrails),
        }
        for mode in _MODES.values()
    ]


def get_mode(name: str | None) -> AgentMode:
    if not name:
        return DEFAULT_MODE
    key = name.strip().lower()
    if key not in _MODES:
        raise KeyError(f"Unknown mode '{name}'. Available: {list(_MODES.keys())}")
    return _MODES[key]


def build_decepticon_engagement_package(
    *,
    objective: str,
    authorized_scope: list[str],
    constraints: list[str] | None = None,
    threat_profile: str = "adaptive adversary simulation",
) -> dict[str, Any]:
    constraints = constraints or []
    return {
        "roe": {
            "objective": objective,
            "authorized_scope": authorized_scope,
            "constraints": constraints,
            "require_human_approval": True,
        },
        "conops": {
            "threat_profile": threat_profile,
            "methodology": "phase_based_red_team",
            "kill_chain": [
                "reconnaissance",
                "initial_access",
                "privilege_escalation",
                "lateral_movement",
                "objective_actions",
                "cleanup_and_reporting",
            ],
        },
        "deconfliction": {
            "window_required": True,
            "escalation_contact_required": True,
            "shared_safety_code_required": True,
        },
        "opplan": {
            "success_criteria": [
                "demonstrate security gap with evidence",
                "map each finding to a defensive control",
                "produce remediation backlog with priority",
            ],
            "reporting": "continuous + final summary",
        },
    }
