"""Dependências da API via FastAPI Depends (SPEC-06)."""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request

from app.adapters.ai.factory import build_ai_provider
from app.adapters.notifier_n8n import N8nWebhookNotifier, NullNotifier
from app.config import Settings
from services.classifier import ClassifierService

logger = logging.getLogger(__name__)


def get_settings() -> Settings:
    """Retorna configurações da aplicação.

    Returns:
        Instância de Settings carregadas do ambiente.
    """
    return Settings()


def get_ai_provider(settings: Settings = Depends(get_settings)):
    """Constrói e retorna o AIProvider (ou FallbackAIProvider) injetado.

    Args:
        settings: Configurações da aplicação.

    Returns:
        Instância de AIProvider ou FallbackAIProvider.
    """
    return build_ai_provider(settings)


def get_classifier_service(ai=Depends(get_ai_provider)):
    """Constrói o ClassifierService injetando o AIProvider.

    Args:
        ai: Instância de AIProvider.

    Returns:
        Instância de ClassifierService.
    """
    return ClassifierService(ai)


async def get_message_repository(request: Request):
    """Retorna MessageRepository injetado via app.state (herdado de main.py).

    Args:
        request: Request atual do FastAPI.

    Yields:
        Instância de MessageRepository com uma sessão por requisição.

    Raises:
        RuntimeError: Se a aplicação foi iniciada sem DATABASE_URL.
    """
    factory = request.app.state.db_session_factory
    if factory is None:
        raise RuntimeError("DATABASE_URL não configurada")

    from app.adapters.repository_postgres import PostgresMessageRepository

    async with factory() as session:
        yield PostgresMessageRepository(session)


def get_notifier(settings: Settings = Depends(get_settings)):
    """Retorna Notifier (real ou Null) dependendo de N8N_WEBHOOK_URL.

    Args:
        settings: Configurações da aplicação.

    Returns:
        N8nWebhookNotifier se N8N_WEBHOOK_URL estiver configurada,
        caso contrário NullNotifier.
    """
    if not settings.N8N_WEBHOOK_URL:
        return NullNotifier()

    return N8nWebhookNotifier(
        webhook_url=settings.N8N_WEBHOOK_URL,
        secret=settings.N8N_WEBHOOK_SECRET,
        timeout=settings.N8N_TIMEOUT_SECONDS,
    )


def require_api_key(request: Request, settings: Settings = Depends(get_settings)):
    """Verifica header X-API-Key. Retorna None se API_KEY estiver vazio (desativado).

    Args:
        request: Request atual do FastAPI.
        settings: Configurações da aplicação.

    Raises:
        HTTPException: status 401 se X-API-Key estiver presente mas inválido.
    """
    api_key = settings.API_KEY
    if api_key:
        provided_key = request.headers.get("X-API-Key")
        if provided_key != api_key:
            logger.warning("Falha de autenticação: X-API-Key inválido")
            raise HTTPException(
                status_code=401,
                detail="X-API-Key inválido",
            )
        logger.debug("Autenticação bem-sucedida com X-API-Key")
