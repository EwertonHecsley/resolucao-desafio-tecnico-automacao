"""Fixtures compartilhadas entre testes."""


import pytest
from fastapi.testclient import TestClient

from adapters.ai.base import FakeAIProvider
from app.main import app


@pytest.fixture
def fake_ai_provider() -> FakeAIProvider:
    """Provider fake de IA para testes — nunca chama API real."""
    return FakeAIProvider()


@pytest.fixture
def client() -> TestClient:
    """Cliente HTTP para testes de integração com a aplicação."""
    return TestClient(app)
