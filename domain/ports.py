"""Portas de domínio — contratos definidos pelo negócio (inversão de dependência).

As camadas externas (``adapters/``, ``services/``, ``app/``) dependem apenas
destas interfaces. Nenhuma implementação concreta de IA vive aqui.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from domain.models import ProcessedMessage


@runtime_checkable
class AIProvider(Protocol):
    """Porta para provedores de IA.

    Qualquer provedor real (OpenAI, Google, etc.) deve implementar este
    contrato. O SDK do provedor só pode ser importado dentro de
    ``adapters/ai/``.
    """

    name: str

    async def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        """Retorna o texto bruto (esperado: JSON). Levanta AIProviderError em falha."""
        ...


@runtime_checkable
class MessageRepository(Protocol):
    """Porta para persistência de mensagens processadas."""

    async def save(self, msg: ProcessedMessage) -> ProcessedMessage:
        """Persiste a mensagem e retorna a versão salva."""
        ...

    async def list(self, limit: int = 50) -> list[ProcessedMessage]:
        """Lista as últimas mensagens processadas (padrão: 50)."""
        ...


@runtime_checkable
class Notifier(Protocol):
    """Porta para notificação externa (ex.: webhook do n8n)."""

    async def notify(self, msg: ProcessedMessage) -> None:
        """Dispara a notificação da mensagem processada."""
        ...
