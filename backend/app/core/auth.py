"""Token generation, storage, and verification dependency."""

from __future__ import annotations

import secrets
import time
from typing import Any

from fastapi import Header, HTTPException

# In-memory token store: {token: {username, role, expire}}
_tokens: dict[str, dict[str, Any]] = {}
TOKEN_TTL = 86400  # 24 hours


def generate_token(username: str = "admin", role: str = "admin") -> str:
    token = secrets.token_hex(16)
    _tokens[token] = {
        "username": username,
        "role": role,
        "expire": time.time() + TOKEN_TTL,
    }
    return token


def validate_token(token: str) -> dict[str, Any] | None:
    entry = _tokens.get(token)
    if entry is None:
        return None
    if time.time() > entry["expire"]:
        del _tokens[token]
        return None
    return entry


def remove_token(token: str) -> None:
    _tokens.pop(token, None)


def verify_token(authorization: str = Header(default="")) -> dict[str, Any]:
    """FastAPI dependency — raises 401 if token is missing or invalid."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"code": 401, "message": "unauthorized", "detail": "未登录或token无效"},
        )
    token = authorization[7:]
    entry = validate_token(token)
    if entry is None:
        raise HTTPException(
            status_code=401,
            detail={"code": 401, "message": "unauthorized", "detail": "未登录或token无效"},
        )
    return {"token": token, "username": entry["username"], "role": entry["role"]}
