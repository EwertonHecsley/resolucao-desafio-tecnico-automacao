"""Ports de domínio - interfaces definidas pelo negócio."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict


class IAProvider(ABC):
    """Porta para provedores de IA.

    Esta interface representa a abstração de classificação de mensagens.
    Qualquer provedor real (OpenAI, Google, etc.) deve implementar este contrato.
    """

    @abstractmethod
    async def classify(
        self,
        message: str,
        meta: dict[str, Any] | None = None,
    ) -> str:
        """
        Classifica uma mensagem enviada por um cliente.

        Args:
            message: A mensagem a ser classificada.
            meta: Metadatos opcionais (timestamp, user_id, etc.).

        Returns:
            A categoria de classificação (ex: "suporte técnico").

        Raises:
            ClassificationError: Se houver erro ao classificar.
        """
        pass


class ClassificationResult(BaseModel):
    """Resultado de uma classificação realizada pela IA."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category": "suporte técnico",
                "confidence": 0.95,
                "reasoning": "Mensagem menciona pedido e produto",
            }
        }
    )

    category: str
    confidence: float
    reasoning: str = ""
