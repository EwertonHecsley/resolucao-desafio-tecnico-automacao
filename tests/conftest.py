"""Fixtures compartilhadas entre testes."""

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.ai import FakeAIProvider
from app.main import app


@pytest.fixture
def fake_ai_provider() -> FakeAIProvider:
    """Provider fake de IA para testes — nunca chama API real."""
    return FakeAIProvider()


@pytest.fixture
def client() -> TestClient:
    """Cliente HTTP para testes de integração com a aplicação."""
    return TestClient(app)


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Sessão async contra o PostgreSQL real, limpa antes e depois de cada teste.

    A fixture é pulada quando ``DATABASE_URL`` não está configurada, mantendo
    a suíte padrão independente de banco. Importa o adapter de forma tardia
    para que os testes unitários existentes não dependam dele.
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL não configurada — pulando teste de integração")

    from sqlalchemy import delete
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.adapters.models import Base, MessageORM

    engine = create_async_engine(database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(delete(MessageORM))

    try:
        async with factory() as session:
            yield session
    finally:
        async with engine.begin() as conn:
            await conn.execute(delete(MessageORM))
        await engine.dispose()
