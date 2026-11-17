"""Testes de integração do repository PostgreSQL (SPEC-04).

Testes marcados com @pytest.mark.integration são pulados quando DATABASE_URL
não estiver configurada, mantendo a suíte padrão independente de banco.
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.repository_postgres import PostgresMessageRepository
from domain.models import ProcessedMessage


def _mensagem_valida(
    *,
    texto: str = "Meu pedido ainda não chegou",
    id_: uuid.UUID | None = None,
    criado_em: datetime | None = None,
) -> ProcessedMessage:
    """Fábrica de ProcessedMessage válida para os testes de integração."""
    return ProcessedMessage.model_validate(
        {
            "id": str(id_ or uuid.uuid4()),
            "entrada": {"texto": texto, "canal": "whatsapp"},
            "classificacao": {
                "categoria": "reclamacao",
                "setor": "logistica",
                "prioridade": "alta",
                "sentimento": "negativo",
                "resumo": "Cliente relata atraso na entrega do pedido.",
                "confianca": 0.92,
            },
            "provedor": "fake",
            "criado_em": criado_em or datetime.now(UTC),
            "notificado": False,
        }
    )


@pytest.mark.integration
class TestPostgresMessageRepository:
    """Testes de integração com banco PostgreSQL real."""

    async def test_save_salva_e_retorna_mensagem(self, db_session: AsyncSession) -> None:
        """save deve persistir a mensagem e retornar a versão salva."""
        repository = PostgresMessageRepository(db_session)
        mensagem = _mensagem_valida()

        mensagem_salva = await repository.save(mensagem)

        assert mensagem_salva.id == mensagem.id
        assert mensagem_salva.entrada.texto == mensagem.entrada.texto
        assert mensagem_salva.provedor == mensagem.provedor

    async def test_get_recupera_mensagem_salva(self, db_session: AsyncSession) -> None:
        """get deve recuperar mensagem pelo ID."""
        repository = PostgresMessageRepository(db_session)
        mensagem_original = _mensagem_valida()

        await repository.save(mensagem_original)
        mensagem_recuperada = await repository.get(mensagem_original.id)

        assert mensagem_recuperada is not None
        assert mensagem_recuperada.id == mensagem_original.id
        assert mensagem_recuperada.entrada.texto == mensagem_original.entrada.texto

    async def test_get_id_inexistente_retorna_none(self, db_session: AsyncSession) -> None:
        """get com ID não existente deve retornar None."""
        repository = PostgresMessageRepository(db_session)

        mensagem = await repository.get(str(uuid.uuid4()))

        assert mensagem is None

    async def test_list_retorna_ultimas_n_mensagens_ordenadas(
        self, db_session: AsyncSession
    ) -> None:
        """list deve retornar até N mensagens ordenadas do mais recente."""
        repository = PostgresMessageRepository(db_session)
        agora = datetime.now(UTC)
        ids = [uuid.uuid4() for _ in range(4)]

        for indice, id_ in enumerate(ids):
            await repository.save(
                _mensagem_valida(
                    id_=id_,
                    texto=f"Mensagem {indice}",
                    criado_em=agora.replace(microsecond=indice),
                )
            )

        mensagens = await repository.list(limit=3)

        assert len(mensagens) == 3
        assert mensagens[0].id == str(ids[-1])  # Mais recente primeiro
        assert mensagens[1].id == str(ids[-2])
        assert mensagens[2].id == str(ids[-3])

    async def test_mark_notificado_marca_mensagem(self, db_session: AsyncSession) -> None:
        """mark_notificado deve alterar o campo notificado."""
        repository = PostgresMessageRepository(db_session)
        mensagem = _mensagem_valida(texto="Teste de notificação")

        await repository.save(mensagem)
        assert await repository.get(mensagem.id) is not None

        await repository.mark_notified(mensagem.id)
        mensagem_atualizada = await repository.get(mensagem.id)

        assert mensagem_atualizada is not None
        assert mensagem_atualizada.notificado is True

    async def test_mark_notificado_id_inexistente_nao_erro(
        self, db_session: AsyncSession
    ) -> None:
        """mark_notificado com ID inexistente não deve lançar erro."""
        repository = PostgresMessageRepository(db_session)

        await repository.mark_notified(str(uuid.uuid4()))

        # Não deve lançar erro
        assert True
