"""Tests for auth layer and provider registry."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.auth import Role, UserStore, create_token, verify_token
from shared.providers.base import ChatMessage, CompletionResponse
from shared.providers.registry import ProviderRegistry, build_default_registry


class TestAuth(unittest.TestCase):
    def test_create_and_verify_token(self) -> None:
        token = create_token("abel", Role.ADMIN)
        payload = verify_token(token)
        self.assertEqual(payload.user_id, "abel")
        self.assertEqual(payload.role, Role.ADMIN)

    def test_expired_token_is_rejected(self) -> None:
        token = create_token("abel", Role.OPERATOR, expiry_s=-1)
        with self.assertRaises(ValueError):
            verify_token(token)

    def test_tampered_token_is_rejected(self) -> None:
        token = create_token("abel", Role.OPERATOR)
        tampered = token[:-5] + "XXXXX"
        with self.assertRaises(ValueError):
            verify_token(tampered)

    def test_user_store_create_and_authenticate(self) -> None:
        db = "./data/test_auth_users.db"
        # Clean slate
        if os.path.exists(db):
            os.remove(db)
        store = UserStore(db)
        store.create_user("testuser", "pass123", Role.OPERATOR)
        token = store.authenticate("testuser", "pass123")
        self.assertIsNotNone(token)
        payload = verify_token(token)
        self.assertEqual(payload.user_id, "testuser")
        self.assertEqual(payload.role, Role.OPERATOR)

    def test_user_store_wrong_password_returns_none(self) -> None:
        db = "./data/test_auth_wrong_pw.db"
        if os.path.exists(db):
            os.remove(db)
        store = UserStore(db)
        store.create_user("testuser", "pass123")
        result = store.authenticate("testuser", "wrong")
        self.assertIsNone(result)


class TestProviderRegistry(unittest.TestCase):
    def test_register_and_list(self) -> None:
        registry = ProviderRegistry()
        from shared.providers.ollama import OllamaProvider
        ollama = OllamaProvider()
        registry.register(ollama)
        providers = registry.list_providers()
        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0]["name"], "ollama")
        self.assertTrue(providers[0]["active"])

    def test_switch_provider(self) -> None:
        registry = ProviderRegistry()
        from shared.providers.ollama import OllamaProvider
        registry.register(OllamaProvider())

        # Can't switch to non-existent provider
        with self.assertRaises(KeyError):
            registry.set_active("nonexistent")

    def test_build_default_registry_includes_ollama(self) -> None:
        # Ollama is always registered (even without env vars)
        registry = build_default_registry()
        names = [p["name"] for p in registry.list_providers()]
        self.assertIn("ollama", names)

    def test_build_default_with_openai_key(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            registry = build_default_registry()
        names = [p["name"] for p in registry.list_providers()]
        self.assertIn("openai", names)


if __name__ == "__main__":
    unittest.main()
