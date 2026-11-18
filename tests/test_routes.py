"""Testes de integração dos endpoints da API (SPEC-06).

Usa TestClient, FakeAIProvider (sem rede), repositório em memória e
notifier falso para cobrir todos os cenários de aceite da SPEC-06.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.adapters.ai.fake import MARCADOR_ERRO, FakeAIProvider
from app.api.deps import (
    get_ai_provider,
    get_classifier_service,
    get_message_repository,
    get_notifier,
)
from app.main import app
from domain.models import MessageIn, ProcessedMessage
from services.classifier import ClassifierService

JSON_CLASSIFICACAO = json.dumps(
    {
        "categoria": "duvida",
        "setor": "financeiro",
        "prioridade": "media",
        "sentimento": "neutro",
        "resumo": "Cliente pede segunda via de boleto vencido.",
        "confianca": 0.95,
    },
    ensure_ascii=False,
)

CORPO_MENSAGEM = {
    "texto": "Meu boleto venceu ontem, como emito a segunda via?",
    "remetente": "joao@example.com",
    "canal": "whatsapp",
}


# ---------------------------------------------------------------------------
# Fakes / stubs de teste (em memória)
# ---------------------------------------------------------------------------


@pytest.fixture
def override_settings():
    """Fixture para sobrescrever Settings via dependency injection."""
    from app.api.deps import get_settings
    from app.config import Settings

    def _apply(**kwargs):
        settings = Settings(**kwargs)
        app.dependency_overrides[get_settings] = lambda: settings
        return settings

    yield _apply
    app.dependency_overrides.clear()


class RepositorioEmMemoria:
    """Implementação em memória da porta MessageRepository para testes."""

    def __init__(self) -> None:
        self._dados: dict[str, ProcessedMessage] = {}

    async def save(self, msg: ProcessedMessage) -> ProcessedMessage:
        """Salva a mensagem em memória."""
        self._dados[msg.id] = msg
        return msg

    async def get(self, msg_id: str) -> ProcessedMessage | None:
        """Busca uma mensagem pelo ID."""
        return self._dados.get(msg_id)

    async def list(self, limit: int = 50) -> list[ProcessedMessage]:
        """Lista as mensagens mais recentes primeiro."""
        return list(reversed(list(self._dados.values())))[:limit]

    async def mark_notified(self, msg_id: str) -> None:
        """Marca a mensagem como notificada."""
        if msg_id in self._dados:
            self._dados[msg_id].notificado = True


class NotifierFalso:
    """Notifier falso que registra chamadas e retorna um valor configurável."""

    def __init__(self, retorno: bool = True) -> None:
        self.retorno = retorno
        self.chamadas: list[ProcessedMessage] = []

    async def notify(self, msg: ProcessedMessage) -> bool:
        """Registra a chamada e devolve o retorno configurado."""
        self.chamadas.append(msg)
        return self.retorno


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def setup_dependencias():
    """Fábrica de setup: injeta fakes via dependency_overrides e limpa ao final."""
    estados: list[RepositorioEmMemoria] = []

    def _configurar(
        respostas_ia: list[str] | None = None,
        notificar: bool = True,
    ) -> tuple[RepositorioEmMemoria, NotifierFalso]:
        respostas = [JSON_CLASSIFICACAO] if respostas_ia is None else respostas_ia
        provider = FakeAIProvider(respostas)
        service = ClassifierService(provider)
        repositorio = RepositorioEmMemoria()
        notifier = NotifierFalso(retorno=notificar)
        estados.append(repositorio)

        app.dependency_overrides[get_ai_provider] = lambda: provider
        app.dependency_overrides[get_classifier_service] = lambda: service
        app.dependency_overrides[get_message_repository] = lambda: repositorio
        app.dependency_overrides[get_notifier] = lambda: notifier
        return repositorio, notifier

    yield _configurar
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /classify
# ---------------------------------------------------------------------------


def test_classify_retorna_classification_sem_salvar(setup_dependencias) -> None:
    """POST /api/v1/classify retorna Classification e não persiste nem notifica."""
    repositorio, notifier = setup_dependencias()
    client = TestClient(app)

    resposta = client.post("/api/v1/classify", json=CORPO_MENSAGEM)

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["categoria"] == "duvida"
    assert dados["setor"] == "financeiro"
    assert dados["confianca"] == 0.95
    assert repositorio._dados == {}
    assert notifier.chamadas == []


# ---------------------------------------------------------------------------
# POST /messages
# ---------------------------------------------------------------------------


def test_post_messages_201_happy_path(setup_dependencias) -> None:
    """POST /api/v1/messages com sucesso retorna 201 e ProcessedMessage completo."""
    repositorio, notifier = setup_dependencias(notificar=True)
    client = TestClient(app)

    resposta = client.post("/api/v1/messages", json=CORPO_MENSAGEM)

    assert resposta.status_code == 201
    dados = resposta.json()
    assert "id" in dados
    assert dados["entrada"] == CORPO_MENSAGEM
    assert dados["classificacao"]["categoria"] == "duvida"
    assert dados["provedor"] == "fake"
    assert dados["notificado"] is True
    assert len(notifier.chamadas) == 1
    assert repositorio._dados[dados["id"]].notificado is True


def test_post_messages_notificado_false_quando_notifier_falha(setup_dependencias) -> None:
    """Se o notifier retorna False, a API responde 201 com notificado=false."""
    repositorio, notifier = setup_dependencias(notificar=False)
    client = TestClient(app)

    resposta = client.post("/api/v1/messages", json=CORPO_MENSAGEM)

    assert resposta.status_code == 201
    assert resposta.json()["notificado"] is False
    assert len(notifier.chamadas) == 1
    assert repositorio._dados[resposta.json()["id"]].notificado is False


def test_post_messages_422_entrada_invalida(setup_dependencias) -> None:
    """POST /api/v1/messages com texto vazio retorna 422 em JSON."""
    setup_dependencias()
    client = TestClient(app)

    resposta = client.post("/api/v1/messages", json={"texto": ""})

    assert resposta.status_code == 422
    assert "detail" in resposta.json()


def test_post_messages_502_quando_ia_falha(setup_dependencias) -> None:
    """POST /api/v1/messages com AIProviderError retorna 502 claro."""
    setup_dependencias(respostas_ia=[MARCADOR_ERRO])
    client = TestClient(app)

    resposta = client.post("/api/v1/messages", json=CORPO_MENSAGEM)

    assert resposta.status_code == 502
    dados = resposta.json()
    assert "detail" in dados
    assert dados["provider"] == "fake"
    assert dados["error"] == "ai_provider_error"


def test_post_messages_502_quando_resposta_invalida(setup_dependencias) -> None:
    """POST /api/v1/messages com JSON inválido esgota retries e retorna 502."""
    setup_dependencias(respostas_ia=["lixo", "lixo", "lixo"])
    client = TestClient(app)

    resposta = client.post("/api/v1/messages", json=CORPO_MENSAGEM)

    assert resposta.status_code == 502
    assert resposta.json()["error"] == "invalid_ai_response"


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------


def test_post_messages_401_sem_api_key_quando_configurada(setup_dependencias, monkeypatch) -> None:
    """Com API_KEY definida, POST sem X-API-Key retorna 401."""
    from app.api.deps import get_settings
    from app.config import Settings

    setup_dependencias()
    monkeypatch.setenv("API_KEY", "minha-chave-secreta")
    app.dependency_overrides[get_settings] = lambda: Settings()
    client = TestClient(app)

    resposta = client.post("/api/v1/messages", json=CORPO_MENSAGEM)

    assert resposta.status_code == 401
    assert resposta.json()["detail"] == "X-API-Key inválido"
    app.dependency_overrides.pop(get_settings, None)


def test_post_messages_com_api_key_valida(setup_dependencias, monkeypatch) -> None:
    """Com API_KEY definida, POST com header correto passa e retorna 201."""
    from app.api.deps import get_settings
    from app.config import Settings

    setup_dependencias()
    monkeypatch.setenv("API_KEY", "minha-chave-secreta")
    app.dependency_overrides[get_settings] = lambda: Settings()
    client = TestClient(app)

    resposta = client.post(
        "/api/v1/messages",
        json=CORPO_MENSAGEM,
        headers={"X-API-Key": "minha-chave-secreta"},
    )

    assert resposta.status_code == 201
    app.dependency_overrides.pop(get_settings, None)


# ---------------------------------------------------------------------------
# GET /messages
# ---------------------------------------------------------------------------


def test_get_messages_lista_com_limit(setup_dependencias) -> None:
    """GET /api/v1/messages retorna lista e respeita o query param limit."""
    repositorio, _ = setup_dependencias()
    for i in range(3):
        msg = ProcessedMessage(
            id=str(uuid4()),
            entrada=MessageIn(texto=f"Mensagem {i}"),
            classificacao=resposta_classificacao(),
            provedor="fake",
            criado_em=datetime.now(UTC),
        )
        repositorio._dados[msg.id] = msg

    client = TestClient(app)
    resposta = client.get("/api/v1/messages", params={"limit": 2})

    assert resposta.status_code == 200
    assert len(resposta.json()) == 2


def test_get_messages_valida_limit_fora_do_intervalo(setup_dependencias) -> None:
    """GET /api/v1/messages?limit=201 retorna 422 (máximo 200)."""
    setup_dependencias()
    client = TestClient(app)

    resposta = client.get("/api/v1/messages", params={"limit": 201})

    assert resposta.status_code == 422


def test_get_messages_404_inexistente(setup_dependencias) -> None:
    """GET /api/v1/messages/{id} com ID inexistente retorna 404."""
    setup_dependencias()
    client = TestClient(app)

    resposta = client.get("/api/v1/messages/00000000-0000-0000-0000-000000000000")

    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Mensagem não encontrada"


def test_get_messages_retorna_detalhe(setup_dependencias) -> None:
    """GET /api/v1/messages/{id} com ID existente retorna o ProcessedMessage."""
    repositorio, _ = setup_dependencias()
    msg = ProcessedMessage(
        id="11111111-1111-1111-1111-111111111111",
        entrada=MessageIn(texto="Mensagem de teste"),
        classificacao=resposta_classificacao(),
        provedor="fake",
        criado_em=datetime.now(UTC),
    )
    repositorio._dados[msg.id] = msg

    client = TestClient(app)
    resposta = client.get(f"/api/v1/messages/{msg.id}")

    assert resposta.status_code == 200
    assert resposta.json()["id"] == msg.id


def resposta_classificacao():
    """Constrói uma Classification válida para os testes de listagem."""
    from domain.models import Classification

    return Classification.model_validate_json(JSON_CLASSIFICACAO)


# ---------------------------------------------------------------------------
# GET /api/v1/config/ai
# ---------------------------------------------------------------------------


def test_config_ai_provider_fake(client, override_settings):
    """Provider fake é sinalizado como não real e sem chave."""
    override_settings(AI_PROVIDER="fake")
    response = client.get("/api/v1/config/ai")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "fake"
    assert data["is_real"] is False
    assert data["key_configured"] is False


def test_config_ai_provider_real_com_chave(client, override_settings):
    """Provider real com chave é sinalizado corretamente."""
    override_settings(AI_PROVIDER="groq", GROQ_API_KEY="chave-teste", GROQ_MODEL="llama")
    response = client.get("/api/v1/config/ai")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "groq"
    assert data["is_real"] is True
    assert data["key_configured"] is True
    assert data["model"] == "llama"
    assert "chave-teste" not in response.text


def test_config_ai_provider_real_sem_chave(client, override_settings):
    """Provider real sem chave é sinalizado como não configurado."""
    override_settings(AI_PROVIDER="gemini", GEMINI_API_KEY="")
    response = client.get("/api/v1/config/ai")
    assert response.status_code == 200
    data = response.json()
    assert data["is_real"] is True
    assert data["key_configured"] is False
