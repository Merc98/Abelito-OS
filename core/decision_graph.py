"""
Decision Graph (Grafo de Decisiones) module for ABEL OS+.
Stores decision trees dynamically created by agents.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class DecisionGraph:
    """
    Persistent directed graph to store decision paths and outcomes.
    This helps the agent 'learn' which paths yield successful results.
    """

    def __init__(self, db_path: str = "./data/abel_memory.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decision_nodes (
                    id TEXT PRIMARY KEY,
                    context_hash TEXT NOT NULL,
                    state_desc TEXT NOT NULL,
                    metadata_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS decision_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_node_id TEXT NOT NULL,
                    to_node_id TEXT NOT NULL,
                    action_taken TEXT NOT NULL,
                    weight REAL DEFAULT 1.0, -- Representa el success rate o confidence
                    visits INTEGER DEFAULT 0,
                    FOREIGN KEY(from_node_id) REFERENCES decision_nodes(id),
                    FOREIGN KEY(to_node_id) REFERENCES decision_nodes(id)
                )
                """
            )

    def add_node(self, node_id: str, context_hash: str, state_desc: str, metadata: dict[str, Any] | None = None) -> None:
        """Register a state node in the decision layout."""
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO decision_nodes(id, context_hash, state_desc, metadata_json)
                VALUES (?, ?, ?, ?)
                """,
                (node_id, context_hash, state_desc, json.dumps(metadata or {}))
            )

    def register_transition(self, from_node: str, to_node: str, action: str, success: bool) -> None:
        """Record the transition between states and update the confidence weight."""
        with self._conn() as conn:
            # Check if edge exists
            edge = conn.execute(
                "SELECT id, weight, visits FROM decision_edges WHERE from_node_id=? AND to_node_id=? AND action_taken=?",
                (from_node, to_node, action)
            ).fetchone()

            if edge:
                current_weight = float(edge["weight"])
                visits = int(edge["visits"])
                new_visits = visits + 1
                
                # Simple exponential moving average roughly tracking success rate
                target = 1.0 if success else -1.0
                new_weight = current_weight + (0.1 * (target - current_weight))

                conn.execute(
                    "UPDATE decision_edges SET weight=?, visits=? WHERE id=?",
                    (new_weight, new_visits, edge["id"])
                )
            else:
                initial_weight = 1.0 if success else -1.0
                conn.execute(
                    """
                    INSERT INTO decision_edges(from_node_id, to_node_id, action_taken, weight, visits)
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (from_node, to_node, action, initial_weight)
                )

    def get_best_action(self, from_node: str) -> dict[str, Any] | None:
        """Query the graph for the historically best acting given a known node context."""
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT to_node_id, action_taken, weight, visits 
                FROM decision_edges 
                WHERE from_node_id=? 
                ORDER BY weight DESC, visits DESC 
                LIMIT 1
                """,
                (from_node,)
            ).fetchone()
            
            if row:
                return dict(row)
            return None
