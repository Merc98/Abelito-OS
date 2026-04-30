"""
Task Scheduler (Planificador) for ABEL OS+.
Handles CRON-like tasks execution independently of human interaction.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    Maintains a list of cron jobs and dispatches them via NATS.
    In a complete setup, this would use APScheduler or similar logic 
    to handle exact timings and cron expressions.
    """

    def __init__(self, nats_client: Any | None = None) -> None:
        self.nats = nats_client
        self.jobs = []
        self._running = False

    def add_job(self, cron_expr: str, task_channel: str, payload: dict[str, Any]) -> None:
        """Add a recurring job. (Dummy simplified wait logic)."""
        self.jobs.append({
            "schedule": cron_expr, # E.g., 'every_5_mins'
            "channel": task_channel,
            "payload": payload,
            "last_run": 0
        })

    async def start(self) -> None:
        self._running = True
        logger.info("Task Scheduler started.")
        asyncio.create_task(self._loop())

    def stop(self) -> None:
        self._running = False

    async def _loop(self) -> None:
        while self._running:
            now = time.time()
            for job in self.jobs:
                # Dummy trigger logic. Assume 'every_5_mins' triggers if diff > 300
                # In production, integrate APScheduler.
                if job["schedule"] == "every_5_mins" and now - job["last_run"] >= 300:
                    logger.info(f"[SCHEDULER] Dispatching autonomous job to {job['channel']}")
                    if self.nats:
                        await self.nats.publish(job["channel"], json.dumps(job["payload"]).encode())
                    job["last_run"] = now

            await asyncio.sleep(10) # Tick rate

