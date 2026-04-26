from __future__ import annotations

import asyncio
import os
import unittest
from unittest.mock import patch

import shared.nats_client as nats_client


class TestNATSClient(unittest.IsolatedAsyncioTestCase):
    async def test_connect_retry_recovers_after_transient_failures(self) -> None:
        class FlakyNATS:
            attempts = 0

            async def connect(self, _url: str) -> None:
                FlakyNATS.attempts += 1
                if FlakyNATS.attempts < 3:
                    raise RuntimeError("temporary failure")

        with patch.object(nats_client, "NATS", FlakyNATS):
            client = await nats_client.connect_nats_with_retry(
                "nats://fake:4222",
                attempts=4,
                delay_s=0.01,
            )
        self.assertIsInstance(client, FlakyNATS)

    async def test_connect_retry_raises_after_exhausting_attempts(self) -> None:
        class AlwaysFailNATS:
            async def connect(self, _url: str) -> None:
                raise RuntimeError("down")

        with patch.object(nats_client, "NATS", AlwaysFailNATS):
            with self.assertRaises(RuntimeError):
                await nats_client.connect_nats_with_retry(
                    "nats://fake:4222",
                    attempts=2,
                    delay_s=0.0,
                )

    def test_retry_config_from_env(self) -> None:
        with patch.dict(
            os.environ,
            {"NATS_CONNECT_ATTEMPTS": "5", "NATS_CONNECT_DELAY_S": "0.25"},
            clear=False,
        ):
            cfg = nats_client.retry_config_from_env()
        self.assertEqual(cfg.attempts, 5)
        self.assertAlmostEqual(cfg.delay_s, 0.25)


if __name__ == "__main__":
    unittest.main()
