"""MCP Bridge — lazy server activation via ToolGateway."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from core.tool_gateway import ToolGateway

logger = logging.getLogger("abel.mcp")


class MCPBridge:
    """Client for interacting with MCP servers with explicit lazy activation."""

    def __init__(self, config_path: str = ".codex/config.toml"):
        self._server_params: Dict[str, StdioServerParameters] = {}
        self._config_path = config_path
        self.gateway = ToolGateway()
        self._load_config()

    def _load_config(self) -> None:
        import tomllib
        from pathlib import Path

        path = Path(self._config_path)
        if not path.exists():
            logger.warning(f"Config not found: {self._config_path}")
            return

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
                servers = data.get("mcp", {}).get("servers", {})
                for name, cfg in servers.items():
                    self._server_params[name] = StdioServerParameters(
                        command=cfg["command"],
                        args=cfg.get("args", []),
                        env=cfg.get("env"),
                    )
                    # Register only metadata in gateway. Activation is explicit.
                    self.gateway.register_server(name, "shared.mcp.client", factory=None)
                    logger.info(f"Registered MCP server metadata: {name}")
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")

    async def register_server(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> None:
        self._server_params[name] = StdioServerParameters(command=command, args=args, env=env)
        self.gateway.register_server(name, "shared.mcp.client", factory=None)
        logger.info(f"Registered MCP server: {name}")

    def list_available_servers(self) -> List[str]:
        return self.gateway.list_available_servers()

    def activate_server(self, server_name: str) -> str:
        if server_name not in self._server_params:
            raise KeyError(f"Server '{server_name}' not registered")
        # For stdio MCP servers, activation means explicit opt-in state marker.
        self.gateway.activate_server(server_name)
        return server_name

    def deactivate_server(self, server_name: str) -> None:
        self.gateway.deactivate_server(server_name)

    async def invoke_tool(self, server: str, tool: str, params: Dict[str, Any]) -> Any:
        # Explicit activation required before invocation.
        if server not in self.gateway.list_available_servers():
            raise KeyError(f"Server '{server}' not registered")
        self.activate_server(server)

        server_params = self._server_params[server]
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(tool, params)

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        return await self.invoke_tool(server_name, tool_name, arguments)

    async def list_tools(self, server_name: str) -> List[Any]:
        self.activate_server(server_name)
        params = self._server_params[server_name]
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return result.tools


def setup():
    return MCPBridge()
