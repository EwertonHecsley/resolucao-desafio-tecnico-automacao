# IA Classifier API

API para classificação de mensagens com IA, com salvamento no PostgreSQL e webhook para n8n.

## Notificações para o n8n (SPEC-05)

Configure `N8N_WEBHOOK_URL`, `N8N_WEBHOOK_SECRET` e (opcionalmente)
`N8N_TIMEOUT_SECONDS` (padrão `5`) no `.env` — veja o `.env.example`.

O n8n expõe **duas URLs de webhook**, que não são intercambiáveis:

| URL | Quando funciona |
| --- | --- |
| `/webhook-test/...` | Somente com o botão **"Listen for test event"** ativo no editor. Para testes manuais. |
| `/webhook/...` | Produção: exige o fluxo **ativo** (toggle ligado). É a que a API usa. |

A API deve apontar para **`/webhook/classificador`**. O host muda conforme onde
a API roda:

- **Fora** do Docker Compose: `http://localhost:5678/webhook/classificador`
- **Dentro** do Docker Compose: `http://n8n:5678/webhook/classificador` (o host é o nome do serviço `n8n`)

Deixar `N8N_WEBHOOK_URL` vazio desativa as notificações: o `NullNotifier` é
usado e `notify()` retorna `False` sem fazer requisição.

O notifier **nunca derruba a API**: timeout, falha de conexão ou resposta
não-2xx geram um log de aviso (sem o segredo) e retorno `False`.

## Docker Compose (SPEC-08)

Suba tudo (Postgres + n8n + API) com um comando:

```bash
cp .env.example .env
# gere a chave de criptografia do n8n e cole em N8N_ENCRYPTION_KEY:
openssl rand -hex 32
docker compose up --build
```

Serviços:

| Serviço | URL | Descrição |
| --- | --- | --- |
| API | http://localhost:8000 | `/health`, `/api/v1/messages` |
| n8n | http://localhost:5678 | Editor de fluxos |
| Postgres | localhost:5432 | bancos `classificador` e `n8n_db` |

O workflow do n8n pode ser importado automaticamente:

```bash
docker compose --profile import run --rm n8n-import
```

Ou manualmente no n8n: **Import from File** → `n8n/workflows/classificador.json`
→ ativar o fluxo (toggle). A rota usada é `/webhook/classificador` (produção).

`docker compose down && docker compose up` preserva os volumes `postgres_data`
e `n8n_data` (dados do Postgres e fluxos do n8n).

**Tamanho da imagem da API:** ~290 MB (`python:3.12-slim` + venv, multi-stage,
usuário não-root). Apenas dependências de runtime instaladas (sem testes/linters).
