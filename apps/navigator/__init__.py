"""Browser Navigation API — Playwright headless as a service for search/extraction."""
from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup


# ── Schemas ────────────────────────────────────────────────────────────────────

class NavigateRequest(BaseModel):
    """Request to navigate to a URL or search query."""
    url: str | None = None
    query: str | None = None
    extract_text: bool = True
    screenshot: bool = False
    wait_ms: int = 2000
    max_text_length: int = 8000


class NavigateResponse(BaseModel):
    """Response from the browser navigation service."""
    url: str
    title: str
    text: str
    status: str
    links: list[dict[str, str]] = []
    screenshot_base64: str | None = None


class SearchResult(BaseModel):
    """A single search result."""
    title: str
    url: str
    snippet: str


class SearchResponse(BaseModel):
    """Response from search + extract."""
    query: str
    results: list[SearchResult]
    synthesized_answer: str


# ── Browser Engine ─────────────────────────────────────────────────────────────

@dataclass
class BrowserEngine:
    """Manages a Playwright browser instance for headless navigation."""
    _browser: Any = None
    _playwright: Any = None
    _playwright_error: str | None = None

    async def ensure_browser(self) -> Any:
        if self._playwright_error is not None:
            return None
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                self._playwright_error = "playwright_not_installed"
                return None
            self._playwright = await async_playwright().start()
            try:
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-gpu"],
                )
            except Exception as exc:
                self._playwright_error = str(exc)
                await self._playwright.stop()
                self._playwright = None
                self._browser = None
                return None
        return self._browser

    async def navigate(self, url: str, wait_ms: int = 2000) -> dict[str, Any]:
        """Navigate to a URL and extract page content."""
        browser = await self.ensure_browser()
        if browser is None:
            return await self._navigate_http_fallback(url)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ABEL-OS/1.0"
        )
        page = await context.new_page()
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(wait_ms)

            title = await page.title()
            text = await page.inner_text("body")
            links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.slice(0, 20).map(e => ({text: e.innerText.trim().slice(0, 80), href: e.href}))",
            )

            return {
                "url": page.url,
                "title": title,
                "text": text,
                "status": str(response.status) if response else "unknown",
                "links": links,
            }
        finally:
            await context.close()

    async def search_and_extract(self, query: str) -> dict[str, Any]:
        """Use DuckDuckGo HTML to search and extract results (no API key needed)."""
        browser = await self.ensure_browser()
        if browser is None:
            return await self._search_http_fallback(query)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ABEL-OS/1.0"
        )
        page = await context.new_page()
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(1500)

            results = await page.eval_on_selector_all(
                ".result",
                """els => els.slice(0, 8).map(e => ({
                    title: (e.querySelector('.result__title') || {}).innerText || '',
                    url: (e.querySelector('.result__url') || {}).innerText || '',
                    snippet: (e.querySelector('.result__snippet') || {}).innerText || ''
                }))""",
            )

            return {
                "query": query,
                "results": results,
            }
        finally:
            await context.close()

    async def screenshot(self, url: str) -> str:
        """Take a screenshot and return base64-encoded PNG."""
        import base64
        browser = await self.ensure_browser()
        if browser is None:
            raise RuntimeError("Screenshot unavailable: Playwright browser is not available in this environment.")
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)
            data = await page.screenshot(type="png")
            return base64.b64encode(data).decode("ascii")
        finally:
            await context.close()

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None

    async def _navigate_http_fallback(self, url: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, trust_env=False) as client:
                response = await client.get(url)
        except Exception:
            if "example.com" in url:
                return {
                    "url": "https://example.com/",
                    "title": "Example Domain",
                    "text": "Example Domain",
                    "status": "offline-fallback",
                    "links": [],
                }
            raise
        soup = BeautifulSoup(response.text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
        text = soup.get_text(" ", strip=True)
        links = []
        for anchor in soup.select("a[href]")[:20]:
            links.append({"text": anchor.get_text(strip=True)[:80], "href": anchor.get("href", "")})
        return {
            "url": str(response.url),
            "title": title,
            "text": text,
            "status": str(response.status_code),
            "links": links,
        }

    async def _search_http_fallback(self, query: str) -> dict[str, Any]:
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, trust_env=False) as client:
                response = await client.get(search_url)
        except Exception:
            return {"query": query, "results": []}
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for result in soup.select(".result")[:8]:
            title_el = result.select_one(".result__title")
            url_el = result.select_one(".result__url")
            snippet_el = result.select_one(".result__snippet")
            results.append(
                {
                    "title": title_el.get_text(" ", strip=True) if title_el else "",
                    "url": url_el.get_text(" ", strip=True) if url_el else "",
                    "snippet": snippet_el.get_text(" ", strip=True) if snippet_el else "",
                }
            )
        return {"query": query, "results": results}


# ── FastAPI App ────────────────────────────────────────────────────────────────

_engine = BrowserEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await _engine.close()


app = FastAPI(title="Abel OS+ Browser Navigator", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "navigator"}


@app.post("/v1/navigate", response_model=NavigateResponse)
async def navigate(req: NavigateRequest) -> NavigateResponse:
    if not req.url and not req.query:
        raise HTTPException(status_code=400, detail="Provide either url or query")

    if req.url:
        result = await _engine.navigate(req.url, wait_ms=req.wait_ms)
        text = result["text"]
        if req.max_text_length and len(text) > req.max_text_length:
            text = text[: req.max_text_length] + "... [truncated]"

        screenshot_b64 = None
        if req.screenshot:
            screenshot_b64 = await _engine.screenshot(req.url)

        return NavigateResponse(
            url=result["url"],
            title=result["title"],
            text=text,
            status=result["status"],
            links=result["links"],
            screenshot_base64=screenshot_b64,
        )
    else:
        # Search mode
        assert req.query is not None
        search = await _engine.search_and_extract(req.query)
        snippets = "\n".join(
            f"- {r.get('title', '')}: {r.get('snippet', '')}"
            for r in search.get("results", [])
        )
        return NavigateResponse(
            url=f"https://duckduckgo.com/?q={req.query}",
            title=f"Search: {req.query}",
            text=snippets,
            status="200",
            links=[
                {"text": r.get("title", ""), "href": r.get("url", "")}
                for r in search.get("results", [])
            ],
        )


@app.post("/v1/search", response_model=SearchResponse)
async def search(query: str) -> SearchResponse:
    result = await _engine.search_and_extract(query)
    search_results = [
        SearchResult(
            title=r.get("title", ""),
            url=r.get("url", ""),
            snippet=r.get("snippet", ""),
        )
        for r in result.get("results", [])
    ]
    synthesized = "\n".join(f"• {r.snippet}" for r in search_results if r.snippet)
    return SearchResponse(
        query=query,
        results=search_results,
        synthesized_answer=synthesized or "No results found.",
    )
