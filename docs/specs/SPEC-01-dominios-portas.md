### SPEC-01 — Domínio e portas (inversão de dependência)

**Objetivo:** definir contratos, sem nenhuma implementação de IA. **Requisitos:**

- `domain/models.py`: `MessageIn` (`texto: str` 1–5000 chars, `remetente: str | None`, `canal: str | None`), `Classification` (campos da seção 1, com `Enum`/`Literal`), `ProcessedMessage` (id, entrada, classificação, provedor usado, criado\_em).
- `domain/ports.py`:

```python
from typing import Protocol

class AIProvider(Protocol):
    name: str
    async def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        """Retorna o texto bruto (esperado: JSON). Levanta AIProviderError em falha."""

class MessageRepository(Protocol):
    async def save(self, msg: "ProcessedMessage") -> "ProcessedMessage": ...
    async def list(self, limit: int = 50) -> list["ProcessedMessage"]: ...

class Notifier(Protocol):
    async def notify(self, msg: "ProcessedMessage") -> None: ...
```

- `AIProviderError` e `InvalidAIResponseError` em `domain/errors.py`. **Aceite:** `pytest tests/test_models.py` valida limites, enums inválidos e `confianca` fora de 0–1.