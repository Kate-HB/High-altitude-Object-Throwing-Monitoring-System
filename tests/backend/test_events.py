"""Tests for events API endpoints and event_service."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import get_db, init_db
from backend.app.services.event_service import (
    batch_insert_events,
    batch_insert_detections,
    batch_insert_tracks,
    get_event,
    list_events,
    update_event_status,
)

client = TestClient(app)

TOKEN: str | None = None


def _login() -> str:
    global TOKEN
    if TOKEN is not None:
        return TOKEN
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.json()
    TOKEN = data["data"]["token"]
    assert TOKEN is not None
    return TOKEN


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_login()}"}


@pytest.fixture(autouse=True)
def _init():
    init_db()
    # Clean events/testing tables
    db = get_db()
    for tbl in ("events", "detection_results", "tracking_results"):
        db.execute(f"DELETE FROM {tbl}")
    db.commit()
    db.close()


# ── event_service unit tests ───────────────────────────────────────────

class TestEventService:
    def test_list_empty(self):
        events = list_events()
        assert events == []

    def test_batch_insert_and_list(self):
        batch_insert_events(1, [
            {"track_id": 1, "confidence": 0.92, "snapshot_path": "/tmp/s1.jpg"},
            {"track_id": 2, "confidence": 0.85, "snapshot_path": "/tmp/s2.jpg"},
        ])
        events = list_events()
        assert len(events) == 2
        track_ids = {e["track_id"] for e in events}
        assert track_ids == {1, 2}

    def test_list_filter_by_task(self):
        batch_insert_events(1, [{"track_id": 1, "confidence": 0.9}])
        batch_insert_events(2, [{"track_id": 2, "confidence": 0.8}])
        assert len(list_events(task_id=1)) == 1
        assert len(list_events(task_id=2)) == 1

    def test_list_filter_by_status(self):
        batch_insert_events(1, [
            {"track_id": 1, "confidence": 0.9, "status": "confirmed"},
            {"track_id": 2, "confidence": 0.8, "status": "unconfirmed"},
        ])
        assert len(list_events(status="confirmed")) == 1
        assert len(list_events(status="false_alarm")) == 0

    def test_get_event_with_relations(self):
        batch_insert_events(1, [{"track_id": 1, "confidence": 0.9}])
        events = list_events()
        event_id = events[0]["id"]

        batch_insert_detections(1, [
            {"frame_id": 10, "bbox_x": 100, "bbox_y": 200, "bbox_width": 50, "bbox_height": 60, "confidence": 0.88},
        ])
        batch_insert_tracks(1, [
            {"track_id": 1, "frame_id": 10, "timestamp": 0.5, "center_x": 125, "center_y": 230,
             "bbox_x": 100, "bbox_y": 200, "bbox_width": 50, "bbox_height": 60},
        ])

        event = get_event(event_id)
        assert event is not None
        assert len(event["detections"]) == 1
        assert len(event["tracks"]) == 1

    def test_update_status(self):
        batch_insert_events(1, [{"track_id": 1, "confidence": 0.9}])
        events = list_events()
        event_id = events[0]["id"]
        assert events[0]["status"] == "unconfirmed"

        assert update_event_status(event_id, "confirmed") is True
        updated = get_event(event_id)
        assert updated["status"] == "confirmed"

    def test_update_nonexistent(self):
        assert update_event_status(99999, "confirmed") is False

    def test_batch_insert_detections(self):
        count = batch_insert_detections(1, [
            {"frame_id": 1, "bbox_x": 10, "bbox_y": 20, "bbox_width": 30, "bbox_height": 40, "confidence": 0.9},
            {"frame_id": 2, "bbox_x": 11, "bbox_y": 21, "bbox_width": 31, "bbox_height": 41, "confidence": 0.8},
        ])
        assert count == 2

    def test_batch_insert_tracks(self):
        count = batch_insert_tracks(1, [
            {"track_id": 1, "frame_id": 1, "timestamp": 0.04, "center_x": 25, "center_y": 40,
             "bbox_x": 10, "bbox_y": 20, "bbox_width": 30, "bbox_height": 40},
        ])
        assert count == 1

    def test_batch_insert_empty(self):
        assert batch_insert_events(1, []) == 0
        assert batch_insert_detections(1, []) == 0
        assert batch_insert_tracks(1, []) == 0


# ── events API tests ───────────────────────────────────────────────────

class TestEventsAPI:
    def test_list_requires_auth(self):
        resp = client.get("/api/events")
        assert resp.status_code == 401

    def test_list_empty(self):
        resp = client.get("/api/events", headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["events"] == []
        assert data["data"]["count"] == 0

    def test_list_with_data(self):
        batch_insert_events(1, [
            {"track_id": 1, "confidence": 0.92},
            {"track_id": 2, "confidence": 0.85},
        ])
        resp = client.get("/api/events", headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["count"] == 2

    def test_list_filter_params(self):
        batch_insert_events(1, [{"track_id": 1, "confidence": 0.9}])
        batch_insert_events(2, [{"track_id": 2, "confidence": 0.8}])

        resp = client.get("/api/events?task_id=1", headers=_auth_headers())
        assert resp.json()["data"]["count"] == 1

        resp = client.get("/api/events?status=unconfirmed", headers=_auth_headers())
        assert resp.json()["data"]["count"] == 2

    def test_get_event_not_found(self):
        resp = client.get("/api/events/99999", headers=_auth_headers())
        assert resp.status_code == 200
        assert resp.json()["code"] == 404

    def test_get_event_found(self):
        batch_insert_events(1, [{"track_id": 1, "confidence": 0.9}])
        events = list_events()
        event_id = events[0]["id"]

        resp = client.get(f"/api/events/{event_id}", headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["track_id"] == 1

    def test_patch_status(self):
        batch_insert_events(1, [{"track_id": 1, "confidence": 0.9}])
        events = list_events()
        event_id = events[0]["id"]

        resp = client.patch(
            f"/api/events/{event_id}/status",
            json={"status": "confirmed"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "confirmed"

        # Verify in DB
        event = get_event(event_id)
        assert event["status"] == "confirmed"

    def test_patch_invalid_status(self):
        batch_insert_events(1, [{"track_id": 1, "confidence": 0.9}])
        events = list_events()
        event_id = events[0]["id"]

        resp = client.patch(
            f"/api/events/{event_id}/status",
            json={"status": "invalid"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 400

    def test_patch_nonexistent(self):
        resp = client.patch(
            "/api/events/99999/status",
            json={"status": "confirmed"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 404
