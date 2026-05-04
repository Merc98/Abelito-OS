from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any


@dataclass
class ServerSpec:
    module: str
    factory: str | None = None


class ToolGateway:
    """Lazy server loader: modules are imported only on explicit activation."""

    def __init__(self, server_registry: dict[str, ServerSpec] | None = None) -> None:
        self._registry: dict[str, ServerSpec] = server_registry or {}
        self._active: dict[str, Any] = {}

    def register_server(self, name: str, module: str, factory: str | None = None) -> None:
        self._registry[name] = ServerSpec(module=module, factory=factory)

    def list_available_servers(self) -> list[str]:
        return sorted(self._registry.keys())

    def activate_server(self, server_name: str) -> Any:
        if server_name in self._active:
            return self._active[server_name]
        if server_name not in self._registry:
            raise KeyError(f"Server '{server_name}' not registered")

        spec = self._registry[server_name]
        module = importlib.import_module(spec.module)
        instance: Any = module
        if spec.factory:
            factory = getattr(module, spec.factory)
            instance = factory()
        self._active[server_name] = instance
        return instance

    async def invoke_tool(self, server: str, tool: str, params: dict[str, Any]) -> Any:
        instance = self.activate_server(server)
        fn = getattr(instance, tool, None)
        if fn is None:
            raise AttributeError(f"Tool '{tool}' not found in server '{server}'")

        result = fn(**params)
        if hasattr(result, "__await__"):
            return await result
        return result

    def deactivate_server(self, server_name: str) -> None:
        if server_name in self._active:
            del self._active[server_name]
