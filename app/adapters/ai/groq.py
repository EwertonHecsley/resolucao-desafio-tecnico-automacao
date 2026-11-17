"""Adapter de IA para o Groq (endpoint compatível com OpenAI)."""

from __future__ import annotations

import httpx

from app.adapters.ai.openai_compat import OpenAICompatAIProvider

#: URL base da API do Groq.
BASE_URL = "https://api.groq.com/openai/v1"


class GroqAIProvider(OpenAICompatAIProvider):
    """Implementação de ``AIProvider`` para o Groq.

    Formato de requisição idêntico ao da OpenAI
    (``response_format: {"type": "json_object"}``, ``temperature`` baixa).
    """

    name: str = "groq"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 20.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Inicializa o adapter apontando para a API do Groq.

        Args:
            api_key: Chave da API do Groq.
            model: Nome do modelo (ex.: ``llama-3.3-70b-versatile``).
            timeout: Timeout em segundos.
            transport: Transporte alternativo para testes (MockTransport).
        """
        super().__init__(
            base_url=BASE_URL,
            api_key=api_key,
            model=model,
            timeout=timeout,
            transport=transport,
        )
