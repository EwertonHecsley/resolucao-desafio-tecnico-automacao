# Documentação dos Nodes do Fluxo n8n

## Visão Geral
Fluxo: **Classificador de Mensagens - IA + Automação**
Nodes: 8 | Conexões: 7 | Pós-importado em n8n v2.48.4

---

### Node 1: Webhook
- **ID:** webhook-01
- **Tipo:** Webhook
- **Método:** POST
- **Path:** classificador
- **Auth:** headerAuth (X-Webhook-Secret)
- **Posição:** x=240, y=300
- **Função:** Recebe mensagem classificada da API FastAPI

### Node 2: Extrair Campos
- **ID:** edit-fields-01
- **Tipo:** Set (Edit Fields)
- **Função:** Estrutura campos da classificação (categoria, setor, prioridade, sentimento, resumo, confianca, texto_original, remetente, canal, mensagem_id, provedor_ia)
- **Posição:** x=500, y=300

### Node 3: Prioridade Alta?
- **ID:** if-node-01
- **Tipo:** IF
- **Condição:** prioridade == "alta"
- **Ramos:** alto → encaminhar urgente | não-alto → encaminhar normal
- **Posição:** x=760, y=300

### Node 4: Encaminhar Urgente
- **ID:** code-high
- **Tipo:** Code
- **Lógica:** Define destinatário urgenete (setor-urgente@empresa.com), assunto [URGENTE], status encaminhado_urgente
- **Posição:** x=1020, y=100

### Node 5: Encaminhar Normal
- **ID:** code-normal
- **Tipo:** Code
- **Lógica:** Define destinatário normal (setor@empresa.com), assunto [categoria], status encaminhado_normal
- **Posição:** x=1020, y=500

### Node 6: Formatar Notificação
- **ID:** code-format
- **Tipo:** Code
- **Lógica:** Monta mensagem Markdown com emoji por categoria, campos: categoria, setor, prioridade, sentimento, confianca%, resumo, remetente, texto original
- **Posição:** x=1280, y=300

### Node 7: Registrar Log
- **ID:** http-log
- **Tipo:** HTTP Request
- **Método:** POST
- **URL:** webhook.site/placeholder (substituir em produção)
- **Headers:** Content-Type: application/json
- **Body:** {{ $json.notificacao }}
- **Nota:** Em produção: Slack / Email / Google Sheets
- **Posição:** x=1540, y=300

### Node 8: Respond to Webhook
- **ID:** respond-webhook
- **Tipo:** Respond to Webhook
- **Responder com:** JSON
- **Body:** {"status":"received","message":"Mensagem registrada com sucesso no n8n","data":{{$json}}}
- **Função:** Retorna 200 OK para API marcar notificação
- **Posição:** x=1800, y=300

---

## Estrutura de Conexões

Webhook → Extrair Campos → Prioridade Alta?
      ├─> Encaminhar Urgente → Formatar Notificação → Registrar Log → Respond to Webhook
      └─> Encaminhar Normal → Formatar Notificação → Registrar Log → Respond to Webhook