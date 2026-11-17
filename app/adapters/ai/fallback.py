"""FallbackAIProvider — tenta provedores em ordem (SPEC-03)."""

from __future__ import annotations

from domain.errors import AIProviderError
from domain.ports import AIProvider


class FallbackAIProvider:
    """Composição de provedores com fallback sequencial.

    Tenta cada provedor na ordem dada. Se um levantar ``AIProviderError``,
    tenta o próximo; se todos falharem, levanta ``AIProviderError``
    agregando os motivos. ``name`` reflete o provedor que respondeu
    (útil para gravar no banco).
    """

    def __init__(self, providers: list[AIProvider]) -> None:
        """Inicializa o fallback com a lista de provedores.

        Args:
            providers: Provedores em ordem de preferência. Deve conter
                ao menos um provedor.
        """
        if not providers:
            raise AIProviderError(
                "FallbackAIProvider requer ao menos um provedor"
            )
        self._providers = providers
        self.name: str = providers[0].name

    async def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        """Tenta cada provedor em ordem até um responder.

        Args:
            system_prompt: Instrução de sistema.
            user_prompt: Prompt do usuário.

        Returns:
            Texto bruto da resposta do primeiro provedor que responder.

        Raises:
            AIProviderError: Se todos os provedores falharem; a mensagem
                agrega o motivo de cada um.
        """
        motivos: list[str] = []
        for provedor in self._providers:
            try:
                resposta = await provedor.generate_json(
                    system_prompt, user_prompt
                )
            except AIProviderError as erro:
                motivos.append(f"{provedor.name}: {erro}")
                continue
            self.name = provedor.name
            return resposta

        detalhe = "; ".join(motivos)
        raise AIProviderError(
            f"Todos os provedores de IA falharam ({detalhe})",
            provedor=self._providers[0].name,
        )
