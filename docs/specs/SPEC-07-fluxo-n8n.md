## SPEC-07 — Fluxo no n8n *(feito manualmente por você)*

Esta etapa é visual. O agente só ajuda a revisar o JSON exportado. Tire os prints **enquanto constrói**.

**Nodes sugeridos**
1. **Webhook**: método POST, path `classificador`, autenticação por header (`X-Webhook-Secret`), resposta via *Respond to Webhook*.
2. **Edit Fields (Set)**: normaliza `id`, `texto`, `categoria`, `setor`, `prioridade`, `sentimento`, `resumo`, `confianca`.
3. **IF**: `confianca < 0.6` → ramo de revisão humana (setor `geral`).
4. **Switch** por `setor`: `suporte`, `financeiro`, `comercial`, `logistica`, `geral`.
5. Em cada saída, um node de encaminhamento (Telegram, Slack, e-mail, ou algo sem credenciais externas, como um **Edit Fields** que monta a mensagem do setor ou um **HTTP Request** para um endpoint de teste).
6. **Respond to Webhook** com `{"status":"encaminhado","setor":"..."}`.

**Passos**
- Construir usando "Listen for test event" e tirar os prints de cada node (configuração, entrada e saída).
- Ativar o fluxo (toggle *Active*) e testar a URL de produção `/webhook/classificador`.
- Exportar o JSON (menu do workflow → Download) para `n8n/workflows/classificador.json`, **sem credenciais**.

**Aceite**
- Execução bem-sucedida visível na aba *Executions*, disparada por um `POST /messages` real da API.
- JSON exportado revisado: sem tokens, senhas ou segredos.