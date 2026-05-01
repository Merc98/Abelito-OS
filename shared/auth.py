"""Auth layer  — JWT tokens, role-based access, OAuth2-ready."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any
from fastapi import Header, HTTPException

# ── Constants ──────────────────────────────────────────────────────────────────

JWT_SECRET = os.getenv("ABEL_JWT_SECRET", "abel-os-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = int(os.getenv("ABEL_TOKEN_EXPIRY", "86400"))  # 24h default


class Role(str, Enum):
    OPERATOR = "operator"
    ADMIN = "admin"
    AUTONOMOUS = "autonomous"


@dataclass(frozen=True, slots=True)
class TokenPayload:
    user_id: str
    role: Role
    iat: float
    exp: float


# ── Lightweight JWT (no PyJWT dependency) ──────────────────────────────────────
# We use HMAC-SHA256 for signing. For production with OAuth2/SSO,
# replace with a proper library or integrate with the SSO provider's tokens.

def _b64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    import base64
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _sign(header_payload: str, secret: str) -> str:
    sig = hmac.new(secret.encode(), header_payload.encode(), hashlib.sha256).digest()
    return _b64url_encode(sig)


def create_token(user_id: str, role: Role | str, expiry_s: int | None = None) -> str:
    """Create a signed JWT token."""
    if isinstance(role, str):
        role = Role(role)
    now = time.time()
    exp = now + (expiry_s or TOKEN_EXPIRY_SECONDS)

    header = _b64url_encode(json.dumps({"alg": JWT_ALGORITHM, "typ": "JWT"}).encode())
    payload = _b64url_encode(json.dumps({
        "user_id": user_id,
        "role": role.value,
        "iat": now,
        "exp": exp,
    }).encode())

    header_payload = f"{header}.{payload}"
    signature = _sign(header_payload, JWT_SECRET)
    return f"{header_payload}.{signature}"


def verify_token(token: str) -> TokenPayload:
    """Verify a JWT token and return its payload. Raises ValueError on failure."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    header_payload = f"{parts[0]}.{parts[1]}"
    expected_sig = _sign(header_payload, JWT_SECRET)
    if not hmac.compare_digest(parts[2], expected_sig):
        raise ValueError("Invalid token signature")

    payload_json = json.loads(_b64url_decode(parts[1]))
    if payload_json.get("exp", 0) < time.time():
        raise ValueError("Token expired")

    return TokenPayload(
        user_id=payload_json["user_id"],
        role=Role(payload_json["role"]),
        iat=payload_json["iat"],
        exp=payload_json["exp"],
    )


# ── User store (SQLite) ──────────────────────────────────────────────────────

class UserStore:
    """Simple user store for local auth. In production, replace with OAuth2/SSO."""

    def __init__(self, db_path: str = "./data/abel_users.db") -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'operator',
                    created_at REAL NOT NULL
                )
            """)

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(f"{JWT_SECRET}:{password}".encode()).hexdigest()

    def create_user(self, user_id: str, password: str, role: Role | str = Role.OPERATOR) -> None:
        if isinstance(role, str):
            role = Role(role)
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO users (user_id, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (user_id, self._hash_password(password), role.value, time.time()),
            )

    def authenticate(self, user_id: str, password: str) -> str | None:
        """Authenticate user and return a JWT token, or None on failure."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT password_hash, role FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        if not hmac.compare_digest(row["password_hash"], self._hash_password(password)):
            return None
        return create_token(user_id, row["role"])

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT user_id, role, created_at FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None


# ── FastAPI dependency (for protecting endpoints) ─────────────────────────────

def require_auth(authorization: str | None = Header(default=None)) -> TokenPayload:
    """FastAPI dependency to extract and validate JWT from Authorization header.

    Usage in a route:
        @app.get("/protected")
        async def protected(auth: TokenPayload = Depends(require_auth)):
            ...
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[7:]
    try:
        return verify_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def require_role(*roles: Role):
    """Factory for a FastAPI dependency that checks the user's role."""
    def checker(authorization: str | None = Header(default=None)) -> TokenPayload:
        payload = require_auth(authorization)
        if payload.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires one of: {[r.value for r in roles]}")
        return payload
    return checker
