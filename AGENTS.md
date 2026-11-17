# Regras do projeto

## Contexto
API FastAPI que classifica mensagens de clientes com IA, salva no PostgreSQL e
dispara um webhook para o n8n. Desafio técnico Kodie (caso 4.1).

## Arquitetura (obrigatória)
- Inversão de dependência: `services/` depende apenas de interfaces em `domain/ports.py`.
- NUNCA importe SDK de provedor de IA (openai, google, groq...) fora de `adapters/ai/`.
- O provedor é escolhido por variável de ambiente `AI_PROVIDER` via `adapters/ai/factory.py`.
- Injeção de dependência pelo `Depends` do FastAPI.

## Regras
- Python 3.12, tipagem completa, Pydantic v2, async onde fizer sentido.
- Segredos SOMENTE por variáveis de ambiente. Jamais commitar chaves. Manter `.env.example` atualizado.
- A resposta da IA SEMPRE é validada com Pydantic; JSON inválido => retry (máx. 2) e depois erro 502 claro.
- Testes com pytest; testes NÃO chamam IA real (usar FakeAIProvider).
- Implementar somente o que a SPEC atual pede. Não criar arquivos fora do escopo.
- Ao terminar: rodar `pytest`, `ruff check .` e listar os critérios de aceite atendidos.
- Commits no padrão Conventional Commits.