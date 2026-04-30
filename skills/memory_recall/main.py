"""Memory Recall Skill — Accesses the upgraded Long-Term Memory."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from core.memory import MemoryCore

class MemoryRecallSkill:
    """Skill to store and retrieve long-term knowledge."""

    def __init__(self):
        db_path = os.getenv("MEMORY_DB_PATH", "./data/abel_memory.db")
        self.memory = MemoryCore(db_path)

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant knowledge chunks."""
        return self.memory.search_knowledge(query, limit=limit)

    def store(self, content: str, category: str = "general", tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Store a new piece of knowledge."""
        know_id = self.memory.store_knowledge(
            category=category,
            content=content,
            tags=tags
        )
        return {"id": know_id, "status": "stored"}

    def recall_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Reconstruct a past workflow's events."""
        return self.memory.reconstruct_workflow(workflow_id)

def setup():
    return MemoryRecallSkill()
