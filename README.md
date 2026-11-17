# IA Classifier API

API FastAPI que classifica mensagens de clientes com Inteligência Artificial,
persiste o resultado no PostgreSQL e dispara um webhook para o n8n, que encaminha
cada mensagem ao setor responsável.

Projeto integrador dos módulos de Fundamentos de IA e Automação e Agentes —
**Desafio Técnico Kodie (caso 4.1)**.

---

## 1. Apresentação da ideia

A ideia surgiu de uma situação comum em pequenas empresas: o atendimento
chega por vários canais (WhatsApp, e-mail, formulário) e alguém precisa ler
cada mensagem, decidir do que se trata e encaminhar manualmente para a pessoa
certa. É um trabalho repetitivo, lento e sujeito a erros — principalmente quando
o volume diário de mensagens cresce.

A proposta foi transformar essa triagem manual em um fluxo automático:
a IA interpreta o texto e devolve uma classificação estruturada; a API
valida, salva e repassa o resultado; o n8n aplica as regras de negócio
(roteamento por setor e revisão humana quando a confiança é baixa).

O projeto foi pensado para ser **simples de executar e fácil de demonstrar**:
com `AI_PROVIDER=fake` ele funciona sem chave de API e sem internet, e com
Docker Compose sobe API, banco e n8n em um único comando.

### 2. Problema escolhido (caso 4.1)

Foi escolhido o **caso 4.1 — Classificação de Mensagens** do PDF do desafio:

> Uma empresa recebe mensagens de clientes com diferentes tipos de solicitações,
> mas não possui um processo organizado para identificar cada assunto.
> Desenvolva uma solução que utilize IA para analisar e classificar as mensagens
> em categorias, como dúvidas, reclamações ou solicitações.

Antes da solução, o processo era:

1. Uma pessoa lia cada mensagem recebida.
2. Identificava manualmente o assunto (dúvida, reclamação, solicitação...).
3. Decidia o setor responsável (suporte, financeiro, comercial, logística...).
4. Encaminhava a mensagem, sem histórico padronizado nem registro confiável.

Problemas decorrentes: tempo gasto em leitura repetitiva, encaminhamentos
errados, ausência de priorização e nenhum registro estruturado para consulta.

### 3. Solução proposta

A IA atua como **classificadora de triagem**, e não como resposta final ao
cliente. Para cada mensagem ela devolve um JSON validado com:

| Campo | Descrição | Valores possíveis |
| --- | --- | --- |
| `categoria` | Tipo da mensagem | `duvida`, `reclamacao`, `solicitacao`, `elogio`, `outro` |
| `setor` | Área responsável | `suporte`, `financeiro`, `comercial`, `logistica`, `geral` |
| `prioridade` | Urgência do atendimento | `baixa`, `media`, `alta` |
| `sentimento` | Tom da mensagem | `positivo`, `neutro`, `negativo` |
| `resumo` | Síntese em até 200 caracteres | texto |
| `confianca` | Grau de certeza (0 a 1) | número |

