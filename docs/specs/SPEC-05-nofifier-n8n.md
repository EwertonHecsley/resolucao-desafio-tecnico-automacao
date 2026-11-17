## SPEC-05 — Notifier para o n8n (integração API → n8n)

**Objetivo:** enviar a mensagem processada ao webhook do n8n sem nunca derrubar a API.

**Requisitos**
- Variáveis: `N8N_WEBHOOK_URL`, `N8N_WEBHOOK_SECRET`, `N8N_TIMEOUT_SECONDS` (padrão 5). Atualize `.env.example`.
- `app/adapters/notifier_n8n.py`: `N8nWebhookNotifier` implementando `Notifier`.
  - `POST` em `N8N_WEBHOOK_URL` com o JSON de `ProcessedMessage` (UUID e datas serializados como string).
  - Header `X-Webhook-Secret` com `N8N_WEBHOOK_SECRET`.
  - Retorna `True` se a resposta for 2xx; em qualquer falha (timeout, conexão, status não 2xx) registra um log de aviso (sem o segredo) e retorna `False`. **Nunca levanta exceção.**
- `NullNotifier` (retorna `False` sem fazer nada) para usar quando `N8N_WEBHOOK_URL` não estiver configurada.
- Observação para o README e para o `.env.example`: o n8n tem duas URLs, `/webhook-test/...` (só funciona com o botão "Listen for test event" ativo) e `/webhook/...` (produção, exige o fluxo **ativo**). A API deve apontar para `/webhook/classificador`. Dentro do Docker Compose o host é `n8n` (`http://n8n:5678/webhook/classificador`), fora dele é `localhost`.

**Aceite**
- Testes com `httpx.MockTransport`: 200 → `True`; 500 → `False`; timeout → `False`; header `X-Webhook-Secret` enviado; payload correto.
- Com o n8n parado, `notify` retorna `False` e não levanta exceção.

**Fora de escopo:** rotas, criação do fluxo no n8n.