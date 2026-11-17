"""Repositório PostgreSQL de mensagens processadas (SPEC-04).

Implementa a porta ``MessageRepository`` usando SQLAlchemy async. Toda a
conversão ORM ↔ domínio fica em ``app.adapters.models``.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.models import (
    Base,
    MessageORM,
    domain_to_message_orm,
    message_orm_to_domain,
)
from domain.models import ProcessedMessage


class PostgresMessageRepository:
    """Persistência de mensagens processadas em PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        """Inicializa o repositório com uma sessão assíncrona injetada.

        Args:
            session: Sessão async do SQLAlchemy (injeção de dependência).
        """
        self._session = session

    async def save(self, msg: ProcessedMessage) -> ProcessedMessage:
        """Persiste a mensagem e retorna a versão salva."""
        orm = domain_to_message_orm(msg)
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return message_orm_to_domain(orm)

    async def get(self, msg_id: str) -> ProcessedMessage | None:
        """Busca uma mensagem pelo ID. Retorna None se não existir."""
        orm = await self._session.get(MessageORM, uuid.UUID(msg_id))
        return message_orm_to_domain(orm) if orm else None

    async def list(self, limit: int = 50) -> list[ProcessedMessage]:
        """Lista as últimas mensagens processadas, do mais recente para o mais antigo."""
        resultado = await self._session.execute(
            select(MessageORM).order_by(MessageORM.criado_em.desc()).limit(limit)
        )
        return [message_orm_to_domain(orm) for orm in resultado.scalars().all()]

    async def mark_notified(self, msg_id: str) -> None:
        """Marca a mensagem como notificada. Não falha se o ID não existir."""
        await self._session.execute(
            update(MessageORM)
            .where(MessageORM.id == uuid.UUID(msg_id))
            .values(notificado=True)
        )
        await self._session.commit()


__all__ = ["Base", "PostgresMessageRepository"]
