from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from nats.aio.client import Client as NATS


@dataclass(frozen=True, slots=True)
class NATSRetryConfig:
    attempts: int = 30
    delay_s: float = 1.0


def retry_config_from_env() -> NATSRetryConfig:
    attempts = int(os.getenv("NATS_CONNECT_ATTEMPTS", "30"))
    delay_s = float(os.getenv("NATS_CONNECT_DELAY_S", "1.0"))
    if attempts < 1:
        raise ValueError("NATS_CONNECT_ATTEMPTS must be >= 1")
    if delay_s < 0:
        raise ValueError("NATS_CONNECT_DELAY_S must be >= 0")
    return NATSRetryConfig(attempts=attempts, delay_s=delay_s)


async def connect_nats_with_retry(
    url: str,
    *,
    attempts: int = 30,
    delay_s: float = 1.0,
) -> NATS:
    """Connect to NATS with bounded retries to survive startup races."""
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        client = NATS()
        try:
            await client.connect(url)
            return client
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == attempts:
                break
            await asyncio.sleep(delay_s)

    assert last_error is not None
    raise RuntimeError(
        f"failed to connect to NATS at {url} after {attempts} attempts"
    ) from last_error


async def connect_nats_from_env(url: str) -> NATS:
    config = retry_config_from_env()
    return await connect_nats_with_retry(
        url,
        attempts=config.attempts,
        delay_s=config.delay_s,
    )
