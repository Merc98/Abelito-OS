"""Tests for the Skills System."""
from __future__ import annotations

import unittest
import sys
import os
from pathlib import Path

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skills.__loader__ import registry

class TestSkills(unittest.TestCase):
    def test_discovery(self):
        # Should have at least 3 skills discovered
        available = registry.list_available()
        names = [s["name"] for s in available]
        self.assertIn("web_search", names)
        self.assertIn("browser_agent", names)
        self.assertIn("computer_use", names)

    def test_load_web_search(self):
        skill = registry.load_skill("web_search")
        self.assertIsNotNone(skill)
        self.assertTrue(hasattr(skill, "search"))

    def test_load_computer_use(self):
        skill = registry.load_skill("computer_use")
        self.assertIsNotNone(skill)
        # Check for core methods
        self.assertTrue(hasattr(skill, "get_screen_info"))

if __name__ == "__main__":
    unittest.main()