O prompt estruturado (`services/prompts.py`) define o formato, as regras de
mapeamento (ex.: "boleto/pagamento → financeiro", "entrega/rastreio →
logística") e exemplos. Quando a mensagem é ambígua, a IA é instruída a usar
`setor = geral` com `confianca < 0.6`, o que dispara revisão humana no n8n.

A resposta bruta da IA passa por limpeza (remoção de cercas markdown),
`json.loads` e validação com Pydantic (`Classification`). Se o JSON for inválido,
há retry (máximo de 2 tentativas extras) e, ainda falhando, a API responde
**502** com mensagem clara — nunca devolve dados não validados.

A automação fica no n8n: se a confiança for menor que `0.6`, o fluxo vai para
**Revisão Humana**; caso contrário, um *Switch* roteia por setor e um node
`Code` monta o destino (`<setor>@empresa.com`) e a mensagem a encaminhar.
Nenhuma credencial externa é necessária no fluxo.

### 4. Tecnologias utilizadas

| Camada | Tecnologia | Uso no projeto |
| --- | --- | --- |
| Back-end | Python 3.12, FastAPI, Uvicorn | API HTTP assíncrona, injeção de dependências via `Depends` |
| Validação | Pydantic v2, Pydantic Settings | Contratos de domínio e configuração por variáveis de ambiente |
| Persistência | PostgreSQL 16, SQLAlchemy 2 (async), asyncpg, Alembic | Armazenamento das mensagens processadas |
| IA | Porta `AIProvider` com adaptadores `fake`, Gemini, Groq e OpenAI | Classificação; provedor escolhido por `AI_PROVIDER`, com fallback opcional |
| Automação | n8n | Workflow de 7 nodes: webhook → normalização → decisão → roteamento → resposta |
| HTTP cliente | httpx | Chamada ao provedor de IA e ao webhook do n8n |
| Testes | pytest, pytest-asyncio, pytest-cov | Testes unitários/integração com `FakeAIProvider` (sem IA real) |
| Qualidade | ruff, mypy, black, isort | Lint, formatação e checagem de tipos |
| Infraestrutura | Docker, Docker Compose | Multi-stage build + Postgres, n8n e API orquestrados |

### Arquitetura

O projeto segue **inversão de dependência**: `services/` depende apenas das
interfaces em `domain/ports.py`. Nenhum SDK de provedor de IA é importado fora
de `adapters/ai/`, e a factory (`adapters/ai/factory.py`) escolhe o provedor a
partir de `AI_PROVIDER`. Trocar de provedor não exige mudança em `services/` nem
em `api/`.

```text
api/            → rotas FastAPI e injeção de dependências (Depends)
services/       → regras de classificação, prompt e retry (depende só de domain/)
domain/         → modelos, enums, erros e portas (AIProvider, MessageRepository, Notifier)
adapters/       → implementações concretas: IA, repositório Postgres, notifier n8n
```

### 5. Funcionamento do sistema

O fluxo completo é **API recebe → IA processa → n8n executa**:

```mermaid
flowchart LR
    C[Cliente] -->|POST /api/v1/messages| A[API FastAPI]
    A -->|prompt estruturado| I{IA Provider}
    I -->|JSON validado| A
    A -->|save| D[(PostgreSQL)]
    A -->|POST + X-Webhook-Secret| N[n8n Webhook]
    N --> E[Edit Fields]
    E --> Q{confianca < 0.6?}
    Q -->|sim| R[Revisão Humana]
    Q -->|não| S[Switch por setor]
    S --> F[Encaminhar Setor]
    R --> W[Respond to Webhook]
    F --> W
    W -->|200 OK| A
    A -->|201 + notificado| C
```

Passo a passo:

1. O cliente envia `texto` e, opcionalmente, `remetente` e `canal`.
2. A API monta o prompt, chama o provedor de IA e valida o JSON retornado.
3. A mensagem processada é salva no PostgreSQL com um UUID.
4. A API envia o payload para o webhook de produção do n8n com o header
   `X-Webhook-Secret`. Falhas de rede/timeout **não derrubam a API**: o campo
   `notificado` permanece `false`.
5. O n8n normaliza os campos, aplica a regra de confiança, roteia por setor e
   responde `{"status":"encaminhado","setor":"..."}`.
6. Com `200` do n8n, a API marca `notificado = true` e responde `201`.

#### Exemplos de `curl`

Classificação direta (sem salvar e sem notificar — útil para testar o prompt):

```bash
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "texto": "Meu pedido ainda não chegou, o que aconteceu?",
    "remetente": "joao@example.com",
    "canal": "whatsapp"
  }'
```

Fluxo completo (classifica, salva no Postgres e notifica o n8n):

```bash
curl -X POST http://localhost:8000/api/v1/messages \
  -H "Content-Type: application/json" \
  -H "X-API-Key: troque-esta-chave" \
  -d '{
    "texto": "Meu pedido ainda não chegou, o que aconteceu?",
    "remetente": "joao@example.com",
    "canal": "whatsapp"
  }'
```

O header `X-API-Key` é obrigatório quando `API_KEY` está definida no `.env`
(se vazia, a verificação fica desativada em desenvolvimento). A rota
`/api/v1/messages` exige `DATABASE_URL` configurada; `/api/v1/classify` não.

Resposta esperada (`201 Created`):

```json
{
  "id": "9b6f1a2e-4c3d-4e5f-8a7b-1c2d3e4f5a6b",
  "entrada": {
    "texto": "Meu pedido ainda não chegou, o que aconteceu?",
    "remetente": "joao@example.com",
    "canal": "whatsapp"
  },
  "classificacao": {
    "categoria": "reclamacao",
    "setor": "logistica",
    "prioridade": "alta",
    "sentimento": "negativo",
    "resumo": "Cliente relata atraso na entrega do pedido.",
    "confianca": 0.92
  },
  "provedor": "fake",
  "criado_em": "2026-11-17T19:23:43.282Z",
  "notificado": true
}
```

Outros endpoints: `GET /health`, `GET /api/v1/messages?limit=50` e
`GET /api/v1/messages/{id}`. A documentação interativa fica em
`http://localhost:8000/docs`.

#### URLs do webhook do n8n

O n8n expõe **duas URLs de webhook, que não são intercambiáveis**:

| URL | Quando funciona |
| --- | --- |
| `/webhook-test/...` | Somente com o botão **"Listen for test event"** ativo no editor (testes manuais). |
| `/webhook/...` | Produção: exige o fluxo **ativo** (toggle ligado). É a que a API usa. |

A API aponta para `/webhook/classificador`. O host muda conforme onde a API
roda:

- **Fora** do Docker Compose: `http://localhost:5678/webhook/classificador`
- **Dentro** do Docker Compose: `http://n8n:5678/webhook/classificador`
  (o host é o nome do serviço `n8n`)

Deixar `N8N_WEBHOOK_URL` vazio desativa as notificações: o `NullNotifier` é
usado e `notify()` retorna `False` sem fazer requisição.

### 6. Como executar

#### Opção A — Com Docker Compose (recomendado)

Sobe Postgres + n8n + API com um comando:

```bash
cp .env.example .env
# gere a chave de criptografia do n8n e cole em N8N_ENCRYPTION_KEY:
openssl rand -hex 32
docker compose up --build
```

| Serviço | URL | Descrição |
| --- | --- | --- |
| API | http://localhost:8000 | `/health`, `/docs`, `/api/v1/messages` |
| n8n | http://localhost:5678 | Editor de fluxos |
| Frontend Sandbox | http://localhost:8501 | Interface web para testar (com --profile demo) |
| Postgres | localhost:5432 | bancos `classificador` e `n8n_db` |

Importar o workflow do n8n automaticamente (uma vez, após o n8n ficar saudável):

```bash
docker compose --profile import run --rm n8n-import
```

Ou manualmente no n8n: **Import from File** → `n8n/workflows/classificador.json`
→ **ativar o fluxo (toggle)**. A rota usada é `/webhook/classificador`
(produção). O toggle precisa estar ligado, senão a API receberá falha na
notificação e `notificado` ficará `false`.

Para iniciar o **Frontend Sandbox** (interface web para testes):

```bash
docker compose --profile demo up --build frontend
```

Isso abrirá http://localhost:8501 com:
- Testes rápidos (classificação sem salvar)
- Fluxo completo (salvar + notificar n8n)
- Histórico de mensagens
- Visualização em tempo real do status do n8n

`docker compose down && docker compose up` preserva os volumes `postgres_data`
e `n8n_data` (dados do Postgres e fluxos do n8n). Para recriar do zero, use
`docker compose down -v`.

#### Opção B — Sem Docker

Requisitos: Python 3.12, PostgreSQL acessível e (opcionalmente) n8n rodando.

```bash
# 1. Ambiente virtual e dependências
python3.12 -m venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"        # ou: pip install -e ".[dev]"

# 2. Configuração
cp .env.example .env
# Edite o .env:
#   DATABASE_URL=postgresql+asyncpg://postgres:SUA_SENHA@localhost:5432/classificador
#   N8N_WEBHOOK_URL=http://localhost:5678/webhook/classificador
#   AI_PROVIDER=fake                (demonstração sem chave)

# 3. Banco de dados (crie o banco "classificador" no seu PostgreSQL local)
#    As tabelas são criadas automaticamente no startup da API.

# 4. Subir a API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. Testar
curl http://localhost:8000/health
```

Para rodar os testes (usam `FakeAIProvider`, sem chamar IA real):

```bash
pytest
ruff check .
```

#### Trocar de chave ou de provedor de IA

1. **Chave inválida ou limite estourado:** altere a chave no `.env` e rode
   `docker compose up -d api` (ou reinicie o Uvicorn, se estiver sem Docker).
2. **Trocar de provedor:** altere `AI_PROVIDER` (ex.: `groq`) e reinicie a API.
   Nenhuma linha de código muda. Preencha também a chave correspondente
   (`GEMINI_API_KEY`, `GROQ_API_KEY` ou `OPENAI_API_KEY`) e, se desejar, o modelo
   (`*_MODEL`).
3. **Fallback automático:** `AI_FALLBACK_PROVIDERS=groq,gemini` faz o
   `FallbackAIProvider` tentar o próximo provedor em caso de erro.
4. **Demonstração sem chave ou internet:** `AI_PROVIDER=fake`.
5. **Novo provedor:** criar `adapters/ai/novo.py` implementando `generate_json`,
   registrar na factory e adicionar as variáveis ao `.env.example`. Nada em
   `services/` ou `api/` muda.

---

## Documentação visual do fluxo n8n

As capturas e a configuração individual de **todos os nodes**, bem como os
dados reais recebidos e processados em cada etapa, estão registradas em
[`docs/prints/print-fluxo-n8n-implantado.md`](docs/prints/print-fluxo-n8n-implantado.md):

- **Fluxo completo:** canvas com os 7 nodes conectados e a visão geral da automação.
- **Execução bem-sucedida:** aba *Executions* com execuções `success` disparadas
  por `POST /api/v1/messages` real da API.
- **Configuração individual de cada node:** Webhook, Edit Fields, IF "Baixa
  Confiança?", Revisão Humana, Roteador por Setor (Switch), Encaminhar Setor
  (Code) e Respond to Webhook — com parâmetros e expressões.
- **Resultados por etapa:** payloads reais de saída do `Edit Fields`, do node de
  revisão, do encaminhamento e a resposta HTTP final do webhook.

O fluxo exportado está em
[`n8n/workflows/classificador.json`](n8n/workflows/classificador.json), sem
credenciais. O PDF original do desafio está em
[`docs/desafio/Desafio_Tecnico_IA_e_Automacao_KODIE.pdf`](docs/desafio/Desafio_Tecnico_IA_e_Automacao_KODIE.pdf).

## Dockerfile e docker-compose.yml

### Dockerfile (multi-stage)

O `Dockerfile` usa dois estágios para manter a imagem final enxuta:

| Estágio | O que faz |
| --- | --- |
| `builder` (`python:3.12-slim`) | Cria `/opt/venv` e instala as dependências com `uv`. Como as dependências são copiadas antes do código, essa camada é reaproveitada pelo cache quando só o código muda. |
| `final` (`python:3.12-slim`) | Copia somente o venv e os diretórios `app/`, `domain/` e `services/`. Define `PATH` para o venv, cria o usuário não-root `appuser`, configura o `HEALTHCHECK` em `/health` e inicia o Uvicorn na porta 8000. |

A imagem final tem cerca de **290 MB**: só dependências de runtime (sem
testes, linters ou caches). Rodar como `appuser` evita que um processo com
privilégios de root manipule o container. O `HEALTHCHECK` consulta
`http://localhost:8000/health` a cada 30s (10s de timeout, 3 retries).

### docker-compose.yml

| Serviço | Responsabilidade | Detalhes |
| --- | --- | --- |
| `postgres` | Banco da API e do n8n | imagem `postgres:16-alpine`, bancos `classificador` e `n8n_db` (criado por `docker/postgres-init/init-db.sql`), volume `postgres_data`, healthcheck com `pg_isready`. |
| `n8n` | Automação | conectado ao Postgres, chave `N8N_ENCRYPTION_KEY` obrigatória, `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` para usar variáveis de ambiente nos nodes, volume `n8n_data`, `extra_hosts` para chamar a API na máquina via `host.docker.internal`, healthcheck em `/healthz`. |
| `api` | API FastAPI | build via `Dockerfile`, `DATABASE_URL` apontando para o host `postgres`, `N8N_WEBHOOK_URL` apontando para o host `n8n`, carrega variáveis do `.env`. |
| `n8n-import` | Importação do workflow | mesmo `image` do n8n, `entrypoint: n8n import:workflow --input=/workflows/classificador.json`, protegido pelo profile `import` — executa apenas quando solicitado. |

Volumes nomeados (`postgres_data`, `n8n_data`) garantem persistência entre
`down`/`up`. As dependências usam `condition: service_healthy` para que a API e
o n8n só iniciem depois que o Postgres estiver pronto. O workflow do n8n é
montado somente-leitura em `/workflows`.

## Segurança

- Todas as chaves, senhas e segredos são lidos **somente de variáveis de
  ambiente** (`app/config.py`, via Pydantic Settings). Nenhum segredo está no
  código-fonte.
- O [`.env.example`](.env.example) contém apenas nomes de variáveis e valores
  placeholder (`your-...-here`, `troque-esta-chave`). O `.env` real está no
  `.gitignore` e nunca deve ser commitado.
- O JSON exportado do n8n não contém credenciais: o bloco `credentials` foi
  removido antes da exportação; o segredo do webhook vive apenas na credencial
  `httpHeaderAuth` do n8n e em `N8N_WEBHOOK_SECRET`.
- O notifier registra logs de falha sem incluir o segredo.
- Foi feita varredura no histórico do git e nos arquivos versionados: não há
  chaves de API, senhas ou tokens reais.

## Aceite — SPEC-09 (mapeado ao PDF, seções 6 a 9)

- [x] API FastAPI funcional
- [x] Integração com modelo de IA (via porta `AIProvider`)
- [x] Prompt estruturado
- [x] Resposta da IA em JSON validada (retry máx. 2 e erro 502 claro)
- [x] Fluxo n8n funcional
- [x] Integração API ↔ n8n
- [x] README com as 6 seções exigidas
- [x] Prints: fluxo completo, execução com sucesso, configuração de cada node,
      dados de cada etapa, com descrições (em `docs/prints/`)
- [x] JSON do n8n exportado (`n8n/workflows/classificador.json`, sem credenciais)
- [x] `.env.example` sem segredos e nenhuma chave no repositório (histórico conferido)
- [x] Diferencial: Dockerfile + docker-compose.yml + instruções detalhadas no README
- [x] Frontend Sandbox com Streamlit para testes (com --profile demo)
- [x] Link do repositório GitHub:
       https://github.com/EwertonHecsley/resolucao-desafio-tecnico-automacao
