"""Abstract base class for all LLM providers in ABEL OS+."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass(frozen=True, slots=True)
class CompletionResponse:
    """Standardised response from any provider."""
    text: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)  # prompt_tokens, completion_tokens
    raw: dict[str, Any] = field(default_factory=dict)


class BaseProvider(ABC):
    """Every LLM provider must implement this interface."""

    name: str = "base"

    @abstractmethod
    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> CompletionResponse:
        """Send a chat completion request and return the full response."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream tokens from the provider. Yields text chunks."""
        ...
        # Make this an async generator to satisfy the type system
        yield ""  # pragma: no cover

    @abstractmethod
    async def healthcheck(self) -> bool:
        """Return True if the provider is reachable and configured."""
        ...

    def available_models(self) -> list[str]:
        """Return the list of model IDs this provider supports."""
        return []
