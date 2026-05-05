"""Shodan query wrapper — consulta la API real de Shodan."""
from __future__ import annotations

import importlib
import os
from typing import Any


def _get_api() -> tuple[Any | None, str | None]:
    api_key = os.getenv("SHODAN_API_KEY", "")
    if not api_key:
        return None, "SHODAN_API_KEY env var not set"
    try:
        shodan = importlib.import_module("shodan")
        return shodan.Shodan(api_key), None
    except ModuleNotFoundError:
        return None, "shodan not installed — run: pip install shodan"
    except Exception as exc:
        return None, str(exc)


def host_info(ip: str) -> dict[str, Any]:
    api, err = _get_api()
    if err:
        return {"error": err}
    try:
        h = api.host(ip)
        return {
            "ip": h["ip_str"], "org": h.get("org", "n/a"), "os": h.get("os", "n/a"),
            "ports": h.get("ports", []), "country": h.get("country_name", "n/a"),
            "hostnames": h.get("hostnames", []), "vulns": list(h.get("vulns", {}).keys()),
        }
    except Exception as exc:
        return {"error": str(exc)}


def search(query: str, limit: int = 10) -> dict[str, Any]:
    api, err = _get_api()
    if err:
        return {"error": err}
    try:
        r = api.search(query, limit=limit)
        return {
            "total": r["total"],
            "matches": [{"ip": m["ip_str"], "port": m.get("port"), "org": m.get("org", "n/a"), "data": m.get("data", "")[:300]} for m in r.get("matches", [])],
        }
    except Exception as exc:
        return {"error": str(exc)}
