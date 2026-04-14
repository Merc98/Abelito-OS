"""Tests for the upgraded Memory Core and Recall Skill."""
from __future__ import annotations

import os
import shutil
import unittest
from pathlib import Path
from core.memory import MemoryCore
from skills.__loader__ import registry

class TestMemoryUpgrade(unittest.TestCase):
    def setUp(self):
        import uuid
        self.db_path = f"./data/test_memory_upgrade_{uuid.uuid4().hex}.db"
        self.memory = MemoryCore(self.db_path)

    def test_store_and_search_knowledge(self):
        # Store some knowledge
        self.memory.store_knowledge(
            category="coding",
            content="Python is a multi-paradigm programming language.",
            tags=["python", "coding"]
        )
        self.memory.store_knowledge(
            category="coding",
            content="FastAPI is a modern web framework for building APIs.",
            tags=["fastapi", "web"]
        )
        
        # Search for knowledge
        results = self.memory.search_knowledge("FastAPI")
        self.assertGreater(len(results), 0)
        self.assertIn("FastAPI", results[0]["content"])
        self.assertEqual(results[0]["category"], "coding")

    def test_recall_skill_integration(self):
        skill = registry.load_skill("memory_recall")
        self.assertIsNotNone(skill)
        
        # Store via skill
        resp = skill.store("ABEL OS+ is a high-capability AI operating system.", category="general")
        self.assertIn("id", resp)
        
        # Search via skill
        results = skill.search("ABEL OS+")
        self.assertGreater(len(results), 0)
        self.assertIn("high-capability", results[0]["content"])

if __name__ == "__main__":
    unittest.main()
