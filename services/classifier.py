"""Serviço de classificação de mensagens (SPEC-02).

Depende apenas de ``domain/ports.py`` — não de implementações concretas
nem de SDKs de provedores de IA.
"""

from __future__ import annotations

import json
import logging

from pydantic import ValidationError

from domain.errors import InvalidAIResponseError
from domain.models import Classification, MessageIn
from domain.ports import AIProvider
from services.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


def _limpar_resposta(bruta: str) -> str:
    """Remove cercas markdown e extrai o JSON, se necessário.

    Ordem de limpeza:
    1. Remove cercas ```` ```json ```` / ```` ``` ````.
    2. Se o resultado não começa com ``{``, extrai do primeiro ``{`` ao
       último ``}``.

    Args:
        bruta: Texto bruto retornado pelo provedor de IA.

    Returns:
        Texto contendo (esperançosamente) apenas o objeto JSON.
    """
    texto = bruta.strip()

    # Remove cercas markdown: ```json ... ``` ou ``` ... ```
    if texto.startswith("```"):
        # Descarta a 1ª linha (``` ou ```json) e a última (```)
        linhas = texto.splitlines()
        if len(linhas) >= 2:
            linhas = linhas[1:]
        if linhas and linhas[-1].strip() == "```":
            linhas = linhas[:-1]
        texto = "\n".join(linhas).strip()

    # Extrai do primeiro { ao último } se houver texto ao redor.
    inicio = texto.find("{")
    fim = texto.rfind("}")
    if inicio != -1 and fim != -1 and fim > inicio:
        texto = texto[inicio : fim + 1]

    return texto


class ClassifierService:
    """Serviço que classifica mensagens de clientes usando IA.

    Fluxo: monta o user prompt → chama ``ai.generate_json`` → limpa a
    resposta → valida com Pydantic. Em caso de JSON inválido, tenta de
    novo até ``max_retries`` vezes (total de ``1 + max_retries`` chamadas).
    """

    def __init__(self, ai: AIProvider, max_retries: int = 2) -> None:
        """Inicializa o serviço com o provider e o limite de retries.

        Args:
            ai: Implementação da porta ``AIProvider`` (injeção via construtor).
            max_retries: Número máximo de tentativas extras após a 1ª.
        """
        self._ai = ai
        self._max_retries = max_retries

    async def classify(self, msg: MessageIn) -> Classification:
        """Classifica a mensagem do cliente.

        Args:
            msg: Mensagem de entrada (texto + metadados opcionais).

        Returns:
            Classificação validada pelo contrato de domínio.

        Raises:
            AIProviderError: Falha do provedor — propagada sem retry.
            InvalidAIResponseError: Resposta inválida após esgotar retries.
        """
        user_prompt = build_user_prompt(msg)
        total_tentativas = 1 + self._max_retries
        ultimo_erro: Exception | None = None

        for _ in range(total_tentativas):
            # AIProviderError NÃO é retentado aqui: apenas propaga
            # (fallback entre provedores é tratado na SPEC-03).
            bruta = await self._ai.generate_json(SYSTEM_PROMPT, user_prompt)

            try:
                limpo = _limpar_resposta(bruta)
                dados = json.loads(limpo)
                return Classification.model_validate(dados)
            except (json.JSONDecodeError, ValidationError, ValueError) as erro:
                logger.warning(
                    "Resposta da IA inválida (tentativa): %s", erro
                )
                ultimo_erro = erro

        detalhe = str(ultimo_erro)
        mensagem = (
            "Resposta da IA inválida após "
            f"{total_tentativas} tentativas: a resposta não é um JSON válido "
            f"ou não obedece ao contrato de classificação. Detalhe: {detalhe}"
        )
        raise InvalidAIResponseError(mensagem, provedor=self._ai.name)
