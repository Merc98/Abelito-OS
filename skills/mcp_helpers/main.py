"""MCP Helpers Skill — lazy MCP activation via ToolGateway-backed bridge."""
from typing import Any, Dict, List

from shared.mcp.client import MCPBridge


class MCPHelpersSkill:
    def __init__(self):
        self.bridge = MCPBridge()
        self.registered_servers: list[str] = []

    async def connect_helper(self, name: str, command: str, args: List[str]) -> str:
        try:
            await self.bridge.register_server(name, command, args)
            self.registered_servers.append(name)
            return f"Successfully connected to helper: {name}"
        except Exception as e:
            return f"Failed to connect helper {name}: {str(e)}"

    async def list_available_helpers(self) -> List[str]:
        return self.bridge.list_available_servers()

    async def activate_helper(self, name: str) -> str:
        self.bridge.activate_server(name)
        return f"Activated: {name}"

    async def use_helper(self, helper_name: str, tool_name: str, args: Dict[str, Any]) -> Any:
        return await self.bridge.invoke_tool(helper_name, tool_name, args)

    async def deactivate_helper(self, name: str) -> str:
        self.bridge.deactivate_server(name)
        return f"Deactivated: {name}"


def setup():
    return MCPHelpersSkill()
