"""Infraestrutura HTTP compartilhada pelos adapters REST de IA.

Único lugar (junto com os adapters de ``app/adapters/ai/``) onde
``httpx`` pode ser importado — regra do AGENTS.md / SPEC-03.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from domain.errors import AIProviderError

logger = logging.getLogger(__name__)

#: Status HTTP que mapeiam para falhas do provedor.
_HTTP_ERROS: dict[int, str] = {
    401: "autenticação recusada (401)",
    403: "acesso negado (403)",
    429: "limite de requisições atingido (429)",
}


def construir_cliente(
    base_url: str,
    timeout: float,
    transport: httpx.AsyncBaseTransport | None = None,
) -> httpx.AsyncClient:
    """Constrói o ``httpx.AsyncClient`` do adapter.

    Args:
        base_url: URL base do provedor.
        timeout: Timeout em segundos (``AI_TIMEOUT_SECONDS``).
        transport: Transporte alternativo (injeção para ``httpx.MockTransport``
            nos testes). ``None`` usa o transporte de rede padrão.

    Returns:
        Cliente async configurado.
    """
    return httpx.AsyncClient(
        base_url=base_url,
        timeout=timeout,
        transport=transport,
    )


async def requisicao_json(
    cliente: httpx.AsyncClient,
    metodo: str,
    url: str,
    provedor: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Executa requisição HTTP e devolve o JSON da resposta.

    Mapeia timeout, falha de rede e erros HTTP (401/403/429/5xx e demais
    códigos de erro) para ``AIProviderError`` com mensagem curta —
    sem vazar chaves ou detalhes sensíveis em logs/mensagens.

    Args:
        cliente: Cliente HTTP do adapter.
        metodo: Método HTTP (``GET``/``POST``).
        url: Caminho/URL da requisição.
        provedor: Nome do provedor (para o erro).
        **kwargs: Argumentos extras para ``client.request``.

    Returns:
        Payload JSON decodificado.

    Raises:
        AIProviderError: Timeout, falha de rede ou HTTP de erro.
    """
    try:
        resposta = await cliente.request(metodo, url, **kwargs)
    except httpx.TimeoutException as erro:
        logger.warning("[%s] timeout: %s", provedor, type(erro).__name__)
        raise AIProviderError(
            f"{provedor}: timeout após o limite configurado", provedor=provedor
        ) from None
    except httpx.HTTPError as erro:
        logger.warning("[%s] falha de rede: %s", provedor, type(erro).__name__)
        raise AIProviderError(
            f"{provedor}: falha de rede ao contatar o provedor",
            provedor=provedor,
        ) from None

    if resposta.status_code in _HTTP_ERROS:
        motivo = _HTTP_ERROS[resposta.status_code]
        logger.warning("[%s] HTTP %s", provedor, resposta.status_code)
        raise AIProviderError(
            f"{provedor}: {motivo}", provedor=provedor
        )
    if resposta.status_code >= 400:
        logger.warning("[%s] HTTP %s", provedor, resposta.status_code)
        raise AIProviderError(
            f"{provedor}: erro do provedor (HTTP {resposta.status_code})",
            provedor=provedor,
        )

    try:
        dados: dict[str, Any] = resposta.json()
    except ValueError as erro:
        logger.warning("[%s] resposta não é JSON", provedor)
        raise AIProviderError(
            f"{provedor}: resposta não é um JSON válido", provedor=provedor
        ) from erro
    return dados
