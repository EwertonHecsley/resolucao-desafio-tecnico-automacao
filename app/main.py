"""Aplicação FastAPI principal da API de classificação."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.adapters.ai.factory import build_ai_provider
from app.adapters.repository_postgres import PostgresMessageRepository
from app.api import routes
from app.config import Settings
from domain.errors import AIProviderError, InvalidAIResponseError
from domain.ports import MessageRepository


def get_settings() -> Settings:
    """
    Retorna as configurações da aplicação.

    Returns:
        Instância de Settings carregadas do ambiente.

    Note:
        Em ambientes de produção, isso seria injetado via FastAPI Depends.
    """
    return Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifecycle manager da aplicação.

    Atua como startup e shutdown hooks.
    """
    import logging

    settings = get_settings()
    logging.basicConfig(level=logging.INFO)

    # Falha cedo se AI_PROVIDER/fallbacks/chaves estiverem inválidos.
    build_ai_provider(settings)

    # Cria as tabelas no startup (SPEC-04). Sem DATABASE_URL a aplicação
    # segue sem persistência — útil em testes de health/unitários.
    if settings.DATABASE_URL:
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        from app.adapters.models import Base

        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        app.state.db_session_factory = async_sessionmaker(
            engine, expire_on_commit=False
        )
        app.state.db_engine = engine
        logging.info("Tabelas PostgreSQL garantidas no startup")
    else:
        app.state.db_session_factory = None
        app.state.db_engine = None

    logging.info(f"{settings.PROJECT_NAME} v{settings.VERSION} iniciado")
    logging.info(f"Ambiente: {settings.ENVIRONMENT}")
    logging.info(f"AI Provider: {settings.AI_PROVIDER}")

    yield

    if app.state.db_engine is not None:
        await app.state.db_engine.dispose()
    logging.info(f"{settings.PROJECT_NAME} v{settings.VERSION} desligado")


app = FastAPI(
    title=get_settings().PROJECT_NAME,
    version=get_settings().VERSION,
    description="API para classificação de mensagens com IA",
    lifespan=lifespan,
)


# Exception handlers (SPEC-06) — erros em JSON claro.
@app.exception_handler(InvalidAIResponseError)
async def invalid_ai_response_error_handler(_request: Request, exc: InvalidAIResponseError):
    """Converte InvalidAIResponseError em HTTP 502 com detalhes claros."""
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "detail": str(exc),
            "provider": exc.provedor or "unknown",
            "error": "invalid_ai_response",
        },
    )


@app.exception_handler(AIProviderError)
async def ai_provider_error_handler(_request: Request, exc: AIProviderError):
    """Converte AIProviderError em HTTP 502 com detalhes claros."""
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "detail": str(exc),
            "provider": exc.provedor or "unknown",
            "error": "ai_provider_error",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    """Converte HTTPException em JSON (401, 404, etc)."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Rotas (SPEC-06) — prefixo /api/v1.
app.include_router(routes.router, prefix="/api/v1", tags=["classification"])


# CORS middleware - configurado para produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: (SPEC-aa) Configurar origins corretamente
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """
    Endpoint de health check da aplicação.

    Returns:
        Status "ok" indicando que a aplicação está saudável.
    """
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    """
    Endpoint raiz da aplicação.

    Returns:
        Mensagem de boas-vindas.
    """
    settings = get_settings()
    return {
        "message": f"{settings.PROJECT_NAME} v{settings.VERSION}",
        "status": "running",
    }


async def get_message_repository(request: Request) -> AsyncIterator[MessageRepository]:
    """Dependency do FastAPI que fornece o repositório de mensagens.

    Args:
        request: Request atual, usado para acessar o estado da aplicação.

    Yields:
        Implementação de ``MessageRepository`` com uma sessão por requisição.

    Raises:
        RuntimeError: Se a aplicação foi iniciada sem ``DATABASE_URL``.
    """
    factory = request.app.state.db_session_factory
    if factory is None:
        raise RuntimeError(
            "Repositório de mensagens indisponível: DATABASE_URL não configurada"
        )

    async with factory() as session:
        yield PostgresMessageRepository(session)
