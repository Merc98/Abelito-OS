"""Auto Module Processor — pipeline generico de transformacion de datos."""
from __future__ import annotations

import json
import re
from typing import Any


def _flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            result.update(_flatten(v, f"{prefix}{k}."))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            result.update(_flatten(v, f"{prefix}{i}."))
    else:
        result[prefix.rstrip(".")] = obj
    return result


def _sanitize(obj: Any) -> Any:
    if isinstance(obj, str):
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", obj).strip()
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


async def process(data: Any) -> Any:
    """Pipeline principal:
    1. Deserializa JSON si llega como string.
    2. Sanitiza strings.
    3. Devuelve el objeto procesado con metadatos.
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            data = {"raw": data}
    data = _sanitize(data)
    return {
        "processed": True,
        "data": data,
        "flat": _flatten(data) if isinstance(data, dict) else {},
    }
