"""Tests for the Navigator service using Playwright."""
from __future__ import annotations

import asyncio
import unittest
import sys
from pathlib import Path

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

class TestNavigator(unittest.IsolatedAsyncioTestCase):
    async def test_search_and_extract(self):
        # We handle the import here to avoid failure at collection time if playwright is broken
        try:
            from apps.navigator import _engine
        except ImportError:
            self.fail("Could not import navigator engine")

        try:
            # We use a simple query that should return results
            # Note: This requires internet access
            result = await _engine.search_and_extract("Abel OS")
            self.assertIn("query", result)
            self.assertEqual(result["query"], "Abel OS")
            self.assertIsInstance(result["results"], list)
            
            # If we have internet, we should have results
            if len(result["results"]) > 0:
                self.assertTrue(any("Abel" in r["title"] or "Abel" in r["snippet"] for r in result["results"]))
        finally:
            await _engine.close()

    async def test_navigate(self):
        try:
            from apps.navigator import _engine
        except ImportError:
            self.fail("Could not import navigator engine")

        try:
            # Navigate to a simple stable page
            result = await _engine.navigate("https://example.com")
            self.assertEqual(result["title"], "Example Domain")
            self.assertIn("Example Domain", result["text"])
        finally:
            await _engine.close()

if __name__ == "__main__":
    unittest.main()
