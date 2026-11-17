"""Modelos de domínio da aplicação.

Define os tipos que atravessam as camadas: entrada do usuário
(``MessageIn``), resultado da classificação (``Classification``) e a
mensagem processada persistida (``ProcessedMessage``).
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Categoria(StrEnum):
    """Categoria da mensagem do cliente."""

    DUVIDA = "duvida"
    RECLAMACAO = "reclamacao"
    SOLICITACAO = "solicitacao"
    ELOGIO = "elogio"
    OUTRO = "outro"


class Setor(StrEnum):
    """Setor responsável por atender a mensagem."""

    SUPORTE = "suporte"
    FINANCEIRO = "financeiro"
    COMERCIAL = "comercial"
    LOGISTICA = "logistica"
    GERAL = "geral"


class Prioridade(StrEnum):
    """Prioridade de atendimento da mensagem."""

    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


class Sentimento(StrEnum):
    """Sentimento detectado na mensagem."""

    POSITIVO = "positivo"
    NEUTRO = "neutro"
    NEGATIVO = "negativo"


class MessageIn(BaseModel):
    """Mensagem enviada pelo cliente para classificação."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "texto": "Meu pedido ainda não chegou, o que aconteceu?",
                "remetente": "joao@example.com",
                "canal": "whatsapp",
            }
        }
    )

    texto: str = Field(min_length=1, max_length=5000)
    remetente: str | None = None
    canal: str | None = None


class Classification(BaseModel):
    """Resultado da classificação realizada pela IA.

    Todos os campos são validados: enums restritos, resumo limitado a
    200 caracteres e ``confianca`` no intervalo fechado [0, 1].
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categoria": "reclamacao",
                "setor": "logistica",
                "prioridade": "alta",
                "sentimento": "negativo",
                "resumo": "Cliente relata atraso na entrega do pedido.",
                "confianca": 0.92,
            }
        }
    )

    categoria: Categoria
    setor: Setor
    prioridade: Prioridade
    sentimento: Sentimento
    resumo: str = Field(min_length=1, max_length=200)
    confianca: float = Field(ge=0, le=1)

    @field_validator("confianca")
    @classmethod
    def validar_confianca_finita(cls, valor: float) -> float:
        """Garante que a confiança é um número finito (não NaN/inf).

        Args:
            valor: Valor de confiança informado pela IA.

        Returns:
            O mesmo valor, se finito.

        Raises:
            ValueError: Se o valor não for finito.
        """
        import math

        if not math.isfinite(valor):
            mensagem = "confianca deve ser um número finito entre 0 e 1"
            raise ValueError(mensagem)
        return valor


class ProcessedMessage(BaseModel):
    """Mensagem processada: entrada, classificação e metadados de execução."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "9b6f1a2e-4c3d-4e5f-8a7b-1c2d3e4f5a6b",
                "entrada": {
                    "texto": "Meu pedido ainda não chegou, o que aconteceu?",
                    "remetente": "joao@example.com",
                    "canal": "whatsapp",
                },
                "classificacao": {
                    "categoria": "reclamacao",
                    "setor": "logistica",
                    "prioridade": "alta",
                    "sentimento": "negativo",
                    "resumo": "Cliente relata atraso na entrega do pedido.",
                    "confianca": 0.92,
                },
                "provedor": "openai",
                "criado_em": "2026-11-17T10:00:00Z",
            }
        }
    )

    id: str
    entrada: MessageIn
    classificacao: Classification
    provedor: str
    criado_em: datetime
