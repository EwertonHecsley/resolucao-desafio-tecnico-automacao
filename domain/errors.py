"""Erros de domínio relacionados a provedores de IA."""

from __future__ import annotations


class AIProviderError(Exception):
    """Erro ao comunicar ou obter resposta do provedor de IA.

    Levantado por qualquer implementação de ``AIProvider`` quando a
    chamada ao provedor falha (rede, autenticação, indisponibilidade).
    """

    def __init__(self, mensagem: str, provedor: str | None = None) -> None:
        """Inicializa o erro com mensagem e provedor opcional.

        Args:
            mensagem: Descrição do problema ocorrido.
            provedor: Nome do provedor que originou o erro, se conhecido.
        """
        self.provedor = provedor
        super().__init__(mensagem)


class InvalidAIResponseError(AIProviderError):
    """Resposta do provedor de IA não é um JSON válido ou não passou na validação.

    Levantado após esgotadas as tentativas de retry definidas pela SPEC
    (máx. 2) — a resposta deve sempre ser validada com Pydantic.
    """
