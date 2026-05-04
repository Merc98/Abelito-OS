from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable


def _token_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _truncate_line(line: str, max_chars: int = 80) -> str:
    if len(line) <= max_chars:
        return line
    return line[: max_chars - 3] + "..."


def response_compressor(data: str | Iterable[str], max_tokens: int = 2000) -> str:
    """Compress verbose outputs without external APIs.

    Heuristics:
    - Remove duplicate lines while preserving order.
    - Truncate very long values per line.
    - Keep first lines + interesting error/warning/traceback lines.
    - Fall back to shape summary when still too large.
    """
    if isinstance(data, str):
        raw_lines = data.splitlines()
    else:
        raw_lines = [str(x) for x in data]

    seen: set[str] = set()
    deduped: list[str] = []
    for line in raw_lines:
        normalized = line.rstrip("\n")
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(_truncate_line(normalized))

    interesting_rx = re.compile(r"error|warn|exception|traceback|failed|fatal", re.IGNORECASE)
    interesting = [ln for ln in deduped if interesting_rx.search(ln)]
    head_n = 120
    output = deduped[:head_n]

    for ln in interesting:
        if ln not in output:
            output.append(ln)

    text = "\n".join(output)
    if _token_count(text) <= max_tokens:
        return text

    # Hard trim by token budget approximation.
    approx_chars = max_tokens * 4
    trimmed = text[:approx_chars]
    if _token_count(trimmed) <= max_tokens:
        return trimmed

    # Final shape summary.
    total = len(deduped)
    counter = Counter()
    for ln in deduped:
        if "/" in ln or "\\" in ln:
            if ln.endswith("/") or ln.endswith("\\"):
                counter["directories"] += 1
            elif "." in ln.split("/")[-1].split("\\")[-1]:
                counter["files"] += 1
        if interesting_rx.search(ln):
            counter["interesting"] += 1

    return (
        f"Compressed summary: {total} unique lines, "
        f"{counter['files']} files, {counter['directories']} directories, "
        f"{counter['interesting']} error/warning lines."
    )
