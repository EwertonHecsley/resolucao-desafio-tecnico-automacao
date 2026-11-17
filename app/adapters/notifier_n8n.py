"""Adapters de notificação para o n8n (SPEC-05).

Contém ``N8nWebhookNotifier`` (POST ao webhook) e ``NullNotifier`` (no-op).
Ambos implementam a porta ``Notifier`` de ``domain/ports.py`` e nunca
levantam exceção — falhas são logadas (sem segredos) e devolvidas como
``False`` para não derrubar a API.

``httpx`` é usado aqui e em ``adapters/ai/`` — regra do AGENTS.md.
"""

from __future__ import annotations

import logging

import httpx

from domain.models import ProcessedMessage

logger = logging.getLogger(__name__)

HEADER_SEGREDO = "X-Webhook-Secret"


class N8nWebhookNotifier:
    """Notifier que envia a mensagem processada ao webhook do n8n."""

    def __init__(
        self,
        webhook_url: str,
        secret: str,
        timeout: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Inicializa o notifier.

        Args:
            webhook_url: URL completa do webhook de produção (ex.:
                ``http://n8n:5678/webhook/classificador``).
            secret: Segredo enviado no header ``X-Webhook-Secret``.
            timeout: Timeout em segundos (``N8N_TIMEOUT_SECONDS``).
            transport: Transporte alternativo (injeção para
                ``httpx.MockTransport`` nos testes).
        """
        self._webhook_url = webhook_url
        self._cliente = httpx.AsyncClient(timeout=timeout, transport=transport)
        self._headers = {HEADER_SEGREDO: secret}

    async def notify(self, msg: ProcessedMessage) -> bool:
        """Envia a mensagem ao n8n. Nunca levanta exceção.

        Args:
            msg: Mensagem processada a ser notificada.

        Returns:
            ``True`` se a resposta for 2xx; ``False`` em timeout, falha de
            conexão ou status não 2xx.
        """
        payload = msg.model_dump(mode="json")
        try:
            resposta = await self._cliente.post(
                self._webhook_url,
                json=payload,
                headers=self._headers,
            )
        except httpx.TimeoutException:
            logger.warning("n8n: timeout ao notificar webhook")
            return False
        except httpx.HTTPError as erro:
            logger.warning("n8n: falha de rede ao notificar (%s)", type(erro).__name__)
            return False

        if not 200 <= resposta.status_code < 300:
            logger.warning("n8n: webhook respondeu HTTP %s", resposta.status_code)
            return False

        return True


class NullNotifier:
    """Notifier no-op usado quando ``N8N_WEBHOOK_URL`` não está configurada."""

    async def notify(self, _msg: ProcessedMessage) -> bool:
        """Não faz nada e retorna ``False``.

        Args:
            _msg: Ignorada (a porta exige o parâmetro).

        Returns:
            ``False`` (nenhuma notificação foi enviada).
        """
        return False
