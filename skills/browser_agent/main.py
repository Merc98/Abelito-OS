"""Browser Agent Skill — For multi-step interactions."""
from __future__ import annotations

import os
import aiohttp
from typing import Any, Dict, List, Optional

NAVIGATOR_URL = os.getenv("NAVIGATOR_URL", "http://localhost:8001")

class BrowserAgentSkill:
    """Agentic browser control, building on top of the Navigator service."""

    async def execute_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a browser action like click, type, or scroll.
        Note: Currently restricted to read-only navigation in Phase 1 setup.
        """
        # In a real implementation, this would send commands to the playwright instance session
        # For Phase 1, we treat it as an extension of navigation
        if action == "navigate":
            return await self.navigate(params.get("url", ""))
        return {"error": f"Action '{action}' not yet supported in restricted mode."}

    async def navigate(self, url: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            try:
                payload = {"url": url, "screenshot": True}
                async with session.post(f"{NAVIGATOR_URL}/v1/navigate", json=payload) as resp:
                    return await resp.json()
            except Exception as e:
                return {"error": str(e)}

def setup():
    return BrowserAgentSkill()
