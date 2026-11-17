## SPEC-09 — Documentação e entrega

**Objetivo:** cumprir as seções 6 a 9 do PDF do desafio.

**Requisitos do README.md** (nesta ordem)
1. Apresentação da ideia (de onde surgiu).
2. Problema escolhido (caso 4.1).
3. Solução proposta (papel da IA no processo).
4. Tecnologias utilizadas.
5. Funcionamento do sistema (API recebe → IA processa → n8n executa), com o diagrama e exemplos de `curl`.
6. Como executar (com Docker Compose e sem Docker), incluindo como trocar de provedor de IA e como importar e ativar o fluxo do n8n.

**Documentação visual** (`docs/prints/` + descrições curtas no README)
- Fluxo completo com todos os nodes conectados.
- Execução bem-sucedida.
- Configuração **individual de cada node** usado.
- Dados recebidos e processados em cada etapa importante.

**Demais itens:** `.env.example` sem segredos, JSON do n8n exportado em `n8n/workflows/`, `docker-compose.yml` e `Dockerfile` documentados, e varredura final para garantir que não há chaves no histórico do git.

**Aceite:** checklist final abaixo completo.

---

## Apêndice A — `.env.example`

```env
# --- IA (provedor ativo e fallbacks) ---
AI_PROVIDER=fake
AI_FALLBACK_PROVIDERS=
AI_TIMEOUT_SECONDS=20

GEMINI_API_KEY=
GEMINI_MODEL=
GROQ_API_KEY=
GROQ_MODEL=
OPENAI_API_KEY=
OPENAI_MODEL=

# --- API ---
API_KEY=troque-esta-chave

# --- Banco ---
POSTGRES_USER=postgres
POSTGRES_PASSWORD=troque-esta-senha
POSTGRES_DB=classificador
DATABASE_URL=postgresql+asyncpg://postgres:troque-esta-senha@postgres:5432/classificador

# --- n8n ---
N8N_WEBHOOK_URL=http://n8n:5678/webhook/classificador
N8N_WEBHOOK_SECRET=troque-este-segredo
N8N_TIMEOUT_SECONDS=5
N8N_ENCRYPTION_KEY=troque-esta-chave-longa
```

## Apêndice B — Trocar de chave ou de provedor de IA

1. **Chave inválida ou limite estourado:** altere a chave no `.env` e rode `docker compose up -d api`.
2. **Trocar de provedor:** altere `AI_PROVIDER` (ex.: `groq`) e reinicie a API. Nenhuma linha de código muda.
3. **Automático:** `AI_FALLBACK_PROVIDERS=groq,gemini` faz o `FallbackAIProvider` tentar o próximo em caso de erro.
4. **Demonstração sem chave ou internet:** `AI_PROVIDER=fake`.
5. **Novo provedor:** criar `adapters/ai/novo.py` implementando `generate_json`, registrar na factory e adicionar as variáveis ao `.env.example`. Nada em `services/` ou `api/` muda.

## Apêndice C — Checklist final (mapeado ao PDF)

- [ ] API FastAPI funcional
- [ ] Integração com modelo de IA (via porta `AIProvider`)
- [ ] Prompt estruturado
- [ ] Resposta da IA em JSON validada
- [ ] Fluxo n8n funcional
- [ ] Integração API ↔ n8n
- [ ] README com as 6 seções exigidas
- [ ] Prints: fluxo completo, execução com sucesso, configuração de cada node, dados de cada etapa, com descrições
- [ ] JSON do n8n exportado (sem credenciais)
- [ ] `.env.example` e nenhuma chave no repositório (conferir o histórico do git)
- [ ] Diferencial: Dockerfile + docker-compose.yml + instruções no README
- [ ] Link do repositório GitHub enviado