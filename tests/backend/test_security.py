"""Tests for backend.app.core.security — file path validation."""
import os
from pathlib import Path

import pytest

from backend.app.core import security

_PROJECT = Path(__file__).resolve().parent.parent.parent


class TestValidateFilePath:
    def test_empty_path_returns_none(self):
        assert security.validate_file_path("") is None

    def test_none_path_returns_none(self):
        assert security.validate_file_path(None) is None

    def test_absolute_path_returns_none(self):
        assert security.validate_file_path("C:\\windows\\system32") is None

    def test_dot_dot_traversal_returns_none(self):
        assert security.validate_file_path("../etc/passwd") is None

    def test_mid_path_traversal_returns_none(self):
        assert security.validate_file_path("uploads/../etc/passwd") is None

    def test_disallowed_dir_returns_none(self):
        assert security.validate_file_path("data/videos/demo.mp4") is None

    def test_events_without_snapshots_is_rejected(self):
        assert security.validate_file_path("events/something.txt") is None

    def test_valid_file_in_uploads(self):
        """Create a real file in uploads/ to verify the happy path."""
        uploads_dir = _PROJECT / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        test_file = uploads_dir / "_test_security.txt"
        test_file.write_text("test")
        try:
            result = security.validate_file_path("uploads/_test_security.txt")
            assert result is not None
            assert result.is_file()
            assert result.name == "_test_security.txt"
        finally:
            test_file.unlink(missing_ok=True)

    def test_valid_file_in_outputs(self):
        """Create a real file in outputs/ to verify outputs whitelist."""
        outputs_dir = _PROJECT / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        test_file = outputs_dir / "_test_output.txt"
        test_file.write_text("test")
        try:
            result = security.validate_file_path("outputs/_test_output.txt")
            assert result is not None
            assert result.name == "_test_output.txt"
        finally:
            test_file.unlink(missing_ok=True)

    def test_valid_file_in_events_snapshots(self):
        """Multi-component whitelist 'events/snapshots' should match."""
        snap_dir = _PROJECT / "events" / "snapshots"
        snap_dir.mkdir(parents=True, exist_ok=True)
        test_file = snap_dir / "_test_snap.txt"
        test_file.write_text("test")
        try:
            result = security.validate_file_path("events/snapshots/_test_snap.txt")
            assert result is not None
            assert result.name == "_test_snap.txt"
        finally:
            test_file.unlink(missing_ok=True)
