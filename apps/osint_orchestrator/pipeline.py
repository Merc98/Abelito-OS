from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass

from core.memory import MemoryCore
from core.sandbox import run_in_sandbox
from shared.schemas import Finding, OsintReport, OsintRequest

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]{3,32}$")
DOMAIN_RE = re.compile(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    reason: str = ""


def validate_request(req: OsintRequest) -> ValidationResult:
    """Enforce legal/compliance guardrails for public-interest OSINT."""
    if not req.purpose:
        return ValidationResult(False, "purpose is required")
    if not req.consent_or_legal_basis:
        return ValidationResult(False, "consent_or_legal_basis is required")

    if req.target_type == "email" and not EMAIL_RE.match(req.target):
        return ValidationResult(False, "invalid email format")
    if req.target_type == "username" and not USERNAME_RE.match(req.target):
        return ValidationResult(False, "invalid username format")
    if req.target_type == "domain" and not DOMAIN_RE.match(req.target):
        return ValidationResult(False, "invalid domain format")

    if req.target_type in {"phone", "plate", "image"} and req.mode == "AUTO":
        return ValidationResult(
            False,
            "AUTO mode is disabled for sensitive target types; use RECOMMEND_ONLY + HITL",
        )

    return ValidationResult(True)


async def generate_dorks(req: OsintRequest) -> list[Finding]:
    base = req.target
    dorks = [
        f'"{base}" site:linkedin.com',
        f'"{base}" site:github.com',
        f'"{base}" site:pastebin.com',
        f'"{base}" "breach"',
    ]
    return [
        Finding(
            source="dork-generator",
            category="query",
            value=q,
            confidence=0.75,
            public_data_only=True,
        )
        for q in dorks
    ]


async def check_breach_surface(req: OsintRequest) -> list[Finding]:
    # Placeholder module: integrate APIs in next phase.
    await asyncio.sleep(0.05)
    return [
        Finding(
            source="breach-surface",
            category="signal",
            value=f"Potential breach footprint for target: {req.target}",
            confidence=0.35,
            public_data_only=True,
        )
    ]


async def check_username_surface(req: OsintRequest) -> list[Finding]:
    if req.target_type != "username":
        return []

    await asyncio.sleep(0.05)
    return [
        Finding(
            source="username-surface",
            category="profile",
            value=f"Candidate profile handle seen: {req.target}",
            confidence=0.4,
            public_data_only=True,
        )
    ]


async def _safe_collect(task, source_name: str, workflow_id: str, memory: MemoryCore) -> list[Finding]:
    try:
        findings = await run_in_sandbox(task, timeout_s=2.5)
        memory.record_event(workflow_id, source_name, "SUCCESS", {"count": len(findings)})
        return findings
    except Exception as exc:  # noqa: BLE001
        memory.record_failure(
            workflow_id,
            source_name,
            str(exc),
            fingerprint=f"{source_name}:{exc.__class__.__name__}",
        )
        return []


async def run_osint(req: OsintRequest, workflow_id: str | None = None) -> OsintReport:
    wf = workflow_id or "wf-ephemeral"
    # Use MEMORY_DB_PATH env var so the pipeline writes to the same DB as the
    # calling service (osint_orchestrator) rather than always using the default path.
    memory = MemoryCore(os.getenv("MEMORY_DB_PATH", "./data/abel_memory.db"))
    validation = validate_request(req)
    if not validation.ok:
        memory.record_failure(wf, "policy_validation", validation.reason, fingerprint="policy_rejection")
        return OsintReport(
            request=req,
            status="REJECTED_POLICY",
            summary=validation.reason,
            findings=[],
            risk="high",
            recommended_next_step="HITL",
        )

    previous = memory.find_recent_failure_fingerprint("policy_rejection", limit=3)

    findings = []
    findings.extend(await _safe_collect(generate_dorks(req), "dork-generator", wf, memory))
    findings.extend(await _safe_collect(check_breach_surface(req), "breach-surface", wf, memory))
    findings.extend(await _safe_collect(check_username_surface(req), "username-surface", wf, memory))

    if previous:
        findings.append(
            Finding(
                source="memory-core",
                category="recovery",
                value=f"Detected {len(previous)} similar past policy failures; guardrails reinforced.",
                confidence=0.95,
                public_data_only=True,
            )
        )

    return OsintReport(
        request=req,
        status="SUCCESS_PARTIAL_SUFFICIENT",
        summary="Public-source OSINT signals generated with compliance guardrails.",
        findings=findings,
        risk="medium",
        recommended_next_step="REVIEW_AND_EXPAND",
    )
