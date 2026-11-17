"""Serviço de classificação de mensagens.

Depende apenas de domain/ports.py — não de implementações concretas.
"""

from domain.ports import IAProvider


class Classifier:
    """
    Serviço que coordena a classificação de mensagens.

    Injeção de dependência via construtor.
    """

    def __init__(self, ai_provider: IAProvider) -> None:
        """
        Inicializa o classifier com um provider de IA.

        Args:
            ai_provider: Implementação de IAProvider (pode ser fake ou real).
        """
        self.ai_provider = ai_provider

    async def classify(self, message: str) -> str:
        """
        Classifica uma mensagem.

        Args:
            message: Mensagem a ser classificada.

        Returns:
            Categoria de classificação.
        """
        # TODO: (SPEC-xx) Adicionar lógica de retry aqui
        # Se falhar, tentar novamente (máx. 2 vezes)
        # Se falhar novamente, levantar erro
        return await self.ai_provider.classify(message=message)


async def classify_message(message: str, ai_provider: IAProvider) -> str:
    """
    Função auxiliar para classificação de mensagens.

    Args:
        message: Mensagem a ser classificada.
        ai_provider: Implementação de IAProvider.

    Returns:
        Categoria de classificação.
    """
    classifier = Classifier(ai_provider=ai_provider)
    return await classifier.classify(message=message)
