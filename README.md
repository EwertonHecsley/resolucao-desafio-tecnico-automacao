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
