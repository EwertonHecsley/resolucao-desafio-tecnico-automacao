"""FakeAIProvider para testes — simula provedor de IA sem chamar API real.
Programável: recebe uma fila de respostas brutas e devolve uma por
chamada. Itens especiais permitem simular falhas (para testar retry e
erro 502 nas próximas SPECs).
"""

from __future__ import annotations

from typing import Final

import json

from pydantic import ValidationError

from domain.errors import AIProviderError
from domain.models import Classification

#: Item especial que, ao ser consumido da fila, levanta AIProviderError.
MARCADOR_ERRO: Final[str] = "__erro__"

#: Resposta padrão válida quando nenhuma resposta é configurada.
#    Esta resposta permite que o fluxo funcione imediatamente com AI_PROVIDER=fake
#    sem precisar configurar respostas manualmente.
RESPOSTA_PADRAO: Final[str] = json.dumps(
    {
        "categoria": "duvida",
        "setor": "geral",
        "prioridade": "baixa",
        "sentimento": "neutro",
        "resumo": "Mensagem recebida para classificação.",
        "confianca": 0.5,
    }
)


class FakeAIProvider:
    """Implementação de teste de ``AIProvider`` (Protocol, sem herança).

    Exemplo:
        >>> fake = FakeAIProvider(['{"ok": true}', MARCADOR_ERRO])
        >>> # 1ª chamada: retorna '{"ok": true}'
        >>> # 2ª chamada: levanta AIProviderError
    """

    name: str = "fake"

    def __init__(self, respostas: list[str] | None = None) -> None:
        """Inicializa o fake com a fila de respostas programadas.

        Args:
            respostas: Respostas brutas a devolver, uma por chamada de
                ``generate_json``. Um item ``"__erro__"`` simula falha do
                provedor. Se ``None`` ou vazio, uma resposta padrão válida é usada.
        """
        if respostas and len(respostas) > 0:
            self._respostas: list[str] = list(respostas)
        else:
            # Usa a resposta padrão quando nenhuma é configurada
            self._respostas: list[str] = [RESPOSTA_PADRAO]

    async def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        """Devolve a próxima resposta da fila (FIFO) ou levanta erro.

        Args:
            system_prompt: Prompt de sistema (ignorado pelo fake, mas
                registrado para depuração).
            user_prompt: Prompt do usuário (ignorado pelo fake).

        Returns:
            A resposta bruta programada.

        Raises:
            AIProviderError: Se o item consumido for o marcador de erro.
        """
        self._system_prompt = system_prompt
        self._user_prompt = user_prompt

        if not self._respostas:
            mensagem = "FakeAIProvider sem respostas programadas"
            raise AIProviderError(mensagem, provedor=self.name)

        resposta = self._respostas.pop(0)
        if resposta == MARCADOR_ERRO:
            mensagem = "Falha simulada do provedor de IA"
            raise AIProviderError(mensagem, provedor=self.name)

        return resposta