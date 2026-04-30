"""
Watchdog component for ABEL OS+. 
Runs a separate monitoring process/loop that checks for guardrail violations.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

class GuardrailsWatchdog:
    """
    Subscribes to all proposed actions before they are executed.
    Can send an abort signal to the NATS bus or memory core to halt workflows.
    """
    
    def __init__(self, nats_client: Any | None = None) -> None:
        self.nats = nats_client
        # Disallowed semantic intents or tool usage patterns
        self.forbidden_patterns = [
            "delete_all", "rm -rf /", "drop table", 
            "unauthorized_api_call", "crawl_internal_network"
        ]

    async def start(self) -> None:
        if not self.nats:
            logger.warning("Watchdog starting without NATS connection. Operating in passive mode.")
            return

        logger.info("Starting Guardrails Watchdog...")
        await self.nats.subscribe("abel.intents.*", cb=self._on_intent_detected)

    async def _on_intent_detected(self, msg: Any) -> None:
        """Analyze intent before passing it to execution."""
        try:
            payload = json.loads(msg.data.decode())
            intent = payload.get("intent", "").lower()
            workflow_id = payload.get("workflow_id", "unknown")
            
            # Simple keyword-based rules engine for the early version
            violation = any(pattern in intent for pattern in self.forbidden_patterns)
            
            if violation:
                logger.error(f"[WATCHDOG] Policy violation detected in workflow {workflow_id}: {intent}")
                # Emit a halt command to the specific agent or global killswitch channel
                await self.nats.publish(f"abel.control.halt.{workflow_id}", b"POLICY_VIOLATION")
                await msg.respond(b"DENIED")
            else:
                await msg.respond(b"APPROVED")
        except Exception as e:
            logger.error(f"Watchdog error processing message: {e}")
