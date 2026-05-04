from __future__ import annotations

import asyncio
import json
import math
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from core.smart_search import SmartSearchEngine


HALF_LIFE_DAYS = {
    "error_pattern": 30,
    "convention": None,
    "ghost_knowledge": 45,
}


class MemoryManager:
    def __init__(self, db_path: str = ".agent/agent_memory.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.search_engine = SmartSearchEngine(".")
        self.apply_confidence_decay()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT NOT NULL,
                    files_json TEXT,
                    tags_json TEXT,
                    confidence REAL NOT NULL,
                    embedding_json TEXT,
                    is_ghost INTEGER DEFAULT 0
                )
                """
            )
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(title, content, tags)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_relationships (
                    src_id INTEGER NOT NULL,
                    dst_id INTEGER NOT NULL,
                    relation TEXT NOT NULL,
                    PRIMARY KEY (src_id, dst_id, relation)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS recall_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    query TEXT NOT NULL,
                    hit_count INTEGER NOT NULL
                )
                """
            )

    def _embed(self, text: str) -> list[float]:
        return self.search_engine._embed(text)

    def learn(self, title: str, content: str, type: str, files: list[str], tags: list[str], confidence: float = 0.85) -> int:
        emb = self._embed(f"{title}\n{content}\n{' '.join(tags)}")
        is_ghost = 1 if "ghost" in tags or type == "ghost_knowledge" else 0
        with self._conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO memory_entries(ts, title, content, type, files_json, tags_json, confidence, embedding_json, is_ghost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (time.time(), title, content, type, json.dumps(files), json.dumps(tags), confidence, json.dumps(emb), is_ghost),
            )
            entry_id = cur.lastrowid or 0
            conn.execute(
                "INSERT INTO memory_fts(rowid, title, content, tags) VALUES (?, ?, ?, ?)",
                (entry_id, title, content, " ".join(tags)),
            )
            return entry_id

    def _is_path_query(self, query: str) -> bool:
        return "/" in query or "\\" in query or query.endswith((".py", ".js", ".ts", ".md"))

    def _strategy_path(self, query: str) -> list[tuple[int, float]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT id, files_json FROM memory_entries").fetchall()
        out: list[tuple[int, float]] = []
        for row in rows:
            files = json.loads(row["files_json"] or "[]")
            if any(query in f for f in files):
                out.append((row["id"], 1.0))
        return out

    def _strategy_fts(self, query: str) -> list[tuple[int, float]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT rowid FROM memory_fts WHERE memory_fts MATCH ? LIMIT 25",
                (query,),
            ).fetchall()
        return [(int(r["rowid"]), 1.0 - i * 0.02) for i, r in enumerate(rows)]

    def _strategy_graph(self, base_ids: list[int]) -> list[tuple[int, float]]:
        if not base_ids:
            return []
        qmarks = ",".join("?" for _ in base_ids)
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT dst_id FROM memory_relationships WHERE src_id IN ({qmarks}) LIMIT 25",
                tuple(base_ids),
            ).fetchall()
        return [(int(r["dst_id"]), 0.7) for r in rows]

    def _strategy_temporal(self, query: str) -> list[tuple[int, float]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT id, ts FROM memory_entries ORDER BY ts DESC LIMIT 50").fetchall()
        now = time.time()
        out = []
        for row in rows:
            age_days = (now - row["ts"]) / 86400
            score = 1 / (1 + age_days)
            out.append((int(row["id"]), score))
        return out

    def _strategy_semantic(self, query: str) -> list[tuple[int, float]]:
        qv = self._embed(query)
        with self._conn() as conn:
            rows = conn.execute("SELECT id, embedding_json FROM memory_entries LIMIT 500").fetchall()
        scored: list[tuple[int, float]] = []
        for row in rows:
            vec = json.loads(row["embedding_json"] or "[]")
            if not vec:
                continue
            sim = sum(a * b for a, b in zip(qv, vec))
            scored.append((int(row["id"]), float(sim)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:25]

    def _rrf(self, rankings: list[list[tuple[int, float]]], k: int = 60) -> list[tuple[int, float]]:
        fused: dict[int, float] = defaultdict(float)
        for ranking in rankings:
            for rank, (entry_id, _score) in enumerate(ranking, start=1):
                fused[entry_id] += 1 / (k + rank)
        return sorted(fused.items(), key=lambda x: x[1], reverse=True)

    async def recall(self, query: str, type: str | None = None, mode: str = "auto") -> list[dict[str, Any]]:
        path_rank = await asyncio.to_thread(self._strategy_path, query) if self._is_path_query(query) else []
        fts_rank = await asyncio.to_thread(self._strategy_fts, query)
        graph_rank = await asyncio.to_thread(self._strategy_graph, [x[0] for x in fts_rank[:10]])
        temporal_rank = await asyncio.to_thread(self._strategy_temporal, query)
        semantic_rank = await asyncio.to_thread(self._strategy_semantic, query)

        fused = self._rrf([path_rank, fts_rank, graph_rank, temporal_rank, semantic_rank])
        with self._conn() as conn:
            out: list[dict[str, Any]] = []
            for entry_id, score in fused:
                row = conn.execute("SELECT * FROM memory_entries WHERE id = ?", (entry_id,)).fetchone()
                if not row:
                    continue
                if type and row["type"] != type:
                    continue
                conf = float(row["confidence"])
                if row["is_ghost"]:
                    conf += 0.15
                if conf < 0.15:
                    continue
                out.append(
                    {
                        "id": entry_id,
                        "title": row["title"],
                        "content": row["content"],
                        "type": row["type"],
                        "files": json.loads(row["files_json"] or "[]"),
                        "tags": json.loads(row["tags_json"] or "[]"),
                        "confidence": conf,
                        "score": score,
                    }
                )
                if len(out) >= 20:
                    break
            conn.execute("INSERT INTO recall_logs(ts, query, hit_count) VALUES (?, ?, ?)", (time.time(), query, len(out)))
            return out

    def apply_confidence_decay(self) -> None:
        now = time.time()
        with self._conn() as conn:
            rows = conn.execute("SELECT id, ts, type, confidence FROM memory_entries").fetchall()
            for row in rows:
                half_life = HALF_LIFE_DAYS.get(row["type"], 60)
                if half_life is None:
                    continue
                age_days = (now - row["ts"]) / 86400
                decayed = float(row["confidence"]) * math.pow(0.5, age_days / half_life)
                conn.execute("UPDATE memory_entries SET confidence = ? WHERE id = ?", (decayed, row["id"]))

    def drift_detection(self) -> float:
        now = time.time()
        with self._conn() as conn:
            rows_7 = conn.execute(
                "SELECT hit_count FROM recall_logs WHERE ts >= ?",
                (now - 7 * 86400,),
            ).fetchall()
            rows_30 = conn.execute(
                "SELECT hit_count FROM recall_logs WHERE ts >= ?",
                (now - 30 * 86400,),
            ).fetchall()
        if not rows_30:
            return 0.0
        z7 = sum(1 for r in rows_7 if r["hit_count"] == 0) / max(1, len(rows_7))
        z30 = sum(1 for r in rows_30 if r["hit_count"] == 0) / max(1, len(rows_30))
        drift = z7 - z30
        return drift

    def self_heal_if_needed(self) -> bool:
        drift = self.drift_detection()
        if drift > 0.1:
            self.search_engine.reindex()
            return True
        return False

    def session_injection(self) -> dict[str, list[dict[str, Any]]]:
        with self._conn() as conn:
            ghosts = conn.execute(
                "SELECT * FROM memory_entries WHERE is_ghost = 1 ORDER BY confidence DESC LIMIT 10"
            ).fetchall()
            conventions = conn.execute(
                "SELECT * FROM memory_entries WHERE type = 'convention' ORDER BY confidence DESC LIMIT 5"
            ).fetchall()
        return {
            "ghost_knowledge": [dict(r) for r in ghosts],
            "conventions": [dict(r) for r in conventions],
        }
