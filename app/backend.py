"""Backend do frontend sandbox.

Este módulo contém as funções principais da interface web.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

API_BASE_URL = "http://api:8000/api/v1"


class MockResponse:
    """Mock de resposta HTTP para testes."""

    def __init__(self, status_code: int, json_data: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self) -> dict:
        return self._json_data


def health_check() -> bool:
    """Verifica se a API está saudável.

    Returns:
        True se a API estiver respondendo, False caso contrário.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def fetch_recent_messages(limit: int = 50) -> list[dict[str, Any]]:
    """Busca as mensagens mais recentes do histórico.

    Args:
        limit: Número máximo de mensagens a buscar.

    Returns:
        Lista de mensagens processadas.
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/messages",
            params={"limit": limit},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
        return []


def classify_text(
    texto: str, use_real_ai: bool = False
) -> dict[str, Any] | None:
    """Classifica um texto.

    Args:
        texto: Mensagem a ser classificada.
        use_real_ai: Se True, usa IA real; se False, usa FakeAIProvider.

    Returns:
        Classificação validada ou None em caso de erro.
    """
    try:
        payload = {
            "texto": texto,
            "remetente": "demo@kodie.com",
            "canal": "sandbox",
        }

        headers = {}
        # API key pode ser obtida de configurações ou usada padrão
        api_key = _get_api_key()
        if api_key:
            headers["X-API-Key"] = api_key

        endpoint = "/classify" if use_real_ai else "/classify"
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            headers=headers,
            timeout=30 if use_real_ai else 5,
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            logger.error("API Key inválida")
            return None
        else:
            logger.error(f"Erro na classificação: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Erro na classificação: {e}")
        return None


def save_and_notify(texto: str) -> dict[str, Any] | None:
    """Salva a mensagem e notifica o n8n (fluxo completo).

    Args:
        texto: Mensagem a ser processada.

    Returns:
        Mensagem processada ou None em caso de erro.
    """
    try:
        payload = {
            "texto": texto,
            "remetente": "demo@kodie.com",
            "canal": "sandbox",
        }

        headers = {}
        api_key = _get_api_key()
        if api_key:
            headers["X-API-Key"] = api_key

        response = requests.post(
            f"{API_BASE_URL}/messages",
            json=payload,
            headers=headers,
            timeout=30,
        )

        if response.status_code == 201:
            return response.json()
        elif response.status_code == 401:
            logger.error("API Key inválida")
            return None
        else:
            logger.error(f"Erro ao salvar: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Erro ao salvar: {e}")
        return None


def _get_api_key() -> str | None:
    """Obtém a API key do ambiente.

    Returns:
        API key configurada ou None.
    """
    try:
        import os

        return os.getenv("API_KEY")
    except Exception:
        return None


def get_ai_status() -> dict[str, Any]:
    """Verifica o status do provedor de IA.

    Returns:
        Dicionário com status do provedor.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health/ai", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "provider": data.get("provider", "unknown"),
                "responded": data.get("responded", False),
                "error": data.get("error"),
            }
    except Exception as e:
        logger.error(f"Erro ao verificar status da IA: {e}")
    return {"provider": "unknown", "responded": False}
