"""Adapter base para APIs compatíveis com OpenAI (Groq, OpenAI).

Ambos expõem ``chat/completions`` com ``response_format: json_object``
e resposta em ``choices[0].message.content``.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.adapters.ai.http import construir_cliente, requisicao_json
from domain.errors import AIProviderError


class OpenAICompatAIProvider:
    """Implementação de ``AIProvider`` para endpoints compatíveis com OpenAI.

    Subclasses configuram ``name`` e a URL base.
    """

    name: str = "openai-compat"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 20.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Inicializa o adapter.

        Args:
            base_url: URL base do endpoint compatível.
            api_key: Chave da API (enviada em header Bearer).
            model: Nome do modelo.
            timeout: Timeout em segundos.
            transport: Transporte alternativo para testes (MockTransport).
        """
        self._api_key = api_key
        self._model = model
        self._cliente = construir_cliente(
            base_url, timeout, transport=transport
        )

    async def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        """Gera uma resposta em JSON via ``chat/completions``.

        Args:
            system_prompt: Instrução de sistema (mensagem ``system``).
            user_prompt: Prompt do usuário (mensagem ``user``).

        Returns:
            Texto bruto da resposta (esperado: JSON).

        Raises:
            AIProviderError: Timeout, falha de rede, HTTP de erro ou
                resposta sem conteúdo.
        """
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        dados = await requisicao_json(
            self._cliente,
            "POST",
            "/chat/completions",
            self.name,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json=payload,
        )

        try:
            texto: str = dados["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise AIProviderError(
                f"{self.name}: resposta sem conteúdo de texto",
                provedor=self.name,
            ) from None
        return texto

    async def aclose(self) -> None:
        """Encerra o cliente HTTP."""
        await self._cliente.aclose()
