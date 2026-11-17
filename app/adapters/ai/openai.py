"""Adapter de IA para a OpenAI (endpoint chat/completions)."""

from __future__ import annotations

import httpx

from app.adapters.ai.openai_compat import OpenAICompatAIProvider

#: URL base da API da OpenAI.
BASE_URL = "https://api.openai.com/v1"


class OpenAIAIProvider(OpenAICompatAIProvider):
    """Implementação de ``AIProvider`` para a OpenAI.

    Mesmo formato do Groq, apontando para ``api.openai.com``.
    """

    name: str = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 20.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Inicializa o adapter apontando para a API da OpenAI.

        Args:
            api_key: Chave da API da OpenAI.
            model: Nome do modelo (ex.: ``gpt-4o-mini``).
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
