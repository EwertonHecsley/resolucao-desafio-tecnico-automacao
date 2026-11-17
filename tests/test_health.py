"""Testes do health check da aplicação FastAPI."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    """Verifica que GET /health retorna 200 com {"status": "ok"}."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_returns_json() -> None:
    """Verifica que o health check retorna content-type JSON."""
    client = TestClient(app)
    response = client.get("/health")
    assert "application/json" in response.headers["content-type"]
