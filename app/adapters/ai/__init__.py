"""Fakes para testes — implementações de portas do domínio sem efeitos externos."""

from app.adapters.ai.fake import MARCADOR_ERRO, FakeAIProvider

__all__ = ["FakeAIProvider", "MARCADOR_ERRO"]
