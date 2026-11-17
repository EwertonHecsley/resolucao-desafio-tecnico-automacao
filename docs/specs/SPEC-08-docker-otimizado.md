## SPEC-08 — Dockerfile otimizado e Docker Compose

**Objetivo:** o avaliador roda tudo com um comando.

**Requisitos do Dockerfile (multi-stage)**
- Estágio *builder* em `python:3.12-slim` instalando dependências (com `uv` ou `pip --no-cache-dir`) em um virtualenv ou diretório isolado.
- Estágio final em `python:3.12-slim` copiando apenas o necessário (deps instaladas + pasta `app/`).
- Camadas ordenadas para cache: arquivos de dependências copiados e instalados **antes** do código.
- Usuário não-root, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`.
- `HEALTHCHECK` batendo em `/health` (pode usar `python -c` com `urllib`, sem instalar `curl`).
- `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`.
- `.dockerignore` com `.git`, `.env`, `__pycache__`, `.venv`, `docs/prints`, `tests` (se não forem usados na imagem), `.gitnexus`.

**Requisitos do `docker-compose.yml`**
- `postgres` (imagem oficial, volume nomeado, healthcheck `pg_isready`). Um único Postgres com **dois bancos**: `classificador` (API) e `n8n_db` (n8n), criados por `docker/postgres-init/init-db.sql` montado em `/docker-entrypoint-initdb.d/`.
- `n8n` (`n8nio/n8n`): porta 5678, volume `n8n_data`, `DB_TYPE=postgresdb` e variáveis `DB_POSTGRESDB_*` apontando para `postgres`/`n8n_db`, `N8N_ENCRYPTION_KEY` vinda do `.env`, `WEBHOOK_URL=http://localhost:5678/`, `depends_on` postgres saudável.
- `api`: `build: .`, `env_file: .env`, `depends_on` postgres com `condition: service_healthy`, porta 8000. Dentro do compose, `N8N_WEBHOOK_URL=http://n8n:5678/webhook/classificador` e `DATABASE_URL` com host `postgres`.
- (Opcional) serviço `n8n-import` de execução única que roda `n8n import:workflow --input=/workflows/classificador.json` (com a pasta `n8n/workflows` montada) para o fluxo já vir carregado. Em qualquer caso, o README explica a importação manual (Import from File) e a ativação do fluxo.
- Nenhum segredo dentro do compose: tudo por `.env`. Atualizar `.env.example` com todas as variáveis (veja o apêndice).

**Aceite**
- Em máquina limpa: `cp .env.example .env && docker compose up --build` sobe os 3 serviços saudáveis.
- `POST /messages` na API aparece como execução no n8n e o registro fica no Postgres.
- `docker compose down && docker compose up` mantém dados do Postgres e os fluxos do n8n.
- Imagem da API final enxuta (informar o tamanho no README).

**Fora de escopo:** alterar o código de negócio.

