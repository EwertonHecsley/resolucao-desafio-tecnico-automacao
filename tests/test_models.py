"""Testes de aceite da SPEC-01 — validação dos modelos de domínio.

Cobertura exigida pela SPEC: limites de ``MessageIn.texto``, enums
inválidos e ``confianca`` fora de 0–1.
"""

import math

import pytest
from pydantic import ValidationError

from domain.models import (
    Categoria,
    Classification,
    MessageIn,
    Prioridade,
    ProcessedMessage,
    Sentimento,
    Setor,
)


def _classificacao_valida(**overrides: object) -> dict[str, object]:
    """Fábrica de payload de classificação válida, com overrides opcionais."""
    base: dict[str, object] = {
        "categoria": Categoria.RECLAMACAO,
        "setor": Setor.LOGISTICA,
        "prioridade": Prioridade.ALTA,
        "sentimento": Sentimento.NEGATIVO,
        "resumo": "Cliente relata atraso na entrega do pedido.",
        "confianca": 0.92,
    }
    base.update(overrides)
    return base


class TestMessageIn:
    """Limites da mensagem de entrada."""

    def test_texto_vazio_rejeitado(self) -> None:
        """Texto vazio (0 char) deve ser rejeitado — mínimo é 1."""
        with pytest.raises(ValidationError):
            MessageIn(texto="")

    def test_texto_5000_chars_aceito(self) -> None:
        """Texto com exatamente 5000 chars é aceito."""
        mensagem = MessageIn(texto="a" * 5000)
        assert mensagem.texto == "a" * 5000

    def test_texto_5001_chars_rejeitado(self) -> None:
        """Texto com 5001 chars deve ser rejeitado — máximo é 5000."""
        with pytest.raises(ValidationError):
            MessageIn(texto="a" * 5001)

    def test_texto_1_char_aceito(self) -> None:
        """Texto com 1 char é aceito (mínimo)."""
        assert MessageIn(texto="a").texto == "a"

    def test_campos_opcionais_padrao_none(self) -> None:
        """Remetente e canal são opcionais e padrão None."""
        mensagem = MessageIn(texto="Olá")
        assert mensagem.remetente is None
        assert mensagem.canal is None

    def test_campos_opcionais_preenchidos(self) -> None:
        """Remetente e canal aceitam valores informados."""
        mensagem = MessageIn(texto="Olá", remetente="joao@example.com", canal="whatsapp")
        assert mensagem.remetente == "joao@example.com"
        assert mensagem.canal == "whatsapp"


class TestClassification:
    """Validação dos campos da classificação."""

    def test_classificacao_valida_aceita(self) -> None:
        """Payload completo e válido é aceito."""
        classificacao = Classification(**_classificacao_valida())
        assert classificacao.categoria is Categoria.RECLAMACAO
        assert classificacao.setor is Setor.LOGISTICA
        assert classificacao.prioridade is Prioridade.ALTA
        assert classificacao.sentimento is Sentimento.NEGATIVO
        assert classificacao.confianca == 0.92

    @pytest.mark.parametrize(
        ("campo", "valor_invalido"),
        [
            ("categoria", "pergunta"),
            ("setor", "tecnico"),
            ("prioridade", "urgente"),
            ("sentimento", "feliz"),
        ],
        ids=["categoria", "setor", "prioridade", "sentimento"],
    )
    def test_enum_invalido_rejeitado(
        self, campo: str, valor_invalido: str
    ) -> None:
        """Valores fora dos enums definidos devem ser rejeitados."""
        payload = _classificacao_valida(**{campo: valor_invalido})
        with pytest.raises(ValidationError):
            Classification(**payload)  # type: ignore[arg-type]

    def test_enums_aceitam_valores_validos(self) -> None:
        """Todos os valores válidos de cada enum são aceitos."""
        for categoria in Categoria:
            payload = _classificacao_valida(categoria=categoria)
            assert Classification(**payload).categoria is categoria
        for setor in Setor:
            payload = _classificacao_valida(setor=setor)
            assert Classification(**payload).setor is setor
        for prioridade in Prioridade:
            payload = _classificacao_valida(prioridade=prioridade)
            assert Classification(**payload).prioridade is prioridade
        for sentimento in Sentimento:
            payload = _classificacao_valida(sentimento=sentimento)
            assert Classification(**payload).sentimento is sentimento

    @pytest.mark.parametrize("confianca", [-0.01, 1.01, -1.0, 2.0])
    def test_confianca_fora_do_intervalo_rejeitada(self, confianca: float) -> None:
        """Confiança fora de 0–1 deve ser rejeitada."""
        payload = _classificacao_valida(confianca=confianca)
        with pytest.raises(ValidationError):
            Classification(**payload)

    @pytest.mark.parametrize("confianca", [0.0, 0.5, 1.0])
    def test_confianca_nos_limites_aceita(self, confianca: float) -> None:
        """Confiança nos extremos 0 e 1 é aceita (intervalo fechado)."""
        payload = _classificacao_valida(confianca=confianca)
        assert Classification(**payload).confianca == confianca

    def test_confianca_nan_rejeitada(self) -> None:
        """Confiança NaN deve ser rejeitada (não é número finito)."""
        payload = _classificacao_valida(confianca=math.nan)
        with pytest.raises(ValidationError):
            Classification(**payload)

    def test_resumo_200_chars_aceito(self) -> None:
        """Resumo com exatamente 200 chars é aceito."""
        payload = _classificacao_valida(resumo="a" * 200)
        assert Classification(**payload).resumo == "a" * 200

    def test_resumo_201_chars_rejeitado(self) -> None:
        """Resumo com 201 chars deve ser rejeitado — máximo é 200."""
        payload = _classificacao_valida(resumo="a" * 201)
        with pytest.raises(ValidationError):
            Classification(**payload)

    def test_resumo_vazio_rejeitado(self) -> None:
        """Resumo vazio deve ser rejeitado — mínimo é 1."""
        payload = _classificacao_valida(resumo="")
        with pytest.raises(ValidationError):
            Classification(**payload)


class TestProcessedMessage:
    """Mensagem processada agrega entrada e classificação."""

    def test_processada_valida_aceita(self) -> None:
        """Processada com entrada + classificação válidas é aceita."""
        mensagem = ProcessedMessage(
            id="id-1",
            entrada=MessageIn(texto="Meu pedido não chegou"),
            classificacao=Classification(**_classificacao_valida()),
            provedor="fake",
            criado_em="2026-11-17T10:00:00Z",
        )
        assert mensagem.id == "id-1"
        assert mensagem.provedor == "fake"
        assert mensagem.entrada.texto == "Meu pedido não chegou"

    def test_entrada_invalida_rejeitada(self) -> None:
        """Entrada inválida (texto vazio) deve ser rejeitada em cascata."""
        with pytest.raises(ValidationError):
            ProcessedMessage(
                id="id-2",
                entrada=MessageIn(texto=""),  # type: ignore[arg-type]
                classificacao=Classification(**_classificacao_valida()),
                provedor="fake",
                criado_em="2026-11-17T10:00:00Z",
            )

    def test_classificacao_invalida_rejeitada(self) -> None:
        """Classificação inválida (confianca > 1) deve ser rejeitada em cascata."""
        with pytest.raises(ValidationError):
            ProcessedMessage(
                id="id-3",
                entrada=MessageIn(texto="Olá"),
                classificacao=Classification(**_classificacao_valida(confianca=1.5)),
                provedor="fake",
                criado_em="2026-11-17T10:00:00Z",
            )
