from __future__ import annotations

import asyncio
import hashlib
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import aiohttp
from bs4 import BeautifulSoup

from core.response_compressor import response_compressor


class AsyncWebSearch:
    def __init__(self, cache_path: str = ".agent/web_cache.json", ttl_seconds: int = 86400) -> None:
        self.cache_path = Path(cache_path)
        self.ttl_seconds = ttl_seconds
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()

    def _load_cache(self) -> dict[str, Any]:
        if self.cache_path.exists():
            try:
                return json.loads(self.cache_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self) -> None:
        self.cache_path.write_text(json.dumps(self.cache), encoding="utf-8")

    def _cache_key(self, query: str, engines: list[str]) -> str:
        raw = f"{query}|{','.join(sorted(engines))}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def _fetch_with_retry(self, session: aiohttp.ClientSession, url: str, proxy: str | None) -> str:
        delay = 0.5
        for _ in range(4):
            try:
                async with session.get(url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                    if resp.status < 400:
                        return await resp.text()
            except Exception:
                pass
            await asyncio.sleep(delay)
            delay *= 2
        return ""

    def _normalize(self, engine: str, items: list[dict[str, str]]) -> list[dict[str, str]]:
        out = []
        for it in items:
            out.append(
                {
                    "engine": engine,
                    "title": it.get("title", "").strip(),
                    "url": it.get("url", "").strip(),
                    "snippet": it.get("snippet", "").strip(),
                }
            )
        return out

    def _parse_generic(self, html: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict[str, str]] = []
        for a in soup.select("a")[:120]:
            href = a.get("href", "")
            title = a.get_text(" ", strip=True)
            if href.startswith("http") and title:
                snippet = ""
                parent = a.find_parent()
                if parent:
                    snippet = parent.get_text(" ", strip=True)
                results.append({"title": title, "url": href, "snippet": snippet[:220]})
        return results[:10]

    async def _search_engine(self, session: aiohttp.ClientSession, engine: str, query: str, proxy: str | None) -> list[dict[str, str]]:
        q = quote_plus(query)
        urls = {
            "bing": f"https://www.bing.com/search?q={q}",
            "yahoo": f"https://search.yahoo.com/search?p={q}",
            "startpage": f"https://www.startpage.com/sp/search?query={q}",
            "aol": f"https://search.aol.com/aol/search?q={q}",
        }
        url = urls.get(engine)
        if not url:
            return []
        html = await self._fetch_with_retry(session, url, proxy)
        if not html:
            return []
        return self._normalize(engine, self._parse_generic(html))

    async def web_search(self, query: str, engines: list[str] | None = None) -> list[dict[str, str]]:
        engines = engines or ["bing", "yahoo", "startpage", "aol"]
        key = self._cache_key(query, engines)
        now = time.time()
        cached = self.cache.get(key)
        if cached and now - cached.get("ts", 0) < self.ttl_seconds:
            return cached.get("results", [])

        proxy = None
        import os

        proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")

        headers = {"User-Agent": "Mozilla/5.0 (compatible; AbelitoBot/1.0)"}
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = [self._search_engine(session, eng, query, proxy) for eng in engines]
            chunks = await asyncio.gather(*tasks, return_exceptions=True)

        merged: list[dict[str, str]] = []
        for chunk in chunks:
            if isinstance(chunk, Exception):
                continue
            merged.extend(chunk)

        # Deduplicate by URL.
        dedup: dict[str, dict[str, str]] = {}
        for row in merged:
            if row.get("url"):
                dedup[row["url"]] = row

        results = list(dedup.values())[:30]
        # Enforce compressed shape for large return paths.
        compressed = response_compressor(json.dumps(results, ensure_ascii=False, indent=2), max_tokens=2000)
        self.cache[key] = {"ts": now, "results": results, "compressed": compressed}
        self._save_cache()
        return results
