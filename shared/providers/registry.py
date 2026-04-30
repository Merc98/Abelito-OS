"""Dynamic provider registry — select, switch, and manage active LLM providers."""
from __future__ import annotations

import os
from typing import Any

from shared.providers.base import BaseProvider, ChatMessage, CompletionResponse


class ProviderRegistry:
    """Central registry for all available LLM providers.

    The active provider can be switched at runtime without restart.
    """

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._active_name: str = ""

    def register(self, provider: BaseProvider) -> None:
        """Register a provider instance by its name."""
        self._providers[provider.name] = provider
        if not self._active_name:
            self._active_name = provider.name

    def set_active(self, name: str) -> None:
        """Switch the active provider by name."""
        if name not in self._providers:
            raise KeyError(
                f"Provider '{name}' not registered. Available: {list(self._providers.keys())}"
            )
        self._active_name = name

    @property
    def active(self) -> BaseProvider:
        """Return the currently active provider."""
        if not self._active_name or self._active_name not in self._providers:
            raise RuntimeError("No active provider configured.")
        return self._providers[self._active_name]

    @property
    def active_name(self) -> str:
        return self._active_name

    def list_providers(self) -> list[dict[str, Any]]:
        """Return metadata about all registered providers."""
        return [
            {
                "name": p.name,
                "active": p.name == self._active_name,
                "models": p.available_models(),
            }
            for p in self._providers.values()
        ]

    async def healthcheck_all(self) -> dict[str, bool]:
        """Run healthcheck on every registered provider."""
        results: dict[str, bool] = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.healthcheck()
            except Exception:
                results[name] = False
        return results


def build_default_registry() -> ProviderRegistry:
    """Auto-configure providers from environment variables.

    Only providers with valid credentials/access are registered.
    """
    registry = ProviderRegistry()

    # OpenAI
    if os.getenv("OPENAI_API_KEY"):
        from shared.providers.openai import OpenAIProvider
        registry.register(OpenAIProvider())

    # Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        from shared.providers.anthropic import AnthropicProvider
        registry.register(AnthropicProvider())

    # OpenRouter
    if os.getenv("OPENROUTER_API_KEY"):
        from shared.providers.openrouter import OpenRouterProvider
        registry.register(OpenRouterProvider())

    # Ollama — always register since it's local and free
    from shared.providers.ollama import OllamaProvider
    registry.register(OllamaProvider())

    # Set active from env if specified
    preferred = os.getenv("ABEL_LLM_PROVIDER", "")
    if preferred and preferred in [p.name for p in registry._providers.values()]:
        registry.set_active(preferred)

    return registry
