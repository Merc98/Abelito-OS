"""Navigation Engine: Advanced web navigation and information extraction."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urljoin, urlparse

import structlog
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page

logger = structlog.get_logger()


@dataclass
class NavigationResult:
    """Result of a navigation and extraction operation."""
    url: str
    title: str
    content: str
    links: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    screenshots: list[bytes] = field(default_factory=list)
    success: bool = True
    error: str | None = None


@dataclass
class ExtractionRule:
    """Rule for extracting specific information."""
    name: str
    selector: str
    attribute: str | None = None
    transform: Literal["text", "html", "attribute", "regex"] = "text"
    pattern: str | None = None
    multiple: bool = False


class NavigationEngine:
    """Advanced web navigation with intelligent extraction."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.extraction_rules: list[ExtractionRule] = []
        self.visited_urls: set[str] = set()
        self.session_data: dict[str, Any] = {}
    
    async def start(self) -> None:
        """Start the browser."""
        playwright = await async_playwright.start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = await context.new_page()
        logger.info("Browser started")
    
    async def stop(self) -> None:
        """Stop the browser."""
        if self.browser:
            await self.browser.close()
        logger.info("Browser stopped")
    
    async def navigate(self, url: str, wait_for: str | None = None, timeout: int = 30000) -> NavigationResult:
        """Navigate to a URL and extract basic information."""
        if not self.page:
            await self.start()
        
        try:
            logger.info(f"Navigating to {url}")
            
            # Handle cookies/session if available
            if self.session_data.get("cookies"):
                await self.page.context.add_cookies(self.session_data["cookies"])
            
            response = await self.page.goto(url, wait_until="networkidle", timeout=timeout)
            
            if wait_for:
                await self.page.wait_for_selector(wait_for, timeout=timeout)
            
            # Extract content
            title = await self.page.title()
            html = await self.page.content()
            soup = BeautifulSoup(html, "lxml")
            
            # Get text content
            for script in soup(["script", "style"]):
                script.decompose()
            content = soup.get_text(separator="\n", strip=True)
            
            # Get links
            links = []
            for link in soup.find_all("a", href=True):
                href = urljoin(url, link["href"])
                if href.startswith("http") and href not in self.visited_urls:
                    links.append(href)
            
            # Get images
            images = []
            for img in soup.find_all("img", src=True):
                src = urljoin(url, img["src"])
                images.append(src)
            
            # Get metadata
            metadata = {}
            meta_tags = soup.find_all("meta")
            for tag in meta_tags:
                if tag.get("name"):
                    metadata[tag["name"]] = tag.get("content", "")
                elif tag.get("property"):
                    metadata[tag["property"]] = tag.get("content", "")
            
            self.visited_urls.add(url)
            
            result = NavigationResult(
                url=url,
                title=title,
                content=content[:50000],  # Limit content size
                links=links[:100],
                images=images[:50],
                metadata=metadata,
                success=response.status_code < 400 if response else True,
            )
            
            logger.info(f"Navigation complete: {title}")
            return result
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return NavigationResult(
                url=url,
                title="",
                content="",
                success=False,
                error=str(e),
            )
    
    async def extract_with_rules(self, url: str, rules: list[ExtractionRule]) -> dict[str, Any]:
        """Extract specific data using rules."""
        result = await self.navigate(url)
        if not result.success:
            return {"error": result.error}
        
        extracted = {}
        soup = BeautifulSoup(await self.page.content(), "lxml")
        
        for rule in rules:
            try:
                elements = soup.select(rule.selector)
                
                if rule.multiple:
                    values = []
                    for elem in elements:
                        value = self._extract_value(elem, rule)
                        if value:
                            values.append(value)
                    extracted[rule.name] = values
                else:
                    if elements:
                        extracted[rule.name] = self._extract_value(elements[0], rule)
                    else:
                        extracted[rule.name] = None
            except Exception as e:
                logger.warning(f"Rule {rule.name} failed: {e}")
                extracted[rule.name] = None
        
        return extracted
    
    def _extract_value(self, element, rule: ExtractionRule) -> Any:
        """Extract value from element based on rule."""
        if rule.transform == "text":
            return element.get_text(strip=True)
        elif rule.transform == "html":
            return str(element)
        elif rule.transform == "attribute" and rule.attribute:
            return element.get(rule.attribute)
        elif rule.transform == "regex" and rule.pattern:
            import re
            text = element.get_text(strip=True)
            match = re.search(rule.pattern, text)
            return match.group(1) if match else None
        return element.get_text(strip=True)
    
    async def take_screenshot(self, full_page: bool = True) -> bytes:
        """Take a screenshot of the current page."""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        return await self.page.screenshot(full_page=full_page)
    
    async def fill_form(self, selectors: dict[str, str]) -> None:
        """Fill form fields."""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        for selector, value in selectors.items():
            await self.page.fill(selector, value)
    
    async def click(self, selector: str) -> None:
        """Click an element."""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        await self.page.click(selector)
    
    async def scroll_to_bottom(self) -> None:
        """Scroll to bottom of page (useful for infinite scroll)."""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
    
    async def infinite_scroll(self, max_scrolls: int = 10) -> int:
        """Perform infinite scroll and return number of scrolls."""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        scrolls = 0
        previous_height = 0
        
        for _ in range(max_scrolls):
            current_height = await self.page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                break
            
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            previous_height = current_height
            scrolls += 1
        
        return scrolls
    
    def save_session(self, path: str = "./data/browser_session.json") -> None:
        """Save session cookies and data."""
        if not self.page:
            return
        
        cookies = self.page.context.cookies()
        self.session_data["cookies"] = cookies
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.session_data, f)
        
        logger.info(f"Session saved to {path}")
    
    def load_session(self, path: str = "./data/browser_session.json") -> bool:
        """Load session cookies and data."""
        path_obj = Path(path)
        if not path_obj.exists():
            return False
        
        with open(path_obj) as f:
            self.session_data = json.load(f)
        
        logger.info(f"Session loaded from {path}")
        return True


