"""Testes do health check da aplicação FastAPI."""

from fastapi.testclient import TestClient

from app.adapters.ai.fake import FakeAIProvider
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


def test_health_ai_responds() -> None:
    """Verifica que GET /api/v1/health/ai retorna provider e responded."""
    client = TestClient(app)
    response = client.get("/api/v1/health/ai")
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "responded" in data
    assert isinstance(data["responded"], bool)
    assert data["provider"] in ["fake", "gemini", "groq", "openai"]


def test_health_ai_probe_compativel_com_groq() -> None:
    """Verifica que o probe do /health/ai é aceito por provedores que exigem
    a palavra 'json' nas mensagens quando ``response_format`` é
    ``json_object`` (ex.: Groq, erro 400 caso contrário).

    O probe deve ser uma chamada simples, mas o conteúdo precisa conter
    'json' para não gerar falso negativo de indisponibilidade.
    """
    fake = FakeAIProvider()
    app.dependency_overrides.clear()
    from app.api.deps import get_ai_provider  # noqa: E402

    app.dependency_overrides[get_ai_provider] = lambda: fake
    try:
        client = TestClient(app)
        response = client.get("/api/v1/health/ai")
        assert response.status_code == 200
        assert response.json()["responded"] is True
    finally:
        app.dependency_overrides.clear()

    # Chamada única com conteúdo contendo "json" nas duas mensagens.
    assert len(fake._respostas) == 0  # consumiu exatamente 1 resposta
    assert "json" in fake._system_prompt.lower()
    assert "json" in fake._user_prompt.lower()
