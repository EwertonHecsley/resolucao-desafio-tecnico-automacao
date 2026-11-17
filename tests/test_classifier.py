"""Testes de aceite da SPEC-02 — ClassifierService.

Todos os cenários usam FakeAIProvider (sem rede), conforme exigido pela
SPEC e pelas regras do AGENTS.md.
"""

import json

import pytest

from app.adapters.ai.fake import MARCADOR_ERRO, FakeAIProvider
from domain.errors import AIProviderError, InvalidAIResponseError
from domain.models import Categoria, Classification, MessageIn, Setor
from services.classifier import ClassifierService

JSON_VALIDO = json.dumps(
    {
        "categoria": "duvida",
        "setor": "financeiro",
        "prioridade": "media",
        "sentimento": "neutro",
        "resumo": "Cliente pede segunda via de boleto vencido.",
        "confianca": 0.95,
    },
    ensure_ascii=False,
)

MENSAGEM = MessageIn(
    texto="Meu boleto venceu ontem, como emito a segunda via?",
    remetente="joao@example.com",
    canal="whatsapp",
)


class FakeAIProviderComContagem(FakeAIProvider):
    """FakeAIProvider com contador de chamadas (instrumento de teste)."""

    def __init__(self, respostas: list[str] | None = None) -> None:
        super().__init__(respostas)
        self.chamadas = 0

    async def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        self.chamadas += 1
        return await super().generate_json(system_prompt, user_prompt)


def _service(respostas: list[str], max_retries: int = 2) -> ClassifierService:
    """Fábrica de serviço com FakeAIProvider programado."""
    return ClassifierService(ai=FakeAIProvider(respostas), max_retries=max_retries)


def _service_com_contador(
    respostas: list[str],
) -> tuple[ClassifierService, FakeAIProviderComContagem]:
    """Serviço + provider, para inspecionar contagem de chamadas."""
    provider = FakeAIProviderComContagem(respostas)
    return ClassifierService(ai=provider), provider


class TestClassificacaoValida:
    """Cenários de sucesso."""

    async def test_json_valido_retorna_classification(self) -> None:
        """JSON válido → Classification correta, com 1 chamada."""
        service, provider = _service_com_contador([JSON_VALIDO])
        resultado = await service.classify(MENSAGEM)
        assert isinstance(resultado, Classification)
        assert resultado.categoria is Categoria.DUVIDA
        assert resultado.setor is Setor.FINANCEIRO
        assert resultado.confianca == 0.95
        assert provider.chamadas == 1

    async def test_json_dentro_de_cercas_markdown_aceito(self) -> None:
        """Resposta cercada por ```json ... ``` é limpa e aceita."""
        cercado = f"```json\n{JSON_VALIDO}\n```"
        resultado = await _service([cercado]).classify(MENSAGEM)
        assert resultado.setor is Setor.FINANCEIRO

    async def test_json_com_cercas_sem_linguagem_aceito(self) -> None:
        """Resposta cercada por ``` (sem `json`) também é aceita."""
        cercado = f"```\n{JSON_VALIDO}\n```"
        resultado = await _service([cercado]).classify(MENSAGEM)
        assert resultado.categoria is Categoria.DUVIDA

    async def test_json_com_texto_ao_redor_extraido(self) -> None:
        """JSON com texto antes/depois é extraído do 1º { ao último }."""
        sujo = f"Claro! Aqui está a classificação:\n{JSON_VALIDO}\nQualquer dúvida, avise."
        resultado = await _service([sujo]).classify(MENSAGEM)
        assert resultado.categoria is Categoria.DUVIDA

    async def test_json_invalido_na_1a_e_valido_na_2a(self) -> None:
        """1ª resposta inválida + 2ª válida → sucesso com 2 chamadas."""
        service, provider = _service_com_contador(
            ["isto não é json", JSON_VALIDO]
        )
        resultado = await service.classify(MENSAGEM)
        assert resultado.categoria is Categoria.DUVIDA
        assert provider.chamadas == 2


class TestRetryEErro:
    """Retry por JSON inválido e propagação de AIProviderError."""

    async def test_sempre_invalido_levanta_erro_apos_3_chamadas(self) -> None:
        """Sempre inválido → InvalidAIResponseError após 1 + max_retries chamadas."""
        service, provider = _service_com_contador(
            ["invalido 1", "invalido 2", "invalido 3"]
        )
        with pytest.raises(InvalidAIResponseError):
            await service.classify(MENSAGEM)
        assert provider.chamadas == 3

    async def test_valor_fora_do_enum_e_tratado_como_invalido(self) -> None:
        """setor "rh" (fora do enum) vira tentativa inválida → retry → erro."""
        json_setor_invalido = json.dumps(
            {
                "categoria": "duvida",
                "setor": "rh",
                "prioridade": "media",
                "sentimento": "neutro",
                "resumo": "Algum resumo.",
                "confianca": 0.9,
            }
        )
        service, provider = _service_com_contador(
            [json_setor_invalido, json_setor_invalido, json_setor_invalido]
        )
        with pytest.raises(InvalidAIResponseError):
            await service.classify(MENSAGEM)
        assert provider.chamadas == 3

    async def test_valor_fora_do_enum_com_retry_valido_funciona(self) -> None:
        """Enum inválido na 1ª + válido na 2ª → sucesso com 2 chamadas."""
        json_setor_invalido = json.dumps(
            {
                "categoria": "duvida",
                "setor": "rh",
                "prioridade": "media",
                "sentimento": "neutro",
                "resumo": "Algum resumo.",
                "confianca": 0.9,
            }
        )
        resultado = await _service([json_setor_invalido, JSON_VALIDO]).classify(MENSAGEM)
        assert resultado.setor is Setor.FINANCEIRO

    async def test_ai_provider_error_propaga_sem_retry(self) -> None:
        """AIProviderError programado propaga na hora — sem retry (1 chamada)."""
        provider = FakeAIProviderComContagem([MARCADOR_ERRO, JSON_VALIDO])
        service = ClassifierService(ai=provider)
        with pytest.raises(AIProviderError) as excinfo:
            await service.classify(MENSAGEM)
        assert not isinstance(excinfo.value, InvalidAIResponseError)
        assert provider.chamadas == 1

    async def test_mensagem_de_erro_e_clara(self) -> None:
        """InvalidAIResponseError traz mensagem explicativa."""
        service = _service(["lixo", "lixo", "lixo"])
        with pytest.raises(InvalidAIResponseError, match="classif"):
            await service.classify(MENSAGEM)

    async def test_campos_faltando_e_tratado_como_invalido(self) -> None:
        """JSON válido mas sem campos do contrato → retry → erro."""
        incompleto = json.dumps({"categoria": "duvida"})
        service, provider = _service_com_contador([incompleto] * 3)
        with pytest.raises(InvalidAIResponseError):
            await service.classify(MENSAGEM)
        assert provider.chamadas == 3


class TestConstrucao:
    """Contrato do construtor."""

    async def test_max_retries_customizavel(self) -> None:
        """max_retries customizado é respeitado (1 + max_retries chamadas)."""
        provider = FakeAIProviderComContagem(["lixo", "lixo"])
        service = ClassifierService(ai=provider, max_retries=1)
        with pytest.raises(InvalidAIResponseError):
            await service.classify(MENSAGEM)
        assert provider.chamadas == 2
