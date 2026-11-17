"""Testes de aceite da SPEC-03 — adapters de IA reais via httpx.MockTransport.

Nenhum teste toca a rede: todas as respostas HTTP são simuladas.
"""

import json
from typing import Any

import httpx
import pytest

from app.adapters.ai.gemini import GeminiAIProvider
from app.adapters.ai.groq import GroqAIProvider
from app.adapters.ai.openai import OpenAIAIProvider
from domain.errors import AIProviderError

SYSTEM = "Você é um classificador."
USER = "Classifique esta mensagem."

PAYLOAD_GEMINI = {
    "candidates": [
        {"content": {"parts": [{"text": '{"categoria": "duvida"}'}]}}
    ]
}
PAYLOAD_COMPAT = {
    "choices": [
        {"message": {"content": '{"categoria": "duvida"}'}}
    ]
}

TERMINAL = "http://test"  # nunca usado: transport intercepta tudo


def _transport(status: int, corpo: str) -> httpx.MockTransport:
    """Transporte que responde sempre igual (independe do request)."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text=corpo)

    return httpx.MockTransport(handler)


def _transport_inspector(
    resposta: dict[str, Any],
) -> tuple[httpx.MockTransport, list[httpx.Request]]:
    """Transporte que grava as requisições e responde com payload fixo."""
    requisicoes: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requisicoes.append(request)
        return httpx.Response(200, json=resposta)

    return httpx.MockTransport(handler), requisicoes


class TestGeminiAdapter:
    """Gemini — sucesso e erros via MockTransport."""

    def _provider(self, transport: httpx.AsyncBaseTransport) -> GeminiAIProvider:
        return GeminiAIProvider(
            api_key="chave-teste",
            model="gemini-2.0-flash",
            timeout=1.0,
            transport=transport,
        )

    async def test_sucesso_retorna_texto_do_payload(self) -> None:
        transport, reqs = _transport_inspector(PAYLOAD_GEMINI)
        provider = self._provider(transport)
        resultado = await provider.generate_json(SYSTEM, USER)
        assert resultado == '{"categoria": "duvida"}'
        # Chave enviada em header, corpo com instrução de sistema e JSON.
        assert reqs[0].headers["x-goog-api-key"] == "chave-teste"
        corpo = json.loads(reqs[0].content)
        assert corpo["system_instruction"]["parts"][0]["text"] == SYSTEM
        assert corpo["contents"][0]["parts"][0]["text"] == USER
        assert (
            corpo["generationConfig"]["responseMimeType"] == "application/json"
        )
        assert reqs[0].url.path.endswith(
            "/models/gemini-2.0-flash:generateContent"
        )
        assert reqs[0].url.host == "generativelanguage.googleapis.com"

    async def test_timeout_levanta_ai_provider_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("timeout simulado")

        provider = self._provider(httpx.MockTransport(handler))
        with pytest.raises(AIProviderError, match="timeout"):
            await provider.generate_json(SYSTEM, USER)

    async def test_falha_de_rede_levanta_ai_provider_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("conexão recusada simulada")

        provider = self._provider(httpx.MockTransport(handler))
        with pytest.raises(AIProviderError, match="rede"):
            await provider.generate_json(SYSTEM, USER)

    @pytest.mark.parametrize("status", [401, 403, 429, 500])
    async def test_http_erros_levanta_ai_provider_error(
        self, status: int
    ) -> None:
        provider = self._provider(_transport(status, "{}"))
        with pytest.raises(AIProviderError):
            await provider.generate_json(SYSTEM, USER)

    async def test_resposta_sem_conteudo_levanta_erro(self) -> None:
        provider = self._provider(_transport(200, json.dumps({"candidates": []})))
        with pytest.raises(AIProviderError, match="sem conteúdo"):
            await provider.generate_json(SYSTEM, USER)

    async def test_erro_nao_vaza_a_chave(self) -> None:
        provider = self._provider(_transport(401, '{"error": "chave-teste"}'))
        with pytest.raises(AIProviderError) as excinfo:
            await provider.generate_json(SYSTEM, USER)
        assert "chave-teste" not in str(excinfo.value)


class TestGroqAdapter:
    """Groq — sucesso e erros via MockTransport."""

    def _provider(self, transport: httpx.AsyncBaseTransport) -> GroqAIProvider:
        return GroqAIProvider(
            api_key="chave-teste",
            model="llama-3.3-70b-versatile",
            timeout=1.0,
            transport=transport,
        )

    async def test_sucesso_retorna_texto_do_payload(self) -> None:
        transport, reqs = _transport_inspector(PAYLOAD_COMPAT)
        provider = self._provider(transport)
        resultado = await provider.generate_json(SYSTEM, USER)
        assert resultado == '{"categoria": "duvida"}'
        assert reqs[0].url.host == "api.groq.com"
        assert reqs[0].url.path == "/openai/v1/chat/completions"
        assert reqs[0].headers["Authorization"] == "Bearer chave-teste"
        corpo = json.loads(reqs[0].content)
        assert corpo["response_format"] == {"type": "json_object"}
        assert 0 <= corpo["temperature"] <= 0.2
        assert corpo["messages"][0]["role"] == "system"
        assert corpo["messages"][0]["content"] == SYSTEM

    async def test_timeout_levanta_ai_provider_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout simulado")

        provider = self._provider(httpx.MockTransport(handler))
        with pytest.raises(AIProviderError, match="timeout"):
            await provider.generate_json(SYSTEM, USER)

    @pytest.mark.parametrize("status", [401, 429, 502])
    async def test_http_erros_levanta_ai_provider_error(
        self, status: int
    ) -> None:
        provider = self._provider(_transport(status, "{}"))
        with pytest.raises(AIProviderError):
            await provider.generate_json(SYSTEM, USER)

    async def test_resposta_nao_json_levanta_erro(self) -> None:
        provider = self._provider(_transport(200, "não é json"))
        with pytest.raises(AIProviderError, match="JSON"):
            await provider.generate_json(SYSTEM, USER)


class TestOpenAIAdapter:
    """OpenAI — sucesso e erros via MockTransport (mesmo formato do Groq)."""

    def _provider(self, transport: httpx.AsyncBaseTransport) -> OpenAIAIProvider:
        return OpenAIAIProvider(
            api_key="chave-teste",
            model="gpt-4o-mini",
            timeout=1.0,
            transport=transport,
        )

    async def test_sucesso_retorna_texto_do_payload(self) -> None:
        transport, reqs = _transport_inspector(PAYLOAD_COMPAT)
        provider = self._provider(transport)
        resultado = await provider.generate_json(SYSTEM, USER)
        assert resultado == '{"categoria": "duvida"}'
        assert reqs[0].url.host == "api.openai.com"
        assert reqs[0].url.path == "/v1/chat/completions"
        corpo = json.loads(reqs[0].content)
        assert corpo["model"] == "gpt-4o-mini"
        assert corpo["response_format"] == {"type": "json_object"}

    @pytest.mark.parametrize("status", [401, 429])
    async def test_http_erros_levanta_ai_provider_error(
        self, status: int
    ) -> None:
        provider = self._provider(_transport(status, "{}"))
        with pytest.raises(AIProviderError):
            await provider.generate_json(SYSTEM, USER)
