from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_returns_service_metadata():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "High-altitude Object Throwing Monitoring System",
        "version": "0.1.0",
    }
