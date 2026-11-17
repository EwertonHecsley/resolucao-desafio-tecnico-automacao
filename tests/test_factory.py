"""Testes de aceite da SPEC-03 — factory de provedores de IA."""

import pytest

from app.adapters.ai.factory import build_ai_provider
from app.adapters.ai.fallback import FallbackAIProvider
from app.adapters.ai.gemini import GeminiAIProvider
from app.adapters.ai.groq import GroqAIProvider
from app.adapters.ai.openai import OpenAIAIProvider
from domain.errors import AIProviderError


def _settings(**overrides: object) -> object:
    """Settings parcialmente sobrescrita (evita ler .env do disco)."""

    from app.config import Settings

    base: dict[str, object] = {
        "AI_PROVIDER": "fake",
        "AI_FALLBACK_PROVIDERS": "",
        "AI_TIMEOUT_SECONDS": 5.0,
        "GEMINI_API_KEY": "",
        "GROQ_API_KEY": "",
        "OPENAI_API_KEY": "",
        "_env_file": None,  # não carregar .env local
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


class TestFactoryProvedorValido:
    """Provedores válidos constroem o adapter correto."""

    def test_fake_sem_chave(self) -> None:
        provider = build_ai_provider(_settings(AI_PROVIDER="fake"))  # type: ignore[arg-type]
        assert provider.name == "fake"

    def test_gemini(self) -> None:
        provider = build_ai_provider(
            _settings(AI_PROVIDER="gemini", GEMINI_API_KEY="k")  # type: ignore[arg-type]
        )
        assert isinstance(provider, GeminiAIProvider)

    def test_groq(self) -> None:
        provider = build_ai_provider(
            _settings(AI_PROVIDER="groq", GROQ_API_KEY="k")  # type: ignore[arg-type]
        )
        assert isinstance(provider, GroqAIProvider)

    def test_openai(self) -> None:
        provider = build_ai_provider(
            _settings(AI_PROVIDER="openai", OPENAI_API_KEY="k")  # type: ignore[arg-type]
        )
        assert isinstance(provider, OpenAIAIProvider)


class TestFactoryErros:
    """Provedor desconhecido ou chave ausente → erro claro."""

    def test_provedor_desconhecido_levanta_erro(self) -> None:
        """Guard da factory (settings validam Literal antes, mas por
        defesa a factory também rejeita nomes fora do contrato)."""

        class _StubSettings:
            AI_PROVIDER = "claude"
            AI_FALLBACK_PROVIDERS = ""
            AI_TIMEOUT_SECONDS = 5.0
            GEMINI_API_KEY = ""
            GROQ_API_KEY = ""
            OPENAI_API_KEY = ""

            def fallback_providers(self) -> list[str]:
                return []

        with pytest.raises(AIProviderError, match="desconhecido"):
            build_ai_provider(_StubSettings())  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("provider", "chave"),
        [
            ("gemini", "GEMINI_API_KEY"),
            ("groq", "GROQ_API_KEY"),
            ("openai", "OPENAI_API_KEY"),
        ],
    )
    def test_chave_ausente_levanta_erro(self, provider: str, chave: str) -> None:
        with pytest.raises(AIProviderError, match=chave):
            build_ai_provider(_settings(AI_PROVIDER=provider))  # type: ignore[arg-type]


class TestFactoryFallback:
    """AI_FALLBACK_PROVIDERS monta a cadeia na ordem correta."""

    def test_fallback_montado_na_ordem(self) -> None:
        provider = build_ai_provider(
            _settings(
                AI_PROVIDER="groq",
                GROQ_API_KEY="k",
                AI_FALLBACK_PROVIDERS="gemini,fake",
                GEMINI_API_KEY="k",
            )  # type: ignore[arg-type]
        )
        assert isinstance(provider, FallbackAIProvider)
        assert provider.name == "groq"
        nomes = [p.name for p in provider._providers]  # noqa: SLF001
        assert nomes == ["groq", "gemini", "fake"]

    def test_sem_fallbacks_devolve_provedor_unico(self) -> None:
        provider = build_ai_provider(
            _settings(AI_PROVIDER="fake", AI_FALLBACK_PROVIDERS="")  # type: ignore[arg-type]
        )
        assert not isinstance(provider, FallbackAIProvider)

    def test_fallback_com_provedor_invalido_falha_na_inicializacao(self) -> None:
        """Fallback desconhecido/sem chave => erro cedo, não na 1ª chamada."""
        with pytest.raises(AIProviderError, match="GROQ_API_KEY"):
            build_ai_provider(
                _settings(
                    AI_PROVIDER="fake",
                    AI_FALLBACK_PROVIDERS="groq",
                )  # type: ignore[arg-type]
            )
