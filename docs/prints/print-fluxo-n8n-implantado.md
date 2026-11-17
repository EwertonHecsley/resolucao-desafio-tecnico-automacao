# Prints do Fluxo n8n — SPEC-07 (implantado e validado)

Este arquivo registra as **capturas/configurações** do fluxo n8n conforme
construído e ativado. Os dados abaixo foram extraídos das execuções reais no
n8n v2.48.4, disparadas por `POST /api/v1/messages` da API FastAPI.

> O n8n está sem interface gráfica desktop neste ambiente; os "prints" são
> representados pela configuração exata de cada node e pelos dados reais de
> entrada/saída de cada execução, extraídos do banco do n8n (`execution_data`).

---

## Print 1 — Visão geral do fluxo (canvas)

<img width="887" height="396" alt="image" src="https://github.com/user-attachments/assets/e5a114a0-2cbf-4572-8ed2-a96ad8902cbe" />


**Workflow:** `Classificador de Mensagens - IA + Automação`
**ID:** `dyck01CHYIj0g8ZT` · **Ativo:** `true` · **Nodes:** 7 · **Conexões:** 8

```
                              +------------------------+
                              |       Webhook          |
                              |  POST /classificador   |
                              | headerAuth (segredo)   |
                              +-----------+------------+
                                          |
                              +-----------v------------+
                              |     Edit Fields        |
                              | normaliza campos       |
                              +-----------+------------+
                                          |
                          +---------------v----------------+
                          |      Baixa Confiança?          |
                          |     confianca < 0.6            |
                          +---+------------------------+---+
                              | TRUE                   | FALSE
                    +---------v----------+   +----------v-----------+
                    |  Revisão Humana    |   | Roteador por Setor   |
                    |  setor = "geral"   |   | (Switch 5 saídas)    |
                    +---------+----------+   +----------+-----------+
                              |                       |
                              |           +-----------v------------+
                              |           |   Encaminhar Setor     |
                              |           | (Code: destino/mensagem)|
                              |           +-----------+------------+
                              |                       |
                              +-----------+-----------+
                                          |
                              +-----------v------------+
                              |  Respond to Webhook    |
                              | {status, setor}        |
                              +------------------------+
```

---

## Print 2 — Webhook (configuração)

| Parâmetro | Valor |
|---|---|
| Node | `Webhook` (`n8n-nodes-base.webhook`, v2) |
| HTTP Method | `POST` |
| Path | `classificador` |
| Authentication | `Header Auth` (`httpHeaderAuth`) |
| Header | `X-Webhook-Secret` |
| Response Mode | `Response Node` (via *Respond to Webhook*) |
| URL de produção | `http://localhost:5678/webhook/classificador` |

**Teste de autenticação (captura):**

```
$ curl -X POST http://localhost:5678/webhook/classificador -d '{}'
HTTP 403   # sem header

$ curl -X POST ... -H 'X-Webhook-Secret: <segredo>' -d '{...}'
HTTP 200   # com header correto
```

> O segredo **não** está no JSON exportado — nem o bloco `credentials` (removido
> antes do download). Ele vive apenas na credencial `Webhook Secret Auth`
> (tipo `httpHeaderAuth`) no n8n e em `N8N_WEBHOOK_SECRET` no `.env` da API.
> Auditoria: `grep -iE 'secret|password|token|credential'` no JSON não retorna
> nenhuma ocorrência.

---

## Print 3 — Edit Fields (configuração + saída real)

**Configuração:** modo *Manual*, 8 campos normalizados. O payload do Webhook
chega em `$json.body` (comportamento do n8n v2).

| Campo | Expressão | Tipo |
|---|---|---|
| `id` | `{{ $json.body.id }}` | string |
| `texto` | `{{ $json.body.entrada.texto }}` | string |
| `categoria` | `{{ $json.body.classificacao.categoria }}` | string |
| `setor` | `{{ $json.body.classificacao.setor }}` | string |
| `prioridade` | `{{ $json.body.classificacao.prioridade }}` | string |
| `sentimento` | `{{ $json.body.classificacao.sentimento }}` | string |
| `resumo` | `{{ $json.body.classificacao.resumo }}` | string |
| `confianca` | `{{ $json.body.classificacao.confianca }}` | number |

**Saída real (execução 13):**

```json
{
  "id": "f56318ff-f55d-435a-919b-d39f3472b59c",
  "texto": "Meu pedido ainda não chegou, o que aconteceu?",
  "categoria": "reclamacao",
  "setor": "logistica",
  "prioridade": "alta",
  "sentimento": "negativo",
  "resumo": "Cliente relata atraso na entrega do pedido.",
  "confianca": 0.92
}
```

---

## Print 4 — IF "Baixa Confiança?" (configuração)

| Parâmetro | Valor |
|---|---|
| Node | `Baixa Confiança?` (`n8n-nodes-base.if`, v2.2) |
| Condição | `{{ $json.confianca }}` ** menor que ** `0.6` |
| Operador | `number:lt` |
| Combinador | `and` |
| TRUE (saída 0) | → Revisão Humana |
| FALSE (saída 1) | → Roteador por Setor |

