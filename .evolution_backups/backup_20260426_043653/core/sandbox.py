from __future__ import annotations

import asyncio
from typing import Awaitable, TypeVar

T = TypeVar("T")


async def run_in_sandbox(task: Awaitable[T], timeout_s: float = 2.0) -> T:
    """Isolated async boundary with timeout; raises TimeoutError on overrun."""
    return await asyncio.wait_for(task, timeout=timeout_s)
