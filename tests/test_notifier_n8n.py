"""Testes de aceite da SPEC-05 — Notifier n8n.

Todos os cenários usam httpx.MockTransport (sem rede), conforme exigido pela
SPEC e pelas regras do AGENTS.md.
"""

import json
from datetime import UTC, datetime

import httpx

from app.adapters.notifier_n8n import N8nWebhookNotifier, NullNotifier
from domain.models import Classification, MessageIn, ProcessedMessage


def _mensagem() -> ProcessedMessage:
    """Mensagem processada de exemplo, idêntica à da SPEC."""
    return ProcessedMessage(
        id="9b6f1a2e-4c3d-4e5f-8a7b-1c2d3e4f5a6b",
        entrada=MessageIn(
            texto="Meu pedido ainda não chegou, o que aconteceu?",
            remetente="joao@example.com",
            canal="whatsapp",
        ),
        classificacao=Classification(
            categoria="reclamacao",
            setor="logistica",
            prioridade="alta",
            sentimento="negativo",
            resumo="Cliente relata atraso na entrega do pedido.",
            confianca=0.92,
        ),
        provedor="fake",
        criado_em=datetime(2026, 11, 17, 10, 0, tzinfo=UTC),
    )


MENSAGEM = _mensagem()


def _transport(status: int, corpo: str = "") -> httpx.MockTransport:
    """Transporte que responde sempre igual (independe do request)."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text=corpo)

    return httpx.MockTransport(handler)


def _transport_inspector() -> tuple[httpx.MockTransport, list[httpx.Request]]:
    """Transporte que grava as requisições e responde com payload fixo."""
    requisicoes: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requisicoes.append(request)
        return httpx.Response(200, json={"ok": True})

    return httpx.MockTransport(handler), requisicoes


def _transport_que_levanta(erro: Exception) -> httpx.MockTransport:
    """Transporte que sempre levanta a exceção informada."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise erro

    return httpx.MockTransport(handler)


def _notifier(transport: httpx.AsyncBaseTransport) -> N8nWebhookNotifier:
    """Fábrica de notifier com transporte injetado."""
    return N8nWebhookNotifier(
        webhook_url="http://localhost:5678/webhook/classificador",
        secret="test-secret",
        timeout=5.0,
        transport=transport,
    )


class TestNullNotifier:
    """Cenários do NullNotifier."""

    async def test_retorna_false_sem_fazer_nada(self) -> None:
        """NullNotifier sempre retorna False."""
        assert await NullNotifier().notify(MENSAGEM) is False


class TestN8nWebhookNotifier:
    """Cenários do N8nWebhookNotifier."""

    async def test_sucesso_200_retorna_true(self) -> None:
        """HTTP 200 → True."""
        transport, _ = _transport_inspector()
        assert await _notifier(transport).notify(MENSAGEM) is True

    async def test_sucesso_201_retorna_true(self) -> None:
        """Qualquer status 2xx (201) → True."""
        assert await _notifier(_transport(201)).notify(MENSAGEM) is True

    async def test_500_retorna_false(self) -> None:
        """HTTP 500 → False."""
        assert await _notifier(_transport(500)).notify(MENSAGEM) is False

    async def test_timeout_retorna_false(self) -> None:
        """Timeout → False."""
        transport = _transport_que_levanta(httpx.TimeoutException("timeout"))
        assert await _notifier(transport).notify(MENSAGEM) is False

    async def test_conexao_falha_retorna_false(self) -> None:
        """Erro de conexão → False."""
        transport = _transport_que_levanta(httpx.ConnectError("offline"))
        assert await _notifier(transport).notify(MENSAGEM) is False

    async def test_header_x_webhook_secret_enviado(self) -> None:
        """Header X-Webhook-Secret é enviado."""
        transport, requisicoes = _transport_inspector()
        await _notifier(transport).notify(MENSAGEM)
        assert requisicoes[0].headers["X-Webhook-Secret"] == "test-secret"

    async def test_payload_serializado_correto(self) -> None:
        """Payload é serializado como JSON (datetime → string ISO)."""
        transport, requisicoes = _transport_inspector()
        await _notifier(transport).notify(MENSAGEM)
        esperado = MENSAGEM.model_dump(mode="json")
        assert json.loads(requisicoes[0].content) == esperado
        assert isinstance(esperado["criado_em"], str)

    async def test_url_correta_no_payload(self) -> None:
        """A URL deve ser /webhook/classificador (não /webhook-test/)."""
        transport, requisicoes = _transport_inspector()
        await _notifier(transport).notify(MENSAGEM)
        assert requisicoes[0].url.path == "/webhook/classificador"

    async def test_nao_levanta_excecao_em_falha(self) -> None:
        """Falha não levanta exceção, apenas retorna False."""
        assert await _notifier(_transport(404)).notify(MENSAGEM) is False
