from __future__ import annotations

import unittest
import uuid

from fastapi import HTTPException

from apps.ceo_api import main as ceo_api
from apps.osint_orchestrator.pipeline import run_osint, validate_request
from core.memory import MemoryCore
from shared.schemas import CEOMessage, OsintRequest


class FakeNATS:
    def __init__(self) -> None:
        self.messages: list[tuple[str, bytes]] = []

    async def publish(self, subject: str, payload: bytes) -> None:
        self.messages.append((subject, payload))


class TestPipelineAndAPI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        ceo_api._nats = FakeNATS()
        ceo_api._memory = MemoryCore("./data/test_pipeline_api.db")

    async def test_validate_request_rejects_invalid_email(self) -> None:
        req = OsintRequest(
            target="not-an-email",
            target_type="email",
            purpose="audit",
            consent_or_legal_basis="consent",
            mode="RECOMMEND_ONLY",
        )
        result = validate_request(req)
        self.assertFalse(result.ok)

    async def test_run_osint_records_events_for_workflow(self) -> None:
        workflow_id = f"wf-test-{uuid.uuid4()}"
        req = OsintRequest(
            target="example.com",
            target_type="domain",
            purpose="security_assessment",
            consent_or_legal_basis="authorized_assessment",
            mode="RECOMMEND_ONLY",
        )
        report = await run_osint(req, workflow_id=workflow_id)
        self.assertEqual(report.status, "SUCCESS_PARTIAL_SUFFICIENT")

        snapshot = MemoryCore("./data/abel_memory.db").reconstruct_workflow(workflow_id)
        self.assertGreaterEqual(len(snapshot["events"]), 2)

    async def test_start_osint_blocks_sensitive_auto_mode(self) -> None:
        req = OsintRequest(
            target="+15551234567",
            target_type="phone",
            purpose="investigation",
            consent_or_legal_basis="legal_order",
            mode="AUTO",
        )
        with self.assertRaises(HTTPException):
            await ceo_api.start_osint(req)

    async def test_ingest_message_publishes_task(self) -> None:
        msg = CEOMessage(user_id="u1", text="hola")
        result = await ceo_api.ingest_message(msg)
        self.assertTrue(result.accepted)
        self.assertEqual(result.status, "QUEUED")
        assert ceo_api._nats is not None
        self.assertEqual(ceo_api._nats.messages[0][0], "abel.tasks.request.operations")

    async def test_dashboard_file_is_available(self) -> None:
        response = await ceo_api.dashboard()
        # Use Path.parts for cross-platform compatibility (Windows uses backslashes)
        from pathlib import Path
        parts = Path(response.path).parts
        self.assertIn("dashboard", parts)
        self.assertEqual(parts[-1], "index.html")


if __name__ == "__main__":
    unittest.main()
