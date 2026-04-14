"""
Multi-Agent Worker orchestration for ABEL OS+.
Registers different specialist workers and loops them concurrently over NATS.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from .intent_logger import IntentLogger

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """Manages pool of specialized agents receiving NATS tasks simultaneously."""

    def __init__(self, nats_client: Any, intents: IntentLogger) -> None:
        self.nats = nats_client
        self.intents = intents
        self._running = False
        self.agents = {}

    def register_agent(self, role: str, subject_pattern: str, handler_func: Any) -> None:
        """Register a specific agent matching a NATS prefix."""
        self.agents[role] = {
            "topic": subject_pattern,
            "handler": handler_func
        }

    async def _wrapped_handler(self, msg: Any, role: str, handler: Any) -> None:
        """Wrapper adding intent logging and error capture for every action."""
        payload = json.loads(msg.data.decode("utf-8"))
        workflow_id = payload.get("workflow_id", "unknown_wf")

        self.intents.log_intent(
            workflow_id=workflow_id,
            agent_role=role,
            target_action=msg.subject,
            reasoning=f"Agent {role} handling incoming task from {msg.subject}",
            context_payload=payload
        )

        try:
            result = await handler(payload)
            response_payload = {
                "status": "completed",
                "result": result
            }
            if msg.reply: # If standard NATS Req/Res was used
                await msg.respond(json.dumps(response_payload).encode())
        except Exception as e:
            logger.error(f"[{role}] Execution failed: {e}")
            if msg.reply:
                await msg.respond(json.dumps({"status": "failed", "error": str(e)}).encode())

    async def start(self) -> None:
        if not self.nats:
            logger.error("NATS client missing. Cannot start MultiAgent orchestrator.")
            return

        self._running = True
        logger.info("Initializing specialized agents...")

        for role, conf in self.agents.items():
            # Use partials or closures to pass role downward
            async def make_closure(role_name: str, handler_func: Any):
                async def closure(msg: Any):
                    await self._wrapped_handler(msg, role_name, handler_func)
                return closure
            
            cb = await make_closure(role, conf["handler"])
            await self.nats.subscribe(conf["topic"], cb=cb)
            logger.info(f"Registered Agent: [{role}] listening on '{conf['topic']}'")

        while self._running:
            await asyncio.sleep(1)

    def stop(self) -> None:
        self._running = False

