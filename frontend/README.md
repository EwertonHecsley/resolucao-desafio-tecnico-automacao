# Frontend Sandbox

Interface web (Streamlit) para testar o classificador de mensagens com IA.
Feita para o recrutador testar visualmente todo o fluxo: classificação →
persistência → webhook n8n.

## Funcionalidades

- 🧪 **Teste Rápido**: Classifica mensagens sem salvar no banco
- ⚡ **Fluxo Completo**: Salva no banco e notifica o n8n
- 📊 **Histórico**: Visualização de todas as mensagens processadas
- 🤖 **Status da IA**: Provedor ativo e saúde do endpoint

## Tecnologias

- **Streamlit**: Framework Python para apps web interativos
- **Requests**: Chamadas HTTP para a API FastAPI

## Como Usar

### Opção 1 - Com Docker (Recomendado)

```bash
docker compose --profile demo up --build frontend
```

Acesse http://localhost:8501

### Opção 2 - Localmente

```bash
# 1. Instalar dependências (requirements.txt na raiz do projeto)
pip install -r requirements.txt

# 2. Rodar
streamlit run frontend/app.py
```

## Configuração

O frontend usa a seguinte configuração padrão:

- **API Base URL**: `http://api:8000/api/v1` (dentro do Docker Compose)
- **API Key**: lida de `.streamlit/secrets.toml` → `SANDBOX_API_KEY`
  (fallback: `kodie-sandbox-token`)

> ⚠️ **Importante**: o Streamlit promove chaves escalares de
> `secrets.toml` para `os.environ`. Por isso a chave do sandbox se chama
> `SANDBOX_API_KEY` — **nunca** `API_KEY`, que é a setting de autenticação
> do backend (SPEC-06). Quando a autenticação da API estiver ativada
> (`API_KEY` definido no `.env` da API), o valor de `SANDBOX_API_KEY`
> deve coincidir com o `API_KEY` do backend.

Exemplo de `.streamlit/secrets.toml`:

```toml
SANDBOX_API_KEY = "kodie-sandbox-token"
```

## Páginas

### 🏠 Início
- Dashboard com estatísticas
- Instruções de como testar
- Exemplos de mensagens

### 🧪 Classificar
- Campo de input para mensagens
- Modos: Classificar (Rápido) vs Salvar & Notificar
- Visualização imediata dos resultados

### 📊 Histórico
- Lista de mensagens salvas
- Filtros por categoria
- Detalhes completos de cada mensagem

## Segurança

- O token do sandbox vem de `.streamlit/secrets.toml` (`SANDBOX_API_KEY`)
- Se a API estiver sem `API_KEY` no `.env`, a autenticação é desativada (dev)
- Em produção, sempre use chaves fortes

## Testes

```bash
pytest tests/frontend/ -v
```

## Troubleshooting

### Frontend não conecta à API
- Verifique se o serviço `api` está rodando: `docker compose ps`
- Confirme que a API responde: `curl http://localhost:8000/health`
- Fora do Docker, `API_BASE_URL` aponta para `http://api:8000` — suba a
  API pelo compose ou ajuste a URL em `frontend/app.py`

### IA não funciona
- Verifique `AI_PROVIDER` no `.env` (padrão: `fake`)
- Para IA real, configure a chave do provedor (ex.: `GROQ_API_KEY`)

### Mensagens não aparecem no histórico
- Verifique se `DATABASE_URL` está configurada no `.env`
- Certifique-se de usar o modo "Salvar & Notificar" para persistir
- Ao rodar dentro do compose, o host do Postgres é `postgres`, não `localhost`

## Exemplos de Mensagens

Dúvidas:
- "Como faço para cancelar minha conta?"
- "Qual o prazo de entrega?"

Reclamações:
- "O produto chegou com defeito, preciso devolver!"
- "Atendimento péssimo, nunca respondem!"

Solicitações:
- "Gostaria de saber mais sobre os planos"
- "Quero migrar do plano básico para premium"

Elogios:
- "Ótimo produto, recomendo a todos!"
- "Atendimento excelente, muito eficiente!"
