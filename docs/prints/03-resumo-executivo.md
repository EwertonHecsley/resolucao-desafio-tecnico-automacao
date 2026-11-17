# Resumo Executivo do Fluxo n8n

## Contexto
Desafio Técnico Kodie — IA e Automação (Caso 4.1: Classificação de Mensagens)
Objetivo: automatizar triagem e encaminhamento de mensagens de clientes usando IA + n8n.

## Fluxo Implementado

1. **Recebimento** — API FastAPI POST /messages classifica mensagem com IA, persiste no PostgreSQL e dispara webhook para n8n.

2. **Processo no n8n:**
   - Webhook recebe payload ProcessedMessage
   - Set node extrai campos estruturados (categoria, setor, prioridade, sentimento, resumo, confianca)
   - IF node ramifica por prioridade:
     - **Alta:** encaminhamento urgente (setor-urgente@empresa.com)
     - **Normal/Média:** encaminhamento padrão (setor@empresa.com)
   - Code node formata notificação em Markdown
   - HTTP Request registra/logga a notificação
   - Respond to Webhook retorna sucesso à API

3. **Saída:** Mensagem notificada, salva no banco com `notificado=true`, resposta 201 para o cliente.

## Tecnologias Envolvidas

- **Backend:** FastAPI (Python), PostgreSQL, n8n, API/ modelo de IA (configurável via factory)
- **Automação:** n8n (workflow JSON exportável)
- **Integração:** Webhook POST/JSON entre API e n8n
- **Documentação:** prints/textos em docs/prints/

## Arquivos Entregues

- `n8n/workflows/classificador.json` — JSON exportável do fluxo n8n
- `docs/prints/01-visualizacao-fluxo-completo.md` — documentação visual textual
- `docs/prints/02-documentacao-nodes.md` — configurações detalhadas por node
- `docs/prints/03-resumo-executivo.md` — este arquivo

## Próximos Passos (Opcional)

- Substituir URL do HTTP Request por integração real (Slack webhook, Email via SendGrid, Google Sheets)
- Adicionar nó de retry/erro handling
- Configurar variáveis de ambiente (N8N_WEBHOOK_URL, N8N_WEBHOOK_SECRET)
- Testes de execução com dados reais

---
*Fluxo importado e documentado via Hermes Agent. JSON válido verificado através de n8n import:workflow.*