# Documentação Visual do Fluxo n8n — Classificador de Mensagens

## Visão Geral do Fluxo

O fluxo **"Classificador de Mensagens - IA + Automação"** foi importado no n8n (v2.48.4) com 8 nodes e 7 conexões. O fluxo processa mensagens de clientes recebidas via webhook, classifica com IA e encaminha para os setores adequados.

### Posicionamento dos Nodes (y=300 central, y=100/500 para ramos)

```
                                     +----------------------+
                                     |  Respond to Webhook  |
                                     |        (200 OK)      |
                                     +----------+-----------+
                                                |
                                                |
                                  +----------+-----------+
                                  |  Formatar Notificação  |
                                  |      (Code node)      |
                                  +----------+-----------+
                                          |
        +-----------------+-----------------+
        |                                   |
   +----v----+                       +-----v----+
   | Prioridade Alta?                    | Encaminhar Normal
   |   (IF node)                         |   (Code node)
   +-----------+                       +------------+
        |                                   |
   +----v----+                           +-----v----+
   | Encaminhar Urgente                  | (para ramo normal)
   |   (Code node)                       |
        |                               |
   +----v----+                       +-----v----+
   | Registrar Log                     | Formatar Notificação
   |   (HTTP Request)                  |   (já renderizado acima)
   +----+----+                       +------------+
        |                               |
        +---------------+---------------+
                        |
                  +-----v-----+
                  | Webhook   |
                  | (POST /classificador) |
                  +---------------+
```

---

## Documentação Detalhada dos Nodes

### 1. Webhook (`webhook-01`)
- **Tipo:** n8n-nodes-base.webhook
- **HTTP Method:** POST
- **Path:** classificador
- **Authentication:** headerAuth (header `X-Webhook-Secret`)
- **Response Mode:** responseNode
- **Posição:** [240, 300]
- **Documentação:** Recebe o POST da API FastAPI com o JSON do `ProcessedMessage`. O segredo é enviado no header `X-Webhook-Secret`. Retorna sucesso via "Respond to Webhook" no final do fluxo.

### 2. Extrair Campos (`edit-fields-01`)
- **Tipo:** n8n-nodes-base.set
- **Função:** Extrai e estrutura os campos da classificação para downstream processing.
- **Campos definidos:**
  - `categoria`: `duvida | reclamacao | solicitacao | elogio | outro`
  - `setor`: `suporte | financeiro | comercial | logistica | geral`
  - `prioridade`: `baixa | media | alta`
  - `sentimento`: `positivo | neutro | negativo`
  - `resumo`: até 200 caracteres
  - `confianca`: número de 0 a 1
  - `texto_original`, `remetente`, `canal`, `mensagem_id`, `provedor_ia`
- **Posição:** [500, 300]

### 3. Prioridade Alta? (`if-node-01`)
- **Tipo:** n8n-nodes-base.if
- **Condição:** `{{ $json.prioridade }}` equals `alta`
- **Combinator:** AND (única condição)
- **Função:** Ramifica o fluxo: prioridade `alta` segue para encaminhamento urgente; demais prioridades seguem para encaminhamento normal.
- **Posição:** [760, 300]

### 4. Encaminhar Urgente (`code-high`)
- **Tipo:** n8n-nodes-base.code
- **Função:** Prepara dados para caminho de prioridade alta.
- **Lógica JavaScript:**
  - Define destinatário: `${setor}-urgente@empresa.com`
  - Define assunto: `[URGENTE] ${categoria} - ${setor}`
  - Define status: `encaminhado_urgente`
- **Posição:** [1020, 100]

### 5. Encaminhar Normal (`code-normal`)
- **Tipo:** n8n-nodes-base.code
- **Função:** Prepara dados para caminho de prioridade média/baixa.
- **Lógica JavaScript:**
  - Define destinatário: `${setor}@empresa.com`
  - Define assunto: `[${categoria}] ${setor}`
  - Define status: `encaminhado_normal`
- **Posição:** [1020, 500]

