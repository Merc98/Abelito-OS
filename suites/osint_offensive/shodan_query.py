from __future__ import annotations
import os
import httpx

def shodan_search(query: str) -> dict:
    key = os.getenv("SHODAN_API_KEY", "")
    if not key:
        raise RuntimeError("SHODAN_API_KEY not configured")
    r = httpx.get("https://api.shodan.io/shodan/host/search", params={"key": key, "query": query}, timeout=20)
    r.raise_for_status()
    return r.json()
