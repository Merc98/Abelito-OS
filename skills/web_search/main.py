"""Web Search Skill — Interacts with the Navigator service."""
from __future__ import annotations

import os
import aiohttp
from typing import Any, Dict, List, Optional

NAVIGATOR_URL = os.getenv("NAVIGATOR_URL", "http://localhost:8001")

class WebSearchSkill:
    """Skill to perform web searches and extraction via the navigator service."""

    async def search(self, query: str) -> Dict[str, Any]:
        """Perform a search and return synthesized results."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{NAVIGATOR_URL}/v1/search", params={"query": query}) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {"error": f"Navigator error: {resp.status}", "detail": error_text}
                    return await resp.json()
            except Exception as e:
                return {"error": str(e)}

    async def extract(self, url: str) -> Dict[str, Any]:
        """Extract full text from a specific URL."""
        async with aiohttp.ClientSession() as session:
            try:
                payload = {"url": url, "extract_text": True}
                async with session.post(f"{NAVIGATOR_URL}/v1/navigate", json=payload) as resp:
                    if resp.status != 200:
                        return {"error": f"Navigator error: {resp.status}"}
                    return await resp.json()
            except Exception as e:
                return {"error": str(e)}

def setup():
    return WebSearchSkill()