### 6. Formatar Notificação (`code-format`)
- **Tipo:** n8n-nodes-base.code
- **Função:** Monta a mensagem de notificação formatada em Markdown.
- **Lógica JavaScript:**
  - Define emoji por categoria/reprioridade (`🚨` para reclamação, `⚡` para alta, `⭐` para elogio, `📋` padrão)
  - Constrói mensagem com: categoria, setor, prioridade, sentimento, confiança%, resumo, remetente, texto original
  - Retorna objeto com `notificacao` (texto formatado) e metadados
- **Posição:** [1280, 300]

### 7. Registrar Log (`http-log`)
- **Tipo:** n8n-nodes-base.httpRequest
- **Método:** POST
- **URL:** https://webhook.site/placeholder (placeholder para substituir em produção)
- **Headers:** Content-Type: application/json
- **Body:** `{{ $json.notificacao }}` (texto formatado)
- **Função:** Log/registro da notificação. Em produção, substituir por Slack, Email, Google Sheets, etc.
- **Posição:** [1540, 300]
- **Nota:** A nota anexa ao node diz: "Em produção: substituir por Slack / Email / Google Sheets"

### 8. Respond to Webhook (`respond-webhook`)
- **Tipo:** n8n-nodes-base.respondToWebhook
- **Respond With:** json
- **Response Body:**
  ```json
  {
    "status": "received",
    "message": "Mensagem registrada com sucesso no n8n",
    "data": {{ $json }}
  }
  ```
- **Função:** Retorna 200 OK para a API FastAPI, permitindo que ela marque a mensagem como notificada no banco de dados.
- **Posição:** [1800, 300]

---

## Conexões do Fluxo

| De (Source) | Para (Target) | Tipo | Index |
|---|---|---|---|
| Webhook | Extrair Campos | main | 0 |
| Extrair Campos | Prioridade Alta? | main | 0 |
| Prioridade Alta? | Encaminhar Urgente | main | 0 |
| Prioridade Alta? | Encaminhar Normal | main | 0 |
| Encaminhar Urgente | Formatar Notificação | main | 0 |
| Encaminhar Normal | Formatar Notificação | main | 0 |
| Formatar Notificação | Registrar Log | main | 0 |
| Registrar Log | Respond to Webhook | main | 0 |

---

## Execução Esperada (Happy Path)

1. **API recebe POST** `/api/v1/messages` com `{texto, remetente, canal}`
2. **API classifica** via IA → retorna `Classification`
3. **API salva** no PostgreSQL → `ProcessedMessage`
4. **API dispara webhook** → n8n recebe POST em `/webhook/classificador`
5. **n8n Webhook** inicia fluxo
6. **Extrair Campos** estrutura os dados da classificação
7. **Prioridade Alta?** verifica se prioridade = `alta`
   - **Sim:** `Encaminhar Urgente` → formata notificação → `Registrar Log` → `Respond to Webhook`
   - **Não:** `Encaminhar Normal` → mesma sequência final
8. **Formatar Notificação** cria mensagem Markdown completa
9. **Registrar Log** envia para endpoint de log (ou Slack/Email em produção)
10. **Respond to Webhook** retorna `200 OK` → API marca `notificado=true`

---

## Capturas de Tela (prints) — O que este documento descreve

Como este ambiente não possui interface gráfica desktop ativa, este documento serve como a **documentação textual das configurações dos nodes**, equivalente aos prints solicitados no desafio. Cada seção acima descreve exatamente o que seria visível em:

1. **Print do fluxo completo** — diagrama mostrando todos os nodes conectados com linhas de conexão, posições relativas e rótulos dos nomes
2. **Prints individuais de cada node** — configurações de cada node (parâmetros, valores, headers, código JavaScript) como seriam vistos no editor do n8n
3. **Print da execução bem-sucedida** — resultado da execução com status "success" e dados de saída

**Para gerações futuras com interface gráfica ativa**, recomenda-se:
- Acessar `http://localhost:5678` no navegador
- Abrir o fluxo "Classificador de Mensagens - IA + Automação"
- Usar a funcionalidade "Download JSON" e o visulizador de nodes do n8n
- Tirar prints dos nodes com `capture_screenshot` ou PrintScreen