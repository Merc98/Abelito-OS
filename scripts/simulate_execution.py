from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.ceo_api import main as ceo_api
from apps.osint_orchestrator.pipeline import run_osint
from core.memory import MemoryCore
from shared.nats_client import connect_nats_with_retry
from shared.schemas import CEOMessage, OsintRequest


class FakeNATS:
    def __init__(self) -> None:
        self.messages: list[tuple[str, bytes]] = []
        self.is_connected = True

    async def publish(self, subject: str, payload: bytes) -> None:
        self.messages.append((subject, payload))

    async def close(self) -> None:
        self.is_connected = False


async def simulate_ceo_api_flow() -> None:
    ceo_api._nats = FakeNATS()
    ceo_api._memory = MemoryCore("./data/simulate_execution.db")

    msg = CEOMessage(user_id="tester", text="hola abel")
    response = await ceo_api.ingest_message(msg)
    assert response.accepted is True
    assert response.status == "QUEUED"
    assert ceo_api._nats.messages[0][0] == "abel.tasks.request.operations"

    osint_req = OsintRequest(
        target="jane.doe@example.com",
        target_type="email",
        purpose="due_diligence",
        consent_or_legal_basis="contract",
        mode="RECOMMEND_ONLY",
    )
    osint_response = await ceo_api.start_osint(osint_req)
    assert osint_response.accepted is True
    assert osint_response.status == "QUEUED"
    assert ceo_api._nats.messages[3][0] == "abel.tasks.short.osint.start"

    snapshot = await ceo_api.memory_snapshot(osint_response.workflow_id)
    assert snapshot["workflow_id"] == osint_response.workflow_id


async def simulate_pipeline_flow() -> None:
    db_path = "./data/abel_memory.db"
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    workflow_id = "wf-simulated-run"
    req = OsintRequest(
        target="example.com",
        target_type="domain",
        purpose="security_assessment",
        consent_or_legal_basis="authorized_assessment",
        mode="RECOMMEND_ONLY",
    )
    report = await run_osint(req, workflow_id=workflow_id)
    assert report.status == "SUCCESS_PARTIAL_SUFFICIENT"

    memory = MemoryCore(db_path)
    snapshot = memory.reconstruct_workflow(workflow_id)
    assert len(snapshot["events"]) >= 2


async def simulate_retry_helper() -> None:
    import shared.nats_client as nats_client_module

    class FlakyNATS:
        attempts = 0

        async def connect(self, _url: str) -> None:
            FlakyNATS.attempts += 1
            if FlakyNATS.attempts < 3:
                raise RuntimeError("temporary failure")

    original_nats_cls = nats_client_module.NATS
    nats_client_module.NATS = FlakyNATS  # type: ignore[assignment]
    try:
        client = await connect_nats_with_retry("nats://fake:4222", attempts=3, delay_s=0.01)
        assert isinstance(client, FlakyNATS)
    finally:
        nats_client_module.NATS = original_nats_cls  # type: ignore[assignment]


async def main() -> None:
    await simulate_ceo_api_flow()
    await simulate_pipeline_flow()
    await simulate_retry_helper()
    print("simulation_ok")


if __name__ == "__main__":
    asyncio.run(main())
