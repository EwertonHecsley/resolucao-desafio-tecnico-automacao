"""Factory de provedores de IA (SPEC-03).

Constrói o ``AIProvider`` a partir das Settings. Provedor desconhecido
ou chave ausente de provedor real => erro claro na inicialização.
"""

from __future__ import annotations

from app.adapters.ai.fake import FakeAIProvider
from app.adapters.ai.fallback import FallbackAIProvider
from app.adapters.ai.gemini import GeminiAIProvider
from app.adapters.ai.groq import GroqAIProvider
from app.adapters.ai.openai import OpenAIAIProvider
from app.config import Settings
from domain.errors import AIProviderError
from domain.ports import AIProvider

#: Chaves exigidas por cada provedor real (nome da setting).
_CHAVES_EXIGIDAS: dict[str, str] = {
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
}

#: Modelos por provedor (nome da setting).
_MODELS: dict[str, str] = {
    "gemini": "GEMINI_MODEL",
    "groq": "GROQ_MODEL",
    "openai": "OPENAI_MODEL",
}


def _construir_provedor(nome: str, settings: Settings) -> AIProvider:
    """Constrói um provedor único a partir do nome.

    Args:
        nome: Nome do provedor (``fake|gemini|groq|openai``).
        settings: Configurações da aplicação.

    Returns:
        Instância do provedor.

    Raises:
        AIProviderError: Provedor desconhecido ou chave ausente.
    """
    if nome == "fake":
        return FakeAIProvider()

    chave_esperada = _CHAVES_EXIGIDAS.get(nome)
    if chave_esperada is None:
        raise AIProviderError(
            f"Provedor de IA desconhecido: '{nome}' "
            "(válidos: fake, gemini, groq, openai)"
        )

    chave = getattr(settings, chave_esperada)
    if not chave.strip():
        raise AIProviderError(
            f"Provedor '{nome}' exige a variável {chave_esperada} "
            "no ambiente/.env"
        )

    model = getattr(settings, _MODELS[nome])
    timeout = settings.AI_TIMEOUT_SECONDS
    match nome:
        case "gemini":
            return GeminiAIProvider(api_key=chave, model=model, timeout=timeout)
        case "groq":
            return GroqAIProvider(api_key=chave, model=model, timeout=timeout)
        case "openai":
            return OpenAIAIProvider(api_key=chave, model=model, timeout=timeout)
        case _:  # inatingível — Literal garante os 4 nomes
            raise AIProviderError(f"Provedor de IA desconhecido: '{nome}'")


def build_ai_provider(settings: Settings) -> AIProvider:
    """Constrói o provedor de IA (ou cadeia de fallback) a partir das settings.

    Args:
        settings: Configurações da aplicação (``AI_PROVIDER``,
            ``AI_FALLBACK_PROVIDERS``, chaves e modelos).

    Returns:
        Provedor único ou ``FallbackAIProvider`` com a ordem
        ``[AI_PROVIDER, *fallbacks]``.

    Raises:
        AIProviderError: Provedor desconhecido ou chave ausente —
            deve falhar cedo, na inicialização.
    """
    principal = _construir_provedor(settings.AI_PROVIDER, settings)
    fallbacks = settings.fallback_providers()
    if not fallbacks:
        return principal

    cadeia = [principal, *(
        _construir_provedor(nome, settings) for nome in fallbacks
    )]
    return FallbackAIProvider(cadeia)
