"""OpenRouter provider — access hundreds of models via a single API key."""
from __future__ import annotations

import os
from typing import Any, AsyncIterator

from shared.providers.base import BaseProvider, ChatMessage, CompletionResponse


class OpenRouterProvider(BaseProvider):
    """Provider for OpenRouter.ai — routes to any model in their catalog."""

    name = "openrouter"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self._base_url = "https://openrouter.ai/api/v1"
        self._default_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")
        self._client: Any = None

    def _ensure_client(self) -> Any:
        """Reuse the openai SDK pointed at OpenRouter's endpoint."""
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self._base_url,
                    default_headers={
                        "HTTP-Referer": "https://abel-os.dev",
                        "X-Title": "ABEL OS+",
                    },
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
        return [
            "openai/gpt-4o",
            "anthropic/claude-sonnet-4-20250514",
            "google/gemini-2.5-pro",
            "meta-llama/llama-3-70b-instruct",
            "mistralai/mistral-large",
        ]
