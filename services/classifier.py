"""Serviço de classificação de mensagens.

Depende apenas de domain/ports.py — não de implementações concretas.
"""

from domain.ports import AIProvider


class Classifier:
    """
    Serviço que coordena a classificação de mensagens.

    Injeção de dependência via construtor.
    """

    def __init__(self, ai_provider: AIProvider) -> None:
        """
        Inicializa o classifier com um provider de IA.

        Args:
            ai_provider: Implementação de AIProvider (pode ser fake ou real).
        """
        self.ai_provider = ai_provider

    async def classificar(self, system_prompt: str, user_prompt: str) -> str:
        """
        Gera a classificação bruta (JSON em texto) via provedor de IA.

        A lógica real de validação da resposta e retry (máx. 2) será
        implementada na SPEC-02.

        Args:
            system_prompt: Prompt de sistema com as regras de classificação.
            user_prompt: Prompt do usuário (mensagem + metadados).

        Returns:
            Texto bruto retornado pelo provedor (esperado: JSON).
        """
        # TODO: (SPEC-02) Validar resposta com Pydantic; retry (máx. 2) e erro 502.
        return await self.ai_provider.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
