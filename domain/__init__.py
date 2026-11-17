"""Camada de domínio — modelos, portas e erros."""

from domain.errors import AIProviderError, InvalidAIResponseError
from domain.models import (
    Categoria,
    Classification,
    MessageIn,
    Prioridade,
    ProcessedMessage,
    Sentimento,
    Setor,
)
from domain.ports import AIProvider, MessageRepository, Notifier

__all__ = [
    "AIProvider",
    "AIProviderError",
    "Categoria",
    "Classification",
    "InvalidAIResponseError",
    "MessageIn",
    "MessageRepository",
    "Notifier",
    "Prioridade",
    "ProcessedMessage",
    "Sentimento",
    "Setor",
]
