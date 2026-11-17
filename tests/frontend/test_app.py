"""Testes unitários para o frontend sandbox."""

import sys
from pathlib import Path

# Adiciona frontend ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "frontend"))

from unittest.mock import patch

import pytest


class MockResponse:
    """Mock de resposta HTTP."""

    def __init__(self, status_code: int, json_data=None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):
        return self._json_data


@pytest.fixture
def sample_classification():
    """Fixture com classificação de exemplo."""
    return {
        "categoria": "reclamacao",
        "setor": "logistica",
        "prioridade": "alta",
        "sentimento": "negativo",
        "resumo": "Cliente relata atraso na entrega.",
        "confianca": 0.92,
    }


@pytest.fixture
def sample_message():
    """Fixture com mensagem processada de exemplo."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "entrada": {
            "texto": "Meu pedido ainda não chegou",
            "remetente": "demo@kodie.com",
            "canal": "sandbox",
        },
        "classificacao": {
            "categoria": "reclamacao",
            "setor": "logistica",
            "prioridade": "alta",
            "sentimento": "negativo",
            "resumo": "Cliente relata atraso na entrega.",
            "confianca": 0.92,
        },
        "provedor": "fake",
        "criado_em": "2026-11-17T19:23:43.282Z",
        "notificado": True,
    }


def test_api_base_url():
    """Testa se a URL base está correta."""
    assert API_BASE_URL == "http://api:8000/api/v1"


@patch("frontend.app.requests.get")
def test_health_check_success(mock_get):
    """Testa health check com sucesso."""
    mock_get.return_value = MockResponse(200)
    assert health_check() is True
    mock_get.assert_called_once_with(f"{API_BASE_URL}/health", timeout=5)


@patch("frontend.app.requests.get")
def test_health_check_failure(mock_get):
    """Testa health check com falha."""
    mock_get.return_value = MockResponse(500)
    assert health_check() is False


@patch("frontend.app.requests.get")
def test_health_check_exception(mock_get):
    """Testa health check com exceção."""
    mock_get.side_effect = Exception("Connection error")
    assert health_check() is False


@patch("frontend.app.requests.get")
def test_fetch_recent_messages_success(mock_get, sample_message):
    """Testa busca de mensagens com sucesso."""
    mock_get.return_value = MockResponse(200, [sample_message])
    result = fetch_recent_messages(limit=10)

    assert len(result) == 1
    assert result[0]["id"] == sample_message["id"]
    mock_get.assert_called_once_with(
        f"{API_BASE_URL}/messages", params={"limit": 10}, timeout=10
    )


@patch("frontend.app.requests.get")
def test_fetch_recent_messages_failure(mock_get):
    """Testa busca de mensagens com falha."""
    mock_get.return_value = MockResponse(500)
    result = fetch_recent_messages()
    assert result == []


@patch("frontend.app.requests.post")
def test_classify_text_success(mock_post, sample_classification):
    """Testa classificação com sucesso."""
    mock_post.return_value = MockResponse(200, sample_classification)

    result = classify_text("Meu pedido não chegou")

    assert result == sample_classification
    assert mock_post.call_args[0][0] == f"{API_BASE_URL}/classify"


@patch("frontend.app.requests.post")
def test_classify_text_with_real_ai(mock_post, sample_classification):
    """Testa classificação com IA real."""
    mock_post.return_value = MockResponse(200, sample_classification)

    classify_text("Meu pedido não chegou", use_real_ai=True)

    assert mock_post.call_args[1]["timeout"] == 30


@patch("frontend.app.requests.post")
def test_classify_text_unauthorized(mock_post):
    """Testa classificação com API key inválida."""
    mock_post.return_value = MockResponse(401, text="Unauthorized")

    result = classify_text("Teste")

    assert result is None


@patch("frontend.app.requests.post")
def test_save_and_notify_success(mock_post, sample_message):
    """Testa fluxo completo com sucesso."""
    mock_post.return_value = MockResponse(201, sample_message)

    result = save_and_notify("Meu pedido não chegou")

    assert result == sample_message
    assert mock_post.call_args[0][0] == f"{API_BASE_URL}/messages"
    assert mock_post.call_args[1]["timeout"] == 30


@patch("frontend.app.requests.post")
def test_save_and_notify_failure(mock_post):
    """Testa fluxo completo com falha."""
    mock_post.return_value = MockResponse(500, text="Internal Server Error")

    result = save_and_notify("Teste")

    assert result is None


@patch("frontend.app.requests.get")
def test_get_ai_status_success(mock_get):
    """Testa status da IA com sucesso."""
    mock_get.return_value = MockResponse(
        200, {"provider": "fake", "responded": True}
    )

    result = get_ai_status()

    assert result["provider"] == "fake"
    assert result["responded"] is True


@patch("frontend.app.requests.get")
def test_get_ai_status_with_error(mock_get):
    """Testa status da IA com erro."""
    mock_get.return_value = MockResponse(
        200, {"provider": "gemini", "responded": False, "error": "API key missing"}
    )

    result = get_ai_status()

    assert result["provider"] == "gemini"
    assert result["responded"] is False
    assert result["error"] == "API key missing"


@patch("frontend.app.requests.get")
def test_get_ai_status_exception(mock_get):
    """Testa status da IA com exceção."""
    mock_get.side_effect = Exception("Connection refused")

    result = get_ai_status()

    assert result["provider"] == "unknown"
    assert result["responded"] is False
    assert "Connection refused" in result["error"]
