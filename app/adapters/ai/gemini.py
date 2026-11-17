"""Adapter de IA para o Google Gemini (API REST ``generateContent``).

SDK nunca é importado fora de ``app/adapters/ai/`` — aqui usamos a API
REST diretamente via ``httpx``.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.adapters.ai.http import construir_cliente, requisicao_json
from domain.errors import AIProviderError

#: URL base da API do Gemini (v1 generateContent).
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiAIProvider:
    """Implementação de ``AIProvider`` para o Gemini via REST."""

    name: str = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 20.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Inicializa o adapter.

        Args:
            api_key: Chave da API (enviada em header, nunca em log).
            model: Nome do modelo (ex.: ``gemini-2.0-flash``).
            timeout: Timeout em segundos.
            transport: Transporte alternativo para testes (MockTransport).
        """
        self._api_key = api_key
        self._model = model
        self._cliente = construir_cliente(
            BASE_URL, timeout, transport=transport
        )

    async def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        """Gera uma resposta em JSON via ``generateContent``.

        Args:
            system_prompt: Instrução de sistema.
            user_prompt: Prompt do usuário.

        Returns:
            Texto bruto da resposta (esperado: JSON).

        Raises:
            AIProviderError: Timeout, falha de rede, HTTP de erro ou
                resposta sem conteúdo.
        """
        payload: dict[str, Any] = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
            },
        }
        dados = await requisicao_json(
            self._cliente,
            "POST",
            f"/models/{self._model}:generateContent",
            self.name,
            headers={"x-goog-api-key": self._api_key},
            json=payload,
        )

        try:
            candidatos = dados["candidates"]
            texto: str = candidatos[0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise AIProviderError(
                f"{self.name}: resposta sem conteúdo de texto",
                provedor=self.name,
            ) from None
        return texto

    async def aclose(self) -> None:
        """Encerra o cliente HTTP."""
        await self._cliente.aclose()
