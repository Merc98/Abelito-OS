"""
Observation-Action Loop (Monitor) for ABEL OS+.
Continuously polls the local runtime state to issue autonomous tasks if things misbehave.
"""
from __future__ import annotations

import asyncio
import logging
import psutil
from typing import Any

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    Observer loop. Checks CPU, Memory, or external service health.
    If it detects an anomaly, it can auto-trigger 'Fix it' tasks in NATS.
    """

    def __init__(self, nats_client: Any | None = None, check_interval: int = 60) -> None:
        self.nats = nats_client
        self.check_interval = check_interval
        self._running = False

    async def start(self) -> None:
        """Start the observation loop."""
        self._running = True
        logger.info(f"System monitor started. Checking every {self.check_interval}s.")
        asyncio.create_task(self._loop())

    def stop(self) -> None:
        self._running = False

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._check_system()
            except Exception as e:
                logger.error(f"Error in observation loop: {e}")
            await asyncio.sleep(self.check_interval)

    async def _check_system(self) -> None:
        # Example metric: CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()

        logger.debug(f"[MONITOR] CPU: {cpu_percent}%, Mem: {mem.percent}%")

        if cpu_percent > 90 or mem.percent > 90:
            logger.warning("[MONITOR] High resource usage detected! Generating corrective OSINT task.")
            if self.nats:
                import json
                task_payload = {
                    "source": "system_monitor",
                    "issue": "HighResourceUsage",
                    "metrics": {
                        "cpu": cpu_percent,
                        "memory": mem.percent
                    },
                    "action_required": "investigate_and_restart"
                }
                await self.nats.publish("abel.tasks.system.autoheal", json.dumps(task_payload).encode())
