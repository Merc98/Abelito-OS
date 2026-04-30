"""OpenAI-compatible provider (GPT-4o, o1, etc.)."""
from __future__ import annotations

import os
from typing import Any, AsyncIterator

from shared.providers.base import BaseProvider, ChatMessage, CompletionResponse


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI API and any OpenAI-compatible endpoint."""

    name = "openai"

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self._default_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self._client: Any = None

    def _ensure_client(self) -> Any:
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise RuntimeError(
                    "openai package not installed. Run: pip install openai"
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
        resp = await client.chat.completions.create(
            model=model or self._default_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        choice = resp.choices[0]
        return CompletionResponse(
            text=choice.message.content or "",
            model=resp.model,
            provider=self.name,
            usage={
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
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
        stream = await client.chat.completions.create(
            model=model or self._default_model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def healthcheck(self) -> bool:
        if not self.api_key:
            return False
        try:
            client = self._ensure_client()
            await client.models.list()
            return True
        except Exception:
            return False

    def available_models(self) -> list[str]:
        return ["gpt-4o", "gpt-4o-mini", "o1", "o1-mini", "gpt-4-turbo"]
