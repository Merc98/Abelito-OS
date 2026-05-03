from __future__ import annotations
import asyncio
import json
from typing import Any, Callable
from nats.aio.client import Client as NATS

class EventBus:
    def __init__(self, url: str = "nats://localhost:4222"):
        self.url = url
        self.nc = NATS()

    async def connect(self) -> None:
        if not self.nc.is_connected:
            await self.nc.connect(servers=[self.url], connect_timeout=2)

    async def publish(self, subject: str, payload: dict[str, Any]) -> None:
        await self.connect()
        await self.nc.publish(subject, json.dumps(payload).encode())

    async def subscribe(self, subject: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        await self.connect()
        async def _cb(msg):
            data = json.loads(msg.data.decode())
            out = handler(data)
            if asyncio.iscoroutine(out):
                await out
        await self.nc.subscribe(subject, cb=_cb)

    async def close(self) -> None:
        if self.nc.is_connected:
            await self.nc.close()
