"""MCP Helpers Skill — Dynamically integrate free AI helper tools via MCP."""
from typing import Any, Dict, List, Optional
from shared.mcp.client import MCPBridge

class MCPHelpersSkill:
    def __init__(self):
        self.bridge = MCPBridge()
        # Pre-configured free helpers (assuming standard names/commands)
        # Note: In a real scenario, these would be installed via npm/pip
        self.registered_servers = []

    async def connect_helper(self, name: str, command: str, args: List[str]) -> str:
        """Register and initialize a new helper tool."""
        try:
            await self.bridge.register_server(name, command, args)
            self.registered_servers.append(name)
            return f"Successfully connected to helper: {name}"
        except Exception as e:
            return f"Failed to connect helper {name}: {str(e)}"

    async def list_available_helpers(self, name: str) -> List[Any]:
        """List what tools a specific helper provides."""
        return await self.bridge.list_tools(name)

    async def use_helper(self, helper_name: str, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool from a specific helper."""
        return await self.bridge.call_tool(helper_name, tool_name, args)

def setup():
    return MCPHelpersSkill()
