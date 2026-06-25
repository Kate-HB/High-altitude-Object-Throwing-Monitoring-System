"""Tests for token generation, validation, and verification dependency."""

import time
from unittest import mock

import pytest
from fastapi import HTTPException

from backend.app.core.auth import (
    TOKEN_TTL,
    generate_token,
    remove_token,
    validate_token,
    verify_token,
)


class TestGenerateToken:
    def test_returns_32_char_hex_string(self):
        token = generate_token()
        assert isinstance(token, str)
        assert len(token) == 32  # token_hex(16)

    def test_token_is_stored(self):
        token = generate_token()
        entry = validate_token(token)
        assert entry is not None
        assert entry["username"] == "admin"
        assert entry["role"] == "admin"

    def test_custom_username_role(self):
        token = generate_token(username="testuser", role="viewer")
        entry = validate_token(token)
        assert entry["username"] == "testuser"
        assert entry["role"] == "viewer"

    def test_each_token_is_unique(self):
        token1 = generate_token()
        token2 = generate_token()
        assert token1 != token2


class TestValidateToken:
    def test_valid_token_returns_entry(self):
        token = generate_token()
        entry = validate_token(token)
        assert entry["username"] == "admin"
        assert entry["role"] == "admin"
        assert "expire" in entry

    def test_unknown_token_returns_none(self):
        assert validate_token("nonexistent-token-abcdefgh") is None

    def test_empty_token_returns_none(self):
        assert validate_token("") is None

    def test_expired_token_returns_none(self):
        with mock.patch.object(time, "time") as mock_time:
            mock_time.return_value = 100000
            token = generate_token()
            # Now advance time past TTL
            mock_time.return_value = 100000 + TOKEN_TTL + 1
            assert validate_token(token) is None

    def test_expired_token_is_removed_from_store(self):
        with mock.patch.object(time, "time") as mock_time:
            mock_time.return_value = 100000
            token = generate_token()
            mock_time.return_value = 100000 + TOKEN_TTL + 1
            validate_token(token)
            # Second validation should also return None
            assert validate_token(token) is None


class TestRemoveToken:
    def test_removes_existing_token(self):
        token = generate_token()
        assert validate_token(token) is not None
        remove_token(token)
        assert validate_token(token) is None

    def test_no_error_on_unknown_token(self):
        remove_token("nonexistent")
        # Should not raise


class TestVerifyToken:
    def test_valid_bearer_token_returns_info(self):
        token = generate_token()
        result = verify_token(authorization=f"Bearer {token}")
        assert result["token"] == token
        assert result["username"] == "admin"
        assert result["role"] == "admin"

    def test_empty_header_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            verify_token(authorization="")
        assert exc.value.status_code == 401

    def test_missing_bearer_prefix_raises_401(self):
        token = generate_token()
        with pytest.raises(HTTPException) as exc:
            verify_token(authorization=token)
        assert exc.value.status_code == 401

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            verify_token(authorization="Bearer invalid-token-here-xxxx")
        assert exc.value.status_code == 401

    def test_expired_token_raises_401(self):
        with mock.patch.object(time, "time") as mock_time:
            mock_time.return_value = 100000
            token = generate_token()
            mock_time.return_value = 100000 + TOKEN_TTL + 1
            with pytest.raises(HTTPException) as exc:
                verify_token(authorization=f"Bearer {token}")
            assert exc.value.status_code == 401

    def test_error_detail_has_code_field(self):
        with pytest.raises(HTTPException) as exc:
            verify_token(authorization="")
        detail = exc.value.detail
        assert detail["code"] == 401
        assert detail["message"] == "unauthorized"
