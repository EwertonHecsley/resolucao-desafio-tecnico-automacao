"""FakeIAProvider para testes — simula classificações sem chamar API real."""

from domain.ports import IAProvider


class FakeAIProvider(IAProvider):
    """Fake AI provider que simula classificações de mensagens."""

    def __init__(self) -> None:
        """Inicializa o fake provider sem dependências externas."""
        pass

    async def classify(
        self,
        message: str,
        meta: dict[str, object] | None = None,  # noqa: ARG002
    ) -> str:
        """
        Simula uma classificação de IA.

        Args:
            message: Mensagem a ser classificada.
            meta: Metadados opcionais.

        Returns:
            Categoria da classificação (ex: "suporte técnico").
        """
        # Simula um delay de processamento
        import asyncio

        await asyncio.sleep(0.01)

        # Classificação fake baseada na primeira palavra
        first_word = message.split()[0].lower() if message else ""
        if first_word in ["pedido", "compra", "comprar", "comprar um"]:
            return "suporte técnico"
        elif first_word in ["cancelar", "devolução", "reembolso", "reembolsar"]:
            return "suporte financeiro"
        elif first_word in ["meu pedido", "meu saldo", "minha conta"]:
            return "suporte cliente"
        elif first_word in ["natal", "ano novo", "feliz", "parabéns"]:
            return "marketing"
        else:
            return "greeting"
