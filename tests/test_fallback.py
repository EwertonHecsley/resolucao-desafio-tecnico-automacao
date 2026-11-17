"""Testes de aceite da SPEC-03 — FallbackAIProvider."""

import pytest

from app.adapters.ai.fake import MARCADOR_ERRO, FakeAIProvider
from app.adapters.ai.fallback import FallbackAIProvider
from domain.errors import AIProviderError

SYSTEM = "system"
USER = "user"


def _fake(nome: str, respostas: list[str]) -> FakeAIProvider:
    """FakeAIProvider com ``name`` customizado (simula provedor real)."""
    fake = FakeAIProvider(respostas)
    fake.name = nome
    return fake


class TestFallback:
    """Cenários de fallback sequencial."""

    async def test_primeiro_falha_segundo_responde(self) -> None:
        """1º levanta erro → 2º responde; name reflete o 2º."""
        cadeia = [
            _fake("primario", [MARCADOR_ERRO]),
            _fake("secundario", ['{"ok": true}']),
        ]
        fallback = FallbackAIProvider(cadeia)
        assert fallback.name == "primario"
        resultado = await fallback.generate_json(SYSTEM, USER)
        assert resultado == '{"ok": true}'
        assert fallback.name == "secundario"

    async def test_primeiro_responde_sem_chamar_os_demais(self) -> None:
        """1º responde → os demais não são chamados."""
        cadeia = [
            _fake("primario", ['{"ok": true}']),
            _fake("secundario", ['{"nao": "chamado"}']),
        ]
        fallback = FallbackAIProvider(cadeia)
        resultado = await fallback.generate_json(SYSTEM, USER)
        assert resultado == '{"ok": true}'
        assert fallback.name == "primario"

    async def test_todos_falham_levanta_erro_agregado(self) -> None:
        """Todos falham → AIProviderError com motivos de cada um."""
        cadeia = [
            _fake("primario", [MARCADOR_ERRO]),
            _fake("secundario", [MARCADOR_ERRO]),
        ]
        fallback = FallbackAIProvider(cadeia)
        with pytest.raises(AIProviderError) as excinfo:
            await fallback.generate_json(SYSTEM, USER)
        mensagem = str(excinfo.value)
        assert "primario" in mensagem and "secundario" in mensagem

    async def test_lista_vazia_levanta_erro(self) -> None:
        """Sem provedores → erro claro na construção."""
        with pytest.raises(AIProviderError, match="ao menos um"):
            FallbackAIProvider([])

    async def test_name_inicial_e_o_primeiro_provedor(self) -> None:
        """name começa apontando para o primário."""
        fallback = FallbackAIProvider([_fake("a", []), _fake("b", [])])
        assert fallback.name == "a"