class InfoExtractor:
    """Specialized information extraction from web content."""
    
    def __init__(self):
        self.navigation = NavigationEngine()
    
    async def extract_osint(self, target: str, target_type: str) -> dict[str, Any]:
        """Extract OSINT information about a target."""
        results = {}
        
        if target_type == "email":
            results = await self._extract_email_osint(target)
        elif target_type == "username":
            results = await self._extract_username_osint(target)
        elif target_type == "domain":
            results = await self._extract_domain_osint(target)
        
        return results
    
    async def _extract_email_osint(self, email: str) -> dict[str, Any]:
        """Extract information about an email."""
        # Would integrate with breach databases, social media, etc.
        return {
            "email": email,
            "sources_checked": ["haveibeenpwned", "social_media", "public_records"],
            "findings": [],
        }
    
    async def _extract_username_osint(self, username: str) -> dict[str, Any]:
        """Check username across platforms."""
        platforms = [
            f"https://github.com/{username}",
            f"https://twitter.com/{username}",
            f"https://www.linkedin.com/in/{username}",
        ]
        
        found = []
        for url in platforms:
            result = await self.navigation.navigate(url)
            if result.success and "not found" not in result.content.lower():
                found.append(url)
        
        return {
            "username": username,
            "found_on": found,
        }
    
    async def _extract_domain_osint(self, domain: str) -> dict[str, Any]:
        """Extract domain information."""
        result = await self.navigation.navigate(f"https://{domain}")
        
        return {
            "domain": domain,
            "title": result.title,
            "technologies": [],  # Would use Wappalyzer-like detection
            "subdomains": [],
        }
    
    async def close(self):
        await self.navigation.stop()


async def main():
    """Demo navigation and extraction."""
    print("\n=== ABELITO OS NAVIGATION ENGINE ===\n")
    
    nav = NavigationEngine(headless=True)
    
    try:
        await nav.start()
        
        # Navigate and extract
        result = await nav.navigate("https://example.com")
        
        print(f"URL: {result.url}")
        print(f"Title: {result.title}")
        print(f"Content length: {len(result.content)} chars")
        print(f"Links found: {len(result.links)}")
        print(f"Images found: {len(result.images)}")
        print(f"Success: {result.success}")
        
        # Define extraction rules
        rules = [
            ExtractionRule(
                name="heading",
                selector="h1",
                transform="text",
            ),
            ExtractionRule(
                name="links",
                selector="a",
                transform="text",
                multiple=True,
            ),
        ]
        
        extracted = await nav.extract_with_rules("https://example.com", rules)
        print(f"\nExtracted data: {json.dumps(extracted, indent=2)}")
        
    finally:
        await nav.stop()


if __name__ == "__main__":
    asyncio.run(main())
