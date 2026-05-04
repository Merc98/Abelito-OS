from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.agent_skeleton import AgentSkeleton
from core.memory_manager import MemoryManager
from core.response_compressor import response_compressor
from core.smart_search import SmartSearchEngine
from core.web_search import AsyncWebSearch


class NativeTools:
    def __init__(self, root: str = ".") -> None:
        self.root = Path(root)
        self.search = SmartSearchEngine(str(self.root))
        self.memory = MemoryManager(str(self.root / ".agent" / "agent_memory.db"))
        self.web = AsyncWebSearch(str(self.root / ".agent" / "web_cache.json"))
        self.skeleton = AgentSkeleton(str(self.root))

    async def smart_search(self, query: str, mode: str = "auto") -> list[dict[str, str]]:
        hits = await self.search.smart_search(query, mode=mode)
        return [asdict(h) for h in hits]

    async def web_search(self, query: str, engines: list[str] | None = None) -> list[dict[str, str]]:
        return await self.web.web_search(query, engines=engines)

    def learn(self, title: str, content: str, type: str, files: list[str], tags: list[str], confidence: float = 0.85) -> int:
        return self.memory.learn(title, content, type, files, tags, confidence)

    async def recall(self, query: str, type: str | None = None, mode: str = "auto") -> list[dict[str, Any]]:
        return await self.memory.recall(query=query, type=type, mode=mode)

    def agent_setup(self) -> dict[str, str]:
        return self.skeleton.agent_setup()

    async def agent_deploy(self, base_url: str = "http://127.0.0.1:8080", log_path: str = "./logs/server.log") -> dict[str, Any]:
        import httpx

        checks: dict[str, Any] = {
            "/auth/login": False,
            "/health": False,
            "server_log": False,
            "provider_log": False,
        }

        async with httpx.AsyncClient(timeout=6.0) as client:
            for route in ("/auth/login", "/health"):
                try:
                    resp = await client.get(f"{base_url}{route}")
                    checks[route] = resp.status_code == 200
                except Exception:
                    checks[route] = False

        try:
            log_text = Path(log_path).read_text(encoding="utf-8", errors="ignore") if Path(log_path).exists() else ""
        except OSError:
            log_text = ""

        checks["server_log"] = "Server running" in log_text
        provider_identity = os.getenv("AI_PROVIDER", "")
        checks["provider_log"] = bool(provider_identity) and provider_identity in log_text

        status = "passed" if all(checks.values()) else "failed"
        return {"status": status, "checks": checks, "compressed_log": response_compressor(log_text, 2000)}

    async def agent_customize(self, feature_desc: str, base_url: str = "http://127.0.0.1:8080", log_path: str = "./logs/server.log") -> dict[str, Any]:
        capture = self.skeleton.agent_customize(feature_desc)
        gate = await self.agent_deploy(base_url=base_url, log_path=log_path)
        return {"capture": capture, "deploy_gate": gate}

    def compress(self, data: str, max_tokens: int = 2000) -> str:
        return response_compressor(data, max_tokens=max_tokens)