**Captura de teste:** com `confianca=0.92` o fluxo seguiu pelo ramo FALSE
(Roteador por Setor); com `confianca=0.45` seguiu pelo ramo TRUE (Revisão
Humana), confirmando o threshold da SPEC-07.

---

## Print 5 — Revisão Humana (configuração + saída real)

**Configuração:** `Edit Fields` que força `setor = "geral"`,
`destino = "geral@empresa.com"` e `status = "revisao_humana"`.

**Saída real (execução 15 — confiança 0.45):**

```json
{
  "id": "ea387c89-c7ee-49dd-8821-8d146450b83f",
  "categoria": "solicitacao",
  "setor": "geral",
  "destino": "geral@empresa.com",
  "status": "revisao_humana"
}
```

---

## Print 6 — Roteador por Setor / Switch (configuração)

| Parâmetro | Valor |
|---|---|
| Node | `Roteador por Setor` (`n8n-nodes-base.switch`, v3.2) |
| Mode | `rules` |
| Regras | `setor == suporte`, `financeiro`, `comercial`, `logistica`, `geral` |
| Output names | renomeadas com o nome do setor |
| Fallback | `extra` → `geral` (qualquer valor não previsto) |

**Captura — saídas testadas individualmente:**

| Setor enviado | Resposta do webhook |
|---|---|
| `suporte` | `{"status":"encaminhado","setor":"suporte"}` |
| `financeiro` | `{"status":"encaminhado","setor":"financeiro"}` |
| `comercial` | `{"status":"encaminhado","setor":"comercial"}` |
| `logistica` | `{"status":"encaminhado","setor":"logistica"}` |
| `geral` | `{"status":"encaminhado","setor":"geral"}` |

---

## Print 7 — Encaminhar Setor (configuração + saída real)

**Configuração:** node `Code` (JavaScript, sem credenciais externas) que monta
`destino = "<setor>@empresa.com"` e `mensagem = "[categoria] texto"`.

**Saída real (execução 13):**

```json
{
  "id": "f56318ff-f55d-435a-919b-d39f3472b59c",
  "categoria": "reclamacao",
  "setor": "logistica",
  "confianca": 0.92,
  "destino": "logistica@empresa.com",
  "mensagem": "[reclamacao] Meu pedido ainda não chegou, o que aconteceu?",
  "status": "encaminhado"
}
```

---

## Print 8 — Respond to Webhook (configuração + resposta real)

| Parâmetro | Valor |
|---|---|
| Node | `Respond to Webhook` (`n8n-nodes-base.respondToWebhook`, v1.1) |
| Respond With | JSON |
| Body | `{{ JSON.stringify({ status: 'encaminhado', setor: $json.setor }) }}` |

**Resposta HTTP real capturada:**

```
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

{"status":"encaminhado","setor":"logistica"}
```

---

## Print 9 — Aba *Executions* (execuções reais)

Execuções geradas por `POST /api/v1/messages` (API → n8n):

| ID | Workflow | Status | Iniciada em (UTC) |
|---|---|---|---|
| 15 | dyck01CHYIj0g8ZT | `success` | 2026-11-17 19:23:43.793 |
| 14 | dyck01CHYIj0g8ZT | `success` | 2026-11-17 19:23:43.506 |
| 13 | dyck01CHYIj0g8ZT | `success` | 2026-11-17 19:23:43.282 |

**Nodes percorridos na execução 13 (setor `logistica`, confiança `0.92`):**

```
Webhook → Edit Fields → Baixa Confiança? → Roteador por Setor
        → Encaminhar Setor → Respond to Webhook
```

**Nodes percorridos na execução 15 (setor `suporte`, confiança `0.45`):**

```
Webhook → Edit Fields → Baixa Confiança? → Revisão Humana → Respond to Webhook
```

---

## Print 10 — Resultado na API (notificado = true)

Saída real do `POST /api/v1/messages` da API correspondente à execução 13:

```
POST /api/v1/messages #1: HTTP 201
  id: f56318ff-f55d-435a-919b-d39f3472b59c
  setor: logistica
  confianca: 0.92
  notificado: True
```

O `notificado: true` confirma que a API recebeu o `200` do
*Respond to Webhook* e marcou a mensagem no PostgreSQL.

---

## Critérios da SPEC-07 atendidos

- [x] Webhook POST, path `classificador`, autenticação por `X-Webhook-Secret`, resposta via *Respond to Webhook*
- [x] *Edit Fields* normalizando `id`, `texto`, `categoria`, `setor`, `prioridade`, `sentimento`, `resumo`, `confianca`
- [x] IF `confianca < 0.6` → ramo de revisão humana (setor `geral`)
- [x] Switch por `setor`: `suporte`, `financeiro`, `comercial`, `logistica`, `geral`
- [x] Encaminhamento sem credenciais externas (node `Code` montando destino/mensagem)
- [x] *Respond to Webhook* com `{"status":"encaminhado","setor":"..."}`
- [x] Fluxo ativo e testado na URL de produção `/webhook/classificador`
- [x] Execuções bem-sucedidas na aba *Executions*, disparadas por `POST /messages` real da API
- [x] JSON exportado em `n8n/workflows/classificador.json` **sem tokens, senhas ou segredos**
