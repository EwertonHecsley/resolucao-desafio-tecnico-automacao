# Frontend Sandbox

Interface web para testar o classificador de mensagens com IA.

## Funcionalidades

- 🧪 **Teste Rápido**: Classifica mensagens sem salvar no banco
- ⚡ **Fluxo Completo**: Salva no banco e notifica o n8n
- 📊 **Histórico**: Visualização de todas as mensagens processadas
- 🔄 **Status do n8n**: Visualização em tempo real do webhook

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
# 1. Instalar dependências
pip install -r frontend/requirements.txt

# 2. Configurar API key (opcional)
# Adicione ao .env se quiser autenticação
# API_KEY=seu-token-aqui

# 3. Rodar
streamlit run frontend/app.py
```

## Configuração

O frontend usa a seguinte configuração padrão:

- **API Base URL**: `http://api:8000/api/v1`
- **API Key**: Pelo `.env` ou `kodie-sandbox-token` (padrão)
- **Modo de IA**: Fake (simulação) por padrão

## Páginas

### 🏠 Início
- Dashboard com estatísticas
- Instruções de como testar
- Exemplos de mensagens

### 🧪 Classificar
- Campo de input para mensagens
- Opções: IA Real vs Fake
- Modos: Classificar (Rápido) vs Salvar & Notificar
- Visualização imediata dos resultados

### 📊 Histórico
- Lista de mensagens salvas
- Filtros por categoria
- Detalhes completos de cada mensagem

## Segurança

- A API key pode ser configurada no `.env`
- Se vazia, a autenticação é desativada (desenvolvimento)
- Em produção, sempre use uma API key forte

## Troubleshooting

### Frontend não conecta à API
- Verifique se o serviço `api` está rodando: `docker compose ps`
- Confirme que a API responde: `curl http://localhost:8000/health`

### IA não funciona
- Verifique `AI_PROVIDER=fake` no `.env`
- Para usar IA real, configure uma chave no `.env`

### Mensagens não aparecem no histórico
- Verifique se `DATABASE_URL` está configurada no `.env`
- Certifique-se de usar o modo "Salvar & Notificar" para persistir

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
