"""Adapters de IA — implementações de AIProvider (SPEC-03).

Adapters REST (gemini/groq/openai) usam httpx; o fake serve para testes.
A factory escolhe pelo ``AI_PROVIDER`` do ambiente.
"""

from app.adapters.ai.factory import build_ai_provider
from app.adapters.ai.fake import MARCADOR_ERRO, FakeAIProvider
from app.adapters.ai.fallback import FallbackAIProvider
from app.adapters.ai.gemini import GeminiAIProvider
from app.adapters.ai.groq import GroqAIProvider
from app.adapters.ai.openai import OpenAIAIProvider

__all__ = [
    "FakeAIProvider",
    "FallbackAIProvider",
    "GeminiAIProvider",
    "GroqAIProvider",
    "MARCADOR_ERRO",
    "OpenAIAIProvider",
    "build_ai_provider",
]
