"""MCP Bridge — Connects ABEL OS+ to external tools and data via the Model Context Protocol."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger("abel.mcp")

class MCPBridge:
    """Client for interacting with multiple MCP servers."""

    def __init__(self, config_path: str = ".codex/config.toml"):
        self._sessions: Dict[str, ClientSession] = {}
        self._server_params: Dict[str, StdioServerParameters] = {}
        self._config_path = config_path
        self._load_config()

    def _load_config(self) -> None:
        """Load MCP server configs from TOML."""
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
                        env=cfg.get("env")
                    )
                    logger.info(f"Auto-registered MCP server: {name}")
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")

    async def register_server(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None) -> None:
        """Register an MCP server configuration."""
        self._server_params[name] = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        logger.info(f"Registered MCP server: {name}")

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Connect to a server and call a specific tool."""
        if server_name not in self._server_params:
            raise KeyError(f"Server '{server_name}' not registered")

        params = self._server_params[server_name]
        
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                logger.debug(f"Calling tool {tool_name} on {server_name}")
                result = await session.call_tool(tool_name, arguments)
                return result

    async def list_tools(self, server_name: str) -> List[Any]:
        """List all tools available on a specific server."""
        if server_name not in self._server_params:
            raise KeyError(f"Server '{server_name}' not registered")

        params = self._server_params[server_name]
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return result.tools

def setup():
    return MCPBridge()
