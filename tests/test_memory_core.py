from core.memory import MemoryCore


def test_record_and_reconstruct_workflow(tmp_path):
    db = tmp_path / "mem.db"
    mem = MemoryCore(str(db))

    mem.record_event("wf-1", "scan", "ok", {"k": 1})
    mem.record_failure("wf-1", "scan", "boom", "fp-1", {"x": True})

    snapshot = mem.reconstruct_workflow("wf-1")
    assert snapshot["workflow_id"] == "wf-1"
    assert len(snapshot["events"]) == 1
    assert snapshot["events"][0]["stage"] == "scan"
    assert snapshot["events"][0]["payload"] == {"k": 1}
    assert len(snapshot["failures"]) == 1
    assert snapshot["failures"][0]["fingerprint"] == "fp-1"


def test_store_and_search_knowledge(tmp_path):
    db = tmp_path / "mem.db"
    mem = MemoryCore(str(db))

    mem.store_knowledge("osint", "Grant opportunities for AI startups in EU", ["grants", "eu"], {"source": "demo"})
    results = mem.search_knowledge("Grant", limit=5)

    assert results
    assert results[0]["category"] == "osint"
    assert "grants" in results[0]["tags"]
