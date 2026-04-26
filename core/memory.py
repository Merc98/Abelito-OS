from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class MemoryCore:
    """Durable memory core for workflow events/failures and lightweight reconstruction."""

    def __init__(self, db_path: str = "./data/abel_memory.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    workflow_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    workflow_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    error TEXT NOT NULL,
                    fingerprint TEXT,
                    payload_json TEXT
                )
                """
            )
            # ── Long-Term Memory (LTM) ──────────────────────────────────────────
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT,
                    metadata_json TEXT
                )
                """
            )
            # Create FTS5 virtual table for lightning search
            try:
                conn.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_search USING fts5(content, tokenize='porter')"
                )
            except sqlite3.OperationalError:
                # FTS5 might not be available in some environments, fallback to basic indexing
                pass
            
            # ── Vector Episodic Memory (sqlite-vec) ─────────────────────────
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS episodic_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    workflow_id TEXT,
                    content TEXT NOT NULL,
                    metadata_json TEXT
                )
                """
            )
            # Intentar inicializar la tabla de vectores si sqlite-vec está cargado
            try:
                conn.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS episodic_vectors USING vec0(rowid INTEGER PRIMARY KEY, embedding float[1536])"
                )
            except sqlite3.OperationalError:
                pass


    def record_event(
        self,
        workflow_id: str,
        stage: str,
        status: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO workflow_events(ts, workflow_id, stage, status, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (time.time(), workflow_id, stage, status, json.dumps(payload or {})),
            )

    def record_failure(
        self,
        workflow_id: str,
        stage: str,
        error: str,
        fingerprint: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO workflow_failures(ts, workflow_id, stage, error, fingerprint, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    workflow_id,
                    stage,
                    error,
                    fingerprint,
                    json.dumps(payload or {}),
                ),
            )

    def reconstruct_workflow(self, workflow_id: str) -> dict[str, Any]:
        with self._conn() as conn:
            events = conn.execute(
                """
                SELECT ts, stage, status, payload_json
                FROM workflow_events
                WHERE workflow_id = ?
                ORDER BY ts ASC
                """,
                (workflow_id,),
            ).fetchall()
            failures = conn.execute(
                """
                SELECT ts, stage, error, fingerprint, payload_json
                FROM workflow_failures
                WHERE workflow_id = ?
                ORDER BY ts ASC
                """,
                (workflow_id,),
            ).fetchall()

        return {
            "workflow_id": workflow_id,
            "events": [
                {
                    "ts": row["ts"],
                    "stage": row["stage"],
                    "status": row["status"],
                    "payload": json.loads(row["payload_json"] or "{}"),
                }
                for row in events
            ],
            "failures": [
                {
                    "ts": row["ts"],
                    "stage": row["stage"],
                    "error": row["error"],
                    "fingerprint": row["fingerprint"],
                    "payload": json.loads(row["payload_json"] or "{}"),
                }
                for row in failures
            ],
        }

    def store_knowledge(
        self,
        category: str,
        content: str,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        ts = time.time()
        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO knowledge_base(ts, category, content, tags, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ts, category, content, ",".join(tags or []), json.dumps(metadata or {})),
            )
            # Update FTS index
            try:
                conn.execute(
                    "INSERT INTO knowledge_search(rowid, content) VALUES (?, ?)",
                    (cursor.lastrowid, content)
                )
            except sqlite3.OperationalError:
                pass
            return cursor.lastrowid or 0

    def search_knowledge(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        with self._conn() as conn:
            # Try FTS5 search first
            try:
                rows = conn.execute(
                    """
                    SELECT kb.id, kb.ts, kb.category, kb.content, kb.tags, kb.metadata_json
                    FROM knowledge_base kb
                    JOIN knowledge_search ks ON kb.id = ks.rowid
                    WHERE knowledge_search MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (query, limit),
                ).fetchall()
            except sqlite3.OperationalError:
                # Fallback to basic LIKE search
                rows = conn.execute(
                    """
                    SELECT id, ts, category, content, tags, metadata_json
                    FROM knowledge_base
                    WHERE content LIKE ? OR category LIKE ?
                    ORDER BY ts DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", f"%{query}%", limit),
                ).fetchall()

        return [
            {
                "id": row["id"],
                "ts": row["ts"],
                "category": row["category"],
                "content": row["content"],
                "tags": (row["tags"] or "").split(",") if row["tags"] else [],
                "metadata": json.loads(row["metadata_json"] or "{}"),
            }
            for row in rows
        ]
    def find_recent_failure_fingerprint(self, fingerprint: str, limit: int = 5) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT ts, workflow_id, stage, error
                FROM workflow_failures
                WHERE fingerprint = ?
                ORDER BY ts DESC
                LIMIT ?
                """,
                (fingerprint, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    # ── Episodic/Vector API ─────────────────────────────────────────────────

    def store_episode(
        self,
        workflow_id: str,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Stores an episodic memory with its vector embedding."""
        ts = time.time()
        with self._conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO episodic_records(ts, workflow_id, content, metadata_json)
                VALUES (?, ?, ?, ?)
                """,
                (ts, workflow_id, content, json.dumps(metadata or {})),
            )
            row_id = cursor.lastrowid
            
            try:
                # Store the vector embedding with precisely the matching rowid
                conn.execute(
                    "INSERT INTO episodic_vectors(rowid, embedding) VALUES (?, ?)",
                    (row_id, json.dumps(embedding))
                )
            except sqlite3.OperationalError:
                pass # Extensión sqlite-vec no cargada o configuración incorrecta
                
            return row_id or 0

    def semantic_search(self, query_embedding: list[float], limit: int = 5) -> list[dict[str, Any]]:
        """Finds most similar episodes using KNN on sqlite-vec. Returns content and distance."""
        with self._conn() as conn:
            try:
                rows = conn.execute(
                    """
                    SELECT 
                        r.id, r.ts, r.workflow_id, r.content, r.metadata_json,
                        distance
                    FROM episodic_vectors v
                    JOIN episodic_records r ON v.rowid = r.id
                    WHERE embedding MATCH ? AND k = ?
                    ORDER BY distance
                    """,
                    (json.dumps(query_embedding), limit)
                ).fetchall()
            except sqlite3.OperationalError:
                # Fallback if no vec extension
                return []
                
        return [
            {
                "id": row["id"],
                "ts": row["ts"],
                "workflow_id": row["workflow_id"],
                "content": row["content"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
                "distance": row["distance"]
            }
            for row in rows
        ]
