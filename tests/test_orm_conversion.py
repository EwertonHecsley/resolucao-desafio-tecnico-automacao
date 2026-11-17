"""Testes unitários da conversão ORM ↔ domínio (SPEC-04).

A conversão vive no adapter (``app.adapters.models``): o domínio não conhece
SQLAlchemy, portanto ``ProcessedMessage`` não expõe ``to_orm()``.
"""

import uuid
from datetime import UTC, datetime

from domain.models import (
    Categoria,
    Classification,
    MessageIn,
    Prioridade,
    ProcessedMessage,
    Sentimento,
    Setor,
)


def _classificacao_valida() -> Classification:
    """Classificação válida reutilizada pelas fábricas de teste."""
    return Classification(
        categoria=Categoria.RECLAMACAO,
        setor=Setor.LOGISTICA,
        prioridade=Prioridade.ALTA,
        sentimento=Sentimento.NEGATIVO,
        resumo="Cliente relata atraso na entrega do pedido.",
        confianca=0.92,
    )


def _message_processada_valida(**overrides: object) -> ProcessedMessage:
    """Fábrica de ProcessedMessage válida, com overrides opcionais."""
    base: dict[str, object] = {
        "id": str(uuid.uuid4()),
        "entrada": MessageIn(texto="Meu pedido ainda não chegou", canal="whatsapp"),
        "classificacao": _classificacao_valida(),
        "provedor": "fake",
        "criado_em": datetime.now(UTC),
    }
    base.update(overrides)
    return ProcessedMessage.model_validate(base)


class TestMessageORMParaProcessedMessage:
    """Conversão de ORM para domínio."""

    def test_orm_para_processada_mapeia_todos_os_campos(self) -> None:
        """MessageORM com todos os campos deve criar ProcessedMessage válido."""
        from app.adapters.models import MessageORM, message_orm_to_domain

        id_ = uuid.uuid4()
        criado_em = datetime.now(UTC)
        mensagem_orm = MessageORM(
            id=id_,
            texto="Teste de texto",
            remetente="test@example.com",
            canal="whatsapp",
            categoria="reclamacao",
            setor="logistica",
            prioridade="alta",
            sentimento="negativo",
            resumo="Resumo do teste",
            confianca=0.85,
            provider="fake",
            notificado=False,
            criado_em=criado_em,
        )

        mensagem_processada = message_orm_to_domain(mensagem_orm)

        assert mensagem_processada.id == str(id_)
        assert mensagem_processada.entrada.texto == "Teste de texto"
        assert mensagem_processada.entrada.remetente == "test@example.com"
        assert mensagem_processada.entrada.canal == "whatsapp"
        assert mensagem_processada.classificacao.categoria == Categoria.RECLAMACAO
        assert mensagem_processada.classificacao.setor == Setor.LOGISTICA
        assert mensagem_processada.classificacao.prioridade == Prioridade.ALTA
        assert mensagem_processada.classificacao.sentimento == Sentimento.NEGATIVO
        assert mensagem_processada.classificacao.resumo == "Resumo do teste"
        assert mensagem_processada.classificacao.confianca == 0.85
        assert mensagem_processada.provedor == "fake"
        assert mensagem_processada.notificado is False
        assert mensagem_processada.criado_em == criado_em

    def test_orm_para_processada_tolerancia_para_campos_null(self) -> None:
        """MessageORM com campos opcionais deve funcionar corretamente."""
        from app.adapters.models import MessageORM, message_orm_to_domain

        mensagem_orm = MessageORM(
            id=uuid.uuid4(),
            texto="Texto sem remetente",
            remetente=None,
            canal=None,
            categoria="elogio",
            setor="suporte",
            prioridade="baixa",
            sentimento="positivo",
            resumo="Elogio sem contexto",
            confianca=0.95,
            provider="fake",
            notificado=False,
            criado_em=datetime.now(UTC),
        )

        mensagem_processada = message_orm_to_domain(mensagem_orm)

        assert mensagem_processada.entrada.remetente is None
        assert mensagem_processada.entrada.canal is None
        assert mensagem_processada.entrada.texto == "Texto sem remetente"

    def test_orm_para_processada_preserva_notificado_true(self) -> None:
        """O flag notificado deve sobreviver à conversão ORM → domínio."""
        from app.adapters.models import MessageORM, message_orm_to_domain

        mensagem_orm = MessageORM(
            id=uuid.uuid4(),
            texto="Já notificado",
            remetente=None,
            canal=None,
            categoria="duvida",
            setor="geral",
            prioridade="media",
            sentimento="neutro",
            resumo="Dúvida já enviada ao n8n",
            confianca=0.7,
            provider="fake",
            notificado=True,
            criado_em=datetime.now(UTC),
        )

        mensagem_processada = message_orm_to_domain(mensagem_orm)

        assert mensagem_processada.notificado is True


class TestProcessedMessageParaORM:
    """Conversão de domínio para ORM."""

    def test_processada_para_orm_cria_todos_os_campos(self) -> None:
        """ProcessedMessage deve criar MessageORM com todos os campos."""
        from app.adapters.models import MessageORM, domain_to_message_orm

        mensagem_processada = _message_processada_valida()

        mensagem_orm = domain_to_message_orm(mensagem_processada)

        assert isinstance(mensagem_orm, MessageORM)
        assert isinstance(mensagem_orm.id, uuid.UUID)
        assert mensagem_orm.texto == mensagem_processada.entrada.texto
        assert mensagem_orm.remetente == mensagem_processada.entrada.remetente
        assert mensagem_orm.canal == mensagem_processada.entrada.canal
        assert mensagem_orm.categoria == mensagem_processada.classificacao.categoria.value
        assert mensagem_orm.setor == mensagem_processada.classificacao.setor.value
        assert mensagem_orm.prioridade == mensagem_processada.classificacao.prioridade.value
        assert mensagem_orm.sentimento == mensagem_processada.classificacao.sentimento.value
        assert mensagem_orm.resumo == mensagem_processada.classificacao.resumo
        assert mensagem_orm.confianca == mensagem_processada.classificacao.confianca
        assert mensagem_orm.provider == mensagem_processada.provedor
        assert mensagem_orm.notificado is False
        assert mensagem_orm.criado_em == mensagem_processada.criado_em

    def test_processada_para_orm_sem_remetente_canal_usa_none(self) -> None:
        """ProcessedMessage com remetente/canal None deve criar ORM corretamente."""
        from app.adapters.models import MessageORM, domain_to_message_orm

        mensagem_processada = _message_processada_valida(
            entrada=MessageIn(texto="Texto sem metadados", remetente=None, canal=None),
        )

        mensagem_orm = domain_to_message_orm(mensagem_processada)

        assert isinstance(mensagem_orm, MessageORM)
        assert mensagem_orm.remetente is None
        assert mensagem_orm.canal is None

    def test_round_trip_preserva_dados(self) -> None:
        """Domínio → ORM → domínio não deve perder informações."""
        from app.adapters.models import domain_to_message_orm, message_orm_to_domain

        original = _message_processada_valida(notificado=True)

        resultado = message_orm_to_domain(domain_to_message_orm(original))

        assert resultado == original
