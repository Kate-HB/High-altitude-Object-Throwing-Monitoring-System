"""Tests for database initialization, connection, and table structure."""

import sqlite3
import tempfile
import os
from pathlib import Path
from unittest import mock

from backend.app.core.database import (
    DDL_STATEMENTS,
    get_db,
    get_db_path,
    init_db,
    _db_path,
)


class TestDDL:
    def test_five_table_creates(self):
        create_stmts = [s for s in DDL_STATEMENTS if s.strip().upper().startswith("CREATE TABLE")]
        assert len(create_stmts) == 5

    def test_table_names(self):
        create_stmts = [s for s in DDL_STATEMENTS if s.strip().upper().startswith("CREATE TABLE")]
        names = []
        for s in create_stmts:
            # Extract table name: "CREATE TABLE IF NOT EXISTS name (..."
            parts = s.split()
            idx = parts.index("EXISTS") if "EXISTS" in parts else parts.index("TABLE")
            names.append(parts[idx + 1])
        assert "system_settings" in names
        assert "video_tasks" in names
        assert "events" in names
        assert "detection_results" in names
        assert "tracking_results" in names

    def test_default_row_insert(self):
        insert_stmts = [s for s in DDL_STATEMENTS if s.strip().upper().startswith("INSERT")]
        assert len(insert_stmts) == 1
        assert "system_settings" in insert_stmts[0]
        assert "OR IGNORE" in insert_stmts[0]


class TestGetDbPath:
    def setup_method(self):
        # Reset cached path
        import backend.app.core.database as db_module
        db_module._db_path = None

    def test_returns_string(self):
        path = get_db_path()
        assert isinstance(path, str)

    def test_ends_with_system_db(self):
        path = get_db_path()
        assert path.endswith("system.db")

    def test_same_path_on_second_call(self):
        path1 = get_db_path()
        path2 = get_db_path()
        assert path1 == path2


class TestInitDb:
    def setup_method(self):
        import backend.app.core.database as db_module
        db_module._db_path = None

    def test_init_creates_db_file(self):
        """Use a temp db path to verify init_db works end-to-end."""
        import backend.app.core.database as db_module

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            db_module._db_path = db_path
            try:
                init_db()
                assert os.path.exists(db_path)
            finally:
                db_module._db_path = None

    def test_tables_exist_after_init(self):
        import backend.app.core.database as db_module

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            db_module._db_path = db_path
            try:
                init_db()
                conn = sqlite3.connect(db_path)
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                assert "system_settings" in tables
                assert "video_tasks" in tables
                assert "events" in tables
                assert "detection_results" in tables
                assert "tracking_results" in tables
            finally:
                db_module._db_path = None

    def test_default_system_settings_exists(self):
        import backend.app.core.database as db_module

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            db_module._db_path = db_path
            try:
                init_db()
                conn = sqlite3.connect(db_path)
                row = conn.execute("SELECT * FROM system_settings WHERE id=1").fetchone()
                conn.close()
                assert row is not None
                # Default values
                assert row[1] == 0.35  # detect_confidence
                assert row[2] == 0.7   # downward_ratio
            finally:
                db_module._db_path = None

    def test_init_is_idempotent(self):
        """Calling init_db twice should not raise errors."""
        import backend.app.core.database as db_module

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            db_module._db_path = db_path
            try:
                init_db()
                init_db()  # second call
                assert os.path.exists(db_path)
            finally:
                db_module._db_path = None


class TestGetDb:
    def setup_method(self):
        import backend.app.core.database as db_module
        db_module._db_path = None

    def test_returns_connection(self):
        import backend.app.core.database as db_module

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            db_module._db_path = db_path
            try:
                init_db()
                conn = get_db()
                assert isinstance(conn, sqlite3.Connection)
                conn.close()
            finally:
                db_module._db_path = None

    def test_row_factory_is_set(self):
        import backend.app.core.database as db_module

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            db_module._db_path = db_path
            try:
                init_db()
                conn = get_db()
                row = conn.execute("SELECT * FROM system_settings WHERE id=1").fetchone()
                # sqlite3.Row allows dict-like access
                assert row["id"] == 1
                assert row["detect_confidence"] == 0.35
                conn.close()
            finally:
                db_module._db_path = None


class TestTableConstraints:
    def setup_method(self):
        import backend.app.core.database as db_module
        db_module._db_path = None

    def test_system_settings_single_row(self):
        """Cannot insert a second row into system_settings."""
        import backend.app.core.database as db_module

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            db_module._db_path = db_path
            try:
                init_db()
                conn = sqlite3.connect(db_path)
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute("INSERT INTO system_settings (id) VALUES (2)")
                conn.close()
            finally:
                db_module._db_path = None

    def test_video_tasks_source_type_check(self):
        import backend.app.core.database as db_module

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            db_module._db_path = db_path
            try:
                init_db()
                conn = sqlite3.connect(db_path)
                with pytest.raises(sqlite3.IntegrityError):
                    conn.execute(
                        "INSERT INTO video_tasks (source_type, source_path) VALUES (?, ?)",
                        ("invalid_type", "test.mp4"),
                    )
                conn.close()
            finally:
                db_module._db_path = None


import pytest
