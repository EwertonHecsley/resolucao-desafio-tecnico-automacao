"""Modelo ORM e conversões para persistência PostgreSQL (SPEC-04).

O SQLAlchemy fica confinado neste módulo: o domínio (``ProcessedMessage``)
não conhece tabelas nem sessões.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from domain.models import ProcessedMessage


class Base(DeclarativeBase):
    """Base declarativa para os modelos ORM da aplicação."""


class MessageORM(Base):
    """Mapeamento da tabela ``messages``."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    texto: Mapped[str] = mapped_column(String(5000), nullable=False)
    remetente: Mapped[str | None] = mapped_column(String(255), nullable=True)
    canal: Mapped[str | None] = mapped_column(String(100), nullable=True)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    setor: Mapped[str] = mapped_column(String(50), nullable=False)
    prioridade: Mapped[str] = mapped_column(String(50), nullable=False)
    sentimento: Mapped[str] = mapped_column(String(50), nullable=False)
    resumo: Mapped[str] = mapped_column(String(200), nullable=False)
    confianca: Mapped[float] = mapped_column(Float, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    notificado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def message_orm_to_domain(orm: MessageORM) -> ProcessedMessage:
    """Converte uma linha ORM em ``ProcessedMessage`` do domínio."""
    return ProcessedMessage.model_validate(
        {
            "id": str(orm.id),
            "entrada": {
                "texto": orm.texto,
                "remetente": orm.remetente,
                "canal": orm.canal,
            },
            "classificacao": {
                "categoria": orm.categoria,
                "setor": orm.setor,
                "prioridade": orm.prioridade,
                "sentimento": orm.sentimento,
                "resumo": orm.resumo,
                "confianca": orm.confianca,
            },
            "provedor": orm.provider,
            "criado_em": orm.criado_em,
            "notificado": orm.notificado,
        }
    )


def domain_to_message_orm(msg: ProcessedMessage) -> MessageORM:
    """Converte um ``ProcessedMessage`` do domínio em linha ORM."""
    return MessageORM(
        id=uuid.UUID(msg.id),
        texto=msg.entrada.texto,
        remetente=msg.entrada.remetente,
        canal=msg.entrada.canal,
        categoria=msg.classificacao.categoria.value,
        setor=msg.classificacao.setor.value,
        prioridade=msg.classificacao.prioridade.value,
        sentimento=msg.classificacao.sentimento.value,
        resumo=msg.classificacao.resumo,
        confianca=msg.classificacao.confianca,
        provider=msg.provedor,
        notificado=msg.notificado,
        criado_em=msg.criado_em,
    )
