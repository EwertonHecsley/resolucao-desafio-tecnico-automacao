"""Configuração da aplicação usando Pydantic Settings (SPEC-03).

Todas as variáveis de IA são lidas do ambiente/``.env``. Segredos nunca
são commitados — ver ``.env.example`` para os nomes esperados.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

AIProviderName = Literal["fake", "gemini", "groq", "openai"]


class Settings(BaseSettings):
    """Configurações da aplicação."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Project
    PROJECT_NAME: str = "IA Classifier API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Health Check
    HEALTH_CHECK_ENABLED: bool = True

    # AI Provider
    # fake: sem rede/chave (padrão); gemini/groq/openai: provedores reais.
    AI_PROVIDER: AIProviderName = "fake"
    # Lista separada por vírgula; vazio = sem fallback.
    AI_FALLBACK_PROVIDERS: str = ""
    AI_TIMEOUT_SECONDS: float = 20.0

    # Gemini (API REST generateContent)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Groq (endpoint compatível com OpenAI)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Autenticação (SPEC-06) — vazio desativa a verificação de X-API-Key.
    API_KEY: str = ""

    # Database (opcional - para próximos specs)
    DATABASE_URL: str = ""


    # n8n Webhook (SPEC-05) — vazio desativa as notificações (NullNotifier).
    N8N_WEBHOOK_URL: str = ""
    N8N_WEBHOOK_SECRET: str = ""
    N8N_TIMEOUT_SECONDS: float = 5.0

    def fallback_providers(self) -> list[str]:
        """Retorna a lista de provedores de fallback em ordem.

        Returns:
            Nomes dos provedores de fallback (vazio se não configurado).
        """
        bruto = self.AI_FALLBACK_PROVIDERS.strip()
        if not bruto:
            return []
        return [item.strip() for item in bruto.split(",") if item.strip()]
