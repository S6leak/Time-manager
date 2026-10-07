"""Tests de la route de santé."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok():
    """La route /api/health répond 200 avec le statut ok."""
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"