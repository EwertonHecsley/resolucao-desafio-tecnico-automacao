"""Rotas da API (SPEC-06)."""

from __future__ import annotations

import datetime
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import (
    get_ai_provider,
    get_classifier_service,
    get_message_repository,
    get_notifier,
    require_api_key,
)
from domain.models import Classification, MessageIn, ProcessedMessage
from domain.ports import MessageRepository, Notifier
from services.classifier import ClassifierService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/classify", response_model=Classification)
async def classify(
    msg: MessageIn,
    service: ClassifierService = Depends(get_classifier_service),
):
    """Classifica uma mensagem (SEM salvar nem notificar).

    Esta rota atende apenas ao fluxo de classificação, ideal para testes
    ou uso direto sem persistência. Se você precisa salvar e notificar,
    use /messages.

    Args:
        msg: Mensagem de entrada com texto e metadados opcionais.
        service: Serviço de classificação injetado.

    Returns:
        Classificação validada com categoria, setor, prioridade,
        sentimento, resumo e confiança.

    Raises:
        AIProviderError: Falha ao comunicar com o provedor de IA.
        InvalidAIResponseError: Resposta inválida após esgotar retries.
    """
    logger.info("Recebida requisição de classificação para: %s", msg.texto[:50])
    return await service.classify(msg)


@router.post("/messages", status_code=201, response_model=ProcessedMessage)
async def create_message(
    msg: MessageIn,
    service: ClassifierService = Depends(get_classifier_service),
    repo: MessageRepository = Depends(get_message_repository),
    notifier: Notifier = Depends(get_notifier),
    _api_key_check=Depends(require_api_key),
):
    """Classifica → salva → notifica → marca como notificado se sucesso.

    Fluxo completo de processamento:
    1. Classificar a mensagem com IA
    2. Montar ProcessedMessage com provedor usado
    3. Salvar no banco
    4. Notificar o webhook (n8n)
    5. Se notificação foi bem-sucedida, marcar como notificado

    Args:
        msg: Mensagem de entrada.
        service: Serviço de classificação.
        repo: Repositório de persistência.
        notifier: Notificador externo (n8n ou NullNotifier).
        _api_key_check: Verificador de autenticação (Opcional se API_KEY=vazio).

    Returns:
        ProcessedMessage com 201 Created.

    Raises:
        AIProviderError: Falha do provedor de IA.
        InvalidAIResponseError: Resposta inválida.
        RuntimeError: Banco indisponível.
    """
    # 1. Classificar
    logger.info("Iniciando classificação para: %s", msg.texto[:50])
    classificacao = await service.classify(msg)

    # 2. Montar ProcessedMessage
    mensagem_processada = ProcessedMessage(
        id=str(uuid4()),
        entrada=msg,
        classificacao=classificacao,
        provedor=service._ai.name,
        criado_em=datetime.datetime.now(datetime.UTC),
        notificado=False,
    )

    # 3. Salvar no banco
    logger.debug("Salvando mensagem processada: %s", mensagem_processada.id)
    salvo = await repo.save(mensagem_processada)

    # 4. Notificar
    logger.debug("Notificando webhook: %s", mensagem_processada.id)
    notificado = await notifier.notify(salvo)

    # 5. Marcar como notificado se sucesso
    if notificado:
        await repo.mark_notified(salvo.id)
        mensagem_processada.notificado = True
        logger.info("Mensagem notificada com sucesso: %s", mensagem_processada.id)

    return mensagem_processada


@router.get("/messages")
async def list_messages(
    limit: int = Query(default=50, ge=1, le=200, description="Limite de mensagens"),
    repo: MessageRepository = Depends(get_message_repository),
):
    """Lista as últimas mensagens processadas.

    Resultado ordenado do mais recente para o mais antigo.

    Args:
        limit: Número máximo de mensagens (máximo 200, padrão 50).

    Returns:
        Lista de ProcessedMessage.

    Raises:
        RuntimeError: Banco indisponível.
    """
    logger.debug("Listando mensagens com limit: %d", limit)
    return await repo.list(limit=limit)


@router.get("/messages/{id}", response_model=ProcessedMessage)
async def get_message(id: str, repo: MessageRepository = Depends(get_message_repository)):
    """Detalhe de uma mensagem pelo ID.

    Args:
        id: UUID da mensagem.

    Returns:
        ProcessedMessage com os dados completos.

    Raises:
        HTTPException: status 404 se a mensagem não existir.
        RuntimeError: Banco indisponível.
    """
    logger.debug("Buscando mensagem: %s", id)
    mensagem = await repo.get(id)

    if not mensagem:
        logger.warning("Mensagem não encontrada: %s", id)
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")

    return mensagem


@router.get("/health/ai")
async def health_ai(ai=Depends(get_ai_provider)):
    """Testa se o provedor de IA ativo responde.

    Faz uma chamada simples (dummy) para verificar se o provedor
    está operacional e retorna seu nome.

    Args:
        ai: Instância de AIProvider injetada.

    Returns:
        Dict com "provider" (nome) e "responded" (bool).
    """
    logger.debug("Health check do provedor de IA: %s", ai.name)
    try:
        # Chamada dummy para testar se o provedor responde
        await ai.generate_json("test", "test")
        return {"provider": ai.name, "responded": True}
    except Exception as e:
        logger.warning("Provedor de IA respondeu com erro: %s", e)
        return {"provider": ai.name, "responded": False, "error": str(e)}
