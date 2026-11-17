"""Factory de adaptadores de IA.

Cria instâncias de provedores baseados na variável de ambiente AI_PROVIDER.
"""


class Factory:
    """Factory para criar instâncias de IAProvider."""

    @staticmethod
    def create() -> str:
        """
        Retorna o provedor de IA configurado para uso.

        Returns:
            Nome do provedor configurado (ex: "openai", "google").
        """
        # TODO: (SPEC-xx) Implementar leitura real de settings aqui
        return "openai"
