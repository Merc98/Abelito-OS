"""Anthropic provider (Claude Sonnet, Opus, Haiku)."""
from __future__ import annotations

import os
from typing import Any, AsyncIterator

from shared.providers.base import BaseProvider, ChatMessage, CompletionResponse


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic's Claude models."""

    name = "anthropic"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self._default_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self._client: Any = None

    def _ensure_client(self) -> Any:
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                raise RuntimeError(
                    "anthropic package not installed. Run: pip install anthropic"
                )
        return self._client

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> CompletionResponse:
        client = self._ensure_client()
        # Anthropic separates system messages from the conversation
        system_text = ""
        chat_msgs = []
        for m in messages:
            if m.role == "system":
                system_text += m.content + "\n"
            else:
                chat_msgs.append({"role": m.role, "content": m.content})

        create_kwargs: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": chat_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }
        if system_text.strip():
            create_kwargs["system"] = system_text.strip()

        resp = await client.messages.create(**create_kwargs)
        text = resp.content[0].text if resp.content else ""
        return CompletionResponse(
            text=text,
            model=resp.model,
            provider=self.name,
            usage={
                "prompt_tokens": resp.usage.input_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.output_tokens if resp.usage else 0,
            },
            raw=resp.model_dump() if hasattr(resp, "model_dump") else {},
        )

    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        client = self._ensure_client()
        system_text = ""
        chat_msgs = []
        for m in messages:
            if m.role == "system":
                system_text += m.content + "\n"
            else:
                chat_msgs.append({"role": m.role, "content": m.content})

        create_kwargs: dict[str, Any] = {
            "model": model or self._default_model,
            "messages": chat_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }
        if system_text.strip():
            create_kwargs["system"] = system_text.strip()

        async with client.messages.stream(**create_kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def healthcheck(self) -> bool:
        if not self.api_key:
            return False
        try:
            client = self._ensure_client()
            # Minimal call to check connectivity
            await client.messages.create(
                model=self._default_model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False

    def available_models(self) -> list[str]:
        return [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-haiku-3-5-20241022",
        ]
