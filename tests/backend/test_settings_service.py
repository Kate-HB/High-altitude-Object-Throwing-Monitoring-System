"""Tests for backend.app.services.settings_service."""
import pytest

from backend.app.core.database import init_db
from backend.app.services.settings_service import get_settings, update_settings, VALID_RANGES

# Known base values to reset to before tests (matches DB DDL defaults)
BASE = {"detect_confidence": 0.35, "downward_ratio": 0.55, "imgsz": 960}


def _reset():
    """Reset settings to known defaults so tests don't interfere."""
    init_db()
    update_settings(BASE)


class TestGetSettings:
    def test_returns_dict_after_init(self):
        _reset()
        result = get_settings()
        assert isinstance(result, dict)
        assert "detect_confidence" in result

    def test_default_values(self):
        _reset()
        result = get_settings()
        assert result["detect_confidence"] == 0.35
        assert result["downward_ratio"] == 0.55
        assert result["imgsz"] == 960


class TestUpdateSettings:
    def test_update_single_field(self):
        _reset()
        updated = update_settings({"detect_confidence": 0.5})
        assert updated["detect_confidence"] == 0.5

    def test_update_multiple_fields(self):
        _reset()
        updated = update_settings({"downward_ratio": 0.8, "imgsz": 640})
        assert updated["downward_ratio"] == 0.8
        assert updated["imgsz"] == 640

    def test_value_below_range_raises(self):
        _reset()
        with pytest.raises(ValueError, match="超出范围"):
            update_settings({"detect_confidence": 0.05})

    def test_value_above_range_raises(self):
        _reset()
        with pytest.raises(ValueError, match="超出范围"):
            update_settings({"detect_confidence": 1.5})

    def test_edge_value_accepted(self):
        _reset()
        updated = update_settings({"detect_confidence": 0.1})
        assert updated["detect_confidence"] == 0.1

    def test_unknown_key_ignored(self):
        _reset()
        updated = update_settings({"nonexistent_param": 999, "detect_confidence": 0.6})
        assert updated["detect_confidence"] == 0.6
        assert "nonexistent_param" not in updated
