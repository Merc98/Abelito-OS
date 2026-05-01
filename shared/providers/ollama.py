"""Ollama provider — free local models (Llama3, Mistral, Qwen, etc.)."""
from __future__ import annotations

import os
from typing import Any, AsyncIterator

import aiohttp

from shared.providers.base import BaseProvider, ChatMessage, CompletionResponse


class OllamaProvider(BaseProvider):
    """Provider for Ollama local inference server."""

    name = "ollama"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self._default_model = os.getenv("OLLAMA_MODEL", "llama3")

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> CompletionResponse:
        payload = {
            "model": model or self._default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()

        return CompletionResponse(
            text=data.get("message", {}).get("content", ""),
            model=data.get("model", model or self._default_model),
            provider=self.name,
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
            raw=data,
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
        payload = {
            "model": model or self._default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        import json
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.content:
                    decoded = line.decode("utf-8").strip()
                    if not decoded:
                        continue
                    chunk = json.loads(decoded)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content

    async def healthcheck(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def available_models(self) -> list[str]:
        return ["llama3", "llama3:70b", "mistral", "qwen2", "codellama", "phi3"]
