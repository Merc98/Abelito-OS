"""
Watchdog component for ABEL OS+.
Passive observer mode — logs intent activity, never blocks execution.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class GuardrailsWatchdog:
    """
    Passive observer. Subscribes to all proposed actions and logs them.
    Does NOT block or deny any execution.
    """

    def __init__(self, nats_client: Any | None = None) -> None:
        self.nats = nats_client

    async def start(self) -> None:
        if not self.nats:
            logger.warning("Watchdog starting without NATS connection. Operating in passive mode.")
            return

        logger.info("Starting Guardrails Watchdog (passive/observe-only mode)...")
        await self.nats.subscribe("abel.intents.*", cb=self._on_intent_detected)

    async def _on_intent_detected(self, msg: Any) -> None:
        """Log intent and always approve execution."""
        try:
            payload = json.loads(msg.data.decode())
            intent = payload.get("intent", "")
            workflow_id = payload.get("workflow_id", "unknown")
            logger.debug(f"[WATCHDOG] Intent observed — workflow={workflow_id}, intent={intent}")
            await msg.respond(b"APPROVED")
        except Exception as e:
            logger.error(f"Watchdog error processing message: {e}")
