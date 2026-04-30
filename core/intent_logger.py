"""
Intent Logger for ABEL OS+.
Serializes and stores in memory the reasoning / step-by-step logic 
a worker uses BEFORE it performs an action, enabling audits and rollbacks.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from .memory import MemoryCore

logger = logging.getLogger(__name__)


class IntentLogger:
    """Logs serialized reasoning before an action occurs."""

    def __init__(self, memory_core: MemoryCore) -> None:
        self.memory = memory_core

    def log_intent(
        self,
        workflow_id: str,
        agent_role: str,
        target_action: str,
        reasoning: str,
        context_payload: dict[str, Any] | None = None
    ) -> None:
        """
        Records *why* an action is taken.
        Logs to both console and Durable Memory.
        """
        log_payload = {
            "type": "INTENT",
            "agent_role": agent_role,
            "target_action": target_action,
            "reasoning": reasoning,
            "context": context_payload or {}
        }
        
        logger.info(f"[{agent_role}] INTENT -> {target_action}: {reasoning}")
        
        # Persist the intent in the knowledge base or an events table
        self.memory.record_event(
            workflow_id=workflow_id,
            stage=f"INTENT_{target_action.upper()}",
            status="LOGGED",
            payload=log_payload
        )

