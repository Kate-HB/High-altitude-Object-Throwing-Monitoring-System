"""Tests for backend.app.services.statistics_service."""
from backend.app.core.database import init_db
from backend.app.services.event_service import batch_insert_events
from backend.app.services.statistics_service import get_overview
from backend.app.services.task_service import create_task


class TestGetOverview:
    def test_returns_empty_stats_when_no_events(self):
        init_db()
        result = get_overview()
        assert result["today_event_count"] == 0
        assert result["total_event_count"] == 0
        assert result["recent_events"] == []
        assert result["daily_trend"] == []
        assert result["confidence_distribution"]["low_0.35_0.5"] == 0
        assert result["status_distribution"]["unconfirmed"] == 0

    def test_counts_events_correctly(self):
        init_db()
        task_id = create_task("upload", "test.mp4")
        events = [
            {"track_id": 1, "confidence": 0.4, "status": "unconfirmed",
             "snapshot_path": "", "roi_x": 0, "roi_y": 0, "roi_width": 100, "roi_height": 100,
             "frame_id": 10, "timestamp": 1.0},
            {"track_id": 2, "confidence": 0.6, "status": "confirmed",
             "snapshot_path": "", "roi_x": 0, "roi_y": 0, "roi_width": 100, "roi_height": 100,
             "frame_id": 20, "timestamp": 2.0},
            {"track_id": 3, "confidence": 0.9, "status": "false_alarm",
             "snapshot_path": "", "roi_x": 0, "roi_y": 0, "roi_width": 100, "roi_height": 100,
             "frame_id": 30, "timestamp": 3.0},
        ]
        batch_insert_events(task_id, events)

        result = get_overview()
        assert result["total_event_count"] == 3
        assert len(result["recent_events"]) == 3
        # confidence_distribution
        assert result["confidence_distribution"]["low_0.35_0.5"] == 1   # 0.4
        assert result["confidence_distribution"]["mid_0.5_0.7"] == 1   # 0.6
        assert result["confidence_distribution"]["high_0.7_1.0"] == 1  # 0.9
        # status_distribution
        assert result["status_distribution"]["unconfirmed"] == 1
        assert result["status_distribution"]["confirmed"] == 1
        assert result["status_distribution"]["false_alarm"] == 1
