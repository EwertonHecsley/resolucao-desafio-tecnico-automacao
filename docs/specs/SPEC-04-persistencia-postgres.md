## SPEC-04 — Persistência com PostgreSQL

**Objetivo:** salvar cada mensagem processada.

**Requisitos**
- Variável `DATABASE_URL` (ex.: `postgresql+asyncpg://user:pass@postgres:5432/classificador`) em `Settings` e `.env.example`.
- Tabela `messages`: `id` UUID (PK), `texto`, `remetente`, `canal`, `categoria`, `setor`, `prioridade`, `sentimento`, `resumo`, `confianca`, `provider`, `notificado` (bool), `criado_em` (timestamptz).
- `app/adapters/repository_postgres.py`: `PostgresMessageRepository` (SQLAlchemy async) implementando `MessageRepository` (`save`, `get`, `list` ordenado do mais recente, `mark_notified`).
- Criação das tabelas no startup da aplicação (`create_all`) é suficiente; Alembic é opcional.
- Conversão entre o modelo ORM e `ProcessedMessage` isolada no adapter (o domínio não conhece SQLAlchemy).
- Para desenvolvimento, um `docker-compose.yml` provisório apenas com o serviço `postgres` (volume nomeado e healthcheck `pg_isready`). O compose completo vem na SPEC-08.

**Aceite**
- Teste de integração (marcado com `@pytest.mark.integration`, pulado se `DATABASE_URL` não estiver disponível) salva, busca, lista e marca como notificado.
- Dados persistem após `docker compose restart postgres`.
- Testes unitários da conversão ORM ↔ domínio.

**Fora de escopo:** rotas, notifier, n8n, migrações complexas.
