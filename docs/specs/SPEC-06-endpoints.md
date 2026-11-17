## SPEC-06 — Endpoints da API

**Objetivo:** API funcional que junta tudo.

**Requisitos**
- `app/api/deps.py`: dependências via `Depends` que constroem `AIProvider` (factory), `ClassifierService`, `MessageRepository` e `Notifier` a partir de `Settings`. Em testes devem ser substituíveis por `app.dependency_overrides`.
- `app/api/routes.py` e registro em `main.py`:
  - `POST /classify` → recebe `MessageIn`, retorna `Classification` (não salva, não notifica).
  - `POST /messages` → recebe `MessageIn`; fluxo: classificar → montar `ProcessedMessage` (com `provider` usado) → `repository.save` → `notifier.notify` → se `True`, `repository.mark_notified` e `notificado=true` na resposta. Retorna `201` com `ProcessedMessage`.
  - `GET /messages?limit=` → lista (padrão 50, máximo 200).
  - `GET /messages/{id}` → detalhe, `404` se não existir.
  - `GET /health` (já existe) e `GET /health/ai` (faz uma chamada simples ao provedor ativo e informa o `name` e se respondeu).
- Autenticação simples: header `X-API-Key` comparado com `API_KEY` (env) nas rotas `POST`. Se `API_KEY` estiver vazia, a verificação fica desativada (útil em desenvolvimento).
- Tratamento de erros em JSON claro: `422` entrada inválida, `502` falha da IA (`AIProviderError` ou `InvalidAIResponseError`), `503` banco indisponível.
- Exemplos no Swagger (`/docs`) para o corpo de `POST /messages`.

**Aceite**
- Testes com `TestClient`, `FakeAIProvider`, repositório em memória e notifier falso cobrindo: 201 feliz, 422, 502 (IA falhando), 401 sem `X-API-Key` quando `API_KEY` definida, 404 em `GET /messages/{id}`, e `notificado=false` quando o notifier retorna `False` (a API ainda responde 201).
- Exemplo de `curl` funcionando:

```bash
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"texto":"Meu boleto venceu, como emito a segunda via?","remetente":"Maria","canal":"whatsapp"}'
```

**Fora de escopo:** Dockerfile, compose completo, fluxo n8n, README final.

---

