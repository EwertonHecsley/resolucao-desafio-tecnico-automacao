"""Aplicação FastAPI principal da API de classificação."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings


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
async def lifespan(app: FastAPI) -> None:  # noqa: ARG001
    """
    Lifecycle manager da aplicação.

    Atua como startup e shutdown hooks.
    """
    import logging

    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    logging.info(f"{settings.PROJECT_NAME} v{settings.VERSION} iniciado")
    logging.info(f"Ambiente: {settings.ENVIRONMENT}")
    logging.info(f"AI Provider: {settings.AI_PROVIDER}")

    yield

    logging.info(f"{settings.PROJECT_NAME} v{settings.VERSION} desligado")


app = FastAPI(
    title=get_settings().PROJECT_NAME,
    version=get_settings().VERSION,
    description="API para classificação de mensagens com IA",
    lifespan=lifespan,
)


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
