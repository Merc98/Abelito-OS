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
