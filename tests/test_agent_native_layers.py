import asyncio

from core.memory_manager import MemoryManager
from core.response_compressor import response_compressor
from core.smart_search import SmartSearchEngine


def test_response_compressor_dedup_and_truncate():
    data = "line1\nline1\n" + ("x" * 120)
    out = response_compressor(data, max_tokens=2000)
    assert out.count("line1") == 1
    assert "..." in out


def test_smart_search_returns_snippets(tmp_path):
    (tmp_path / "a.py").write_text("def hello():\n    return 'ok'\n", encoding="utf-8")
    engine = SmartSearchEngine(str(tmp_path))
    hits = asyncio.run(engine.smart_search("hello function", mode="auto"))
    assert hits
    assert hits[0].path.endswith("a.py")
    assert "def hello" in hits[0].snippet


def test_memory_manager_learn_and_recall(tmp_path):
    db = tmp_path / "agent_memory.db"
    mm = MemoryManager(str(db))
    mm.learn(
        title="Auth convention",
        content="Always validate JWT before route handlers.",
        type="convention",
        files=["app/auth.py"],
        tags=["auth", "ghost"],
        confidence=0.9,
    )
    rows = asyncio.run(mm.recall("JWT validate", type="convention", mode="auto"))
    assert rows
    assert rows[0]["confidence"] >= 0.15
