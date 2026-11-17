## SPEC-03 — Adapters de IA, factory e fallback

**Objetivo:** poder trocar de provedor ou de chave de IA só mudando o `.env`.

**Requisitos**

1. Configuração em `app/config.py` (Settings), com estas variáveis:
   `AI_PROVIDER` (`fake|gemini|groq|openai`, padrão `fake`), `AI_FALLBACK_PROVIDERS` (lista separada por vírgula, vazia por padrão), `AI_TIMEOUT_SECONDS` (padrão 20), `GEMINI_API_KEY`, `GEMINI_MODEL`, `GROQ_API_KEY`, `GROQ_MODEL`, `OPENAI_API_KEY`, `OPENAI_MODEL`. Atualize o `.env.example` (sem valores reais).

2. Adapters em `app/adapters/ai/`, cada um implementando `AIProvider` (`name` e `generate_json`), usando `httpx.AsyncClient` com timeout:
   - `gemini.py`: API REST do Gemini (`generateContent`), chave enviada em header, pedindo resposta em JSON (`responseMimeType: application/json`), `system_prompt` como instrução de sistema.
   - `groq.py`: endpoint compatível com OpenAI (`/openai/v1/chat/completions`), `response_format: {"type": "json_object"}`, `temperature` baixa (0 a 0.2).
   - `openai.py`: mesmo formato do Groq, apontando para a API da OpenAI.
   - Implemente pelo menos `gemini` e `groq`; `openai` é opcional.
   - Os nomes de modelo vêm do `.env`; use valores sugeridos no `.env.example` e confira no site do provedor qual modelo está vigente.
   - Mapeamento de erros: timeout, falha de rede, HTTP 401/403/429/5xx → `AIProviderError` com mensagem curta, **sem vazar a chave** em logs ou mensagens.

3. `app/adapters/ai/factory.py`: `build_ai_provider(settings) -> AIProvider`.
   - Lê `AI_PROVIDER`; se houver `AI_FALLBACK_PROVIDERS`, devolve um `FallbackAIProvider` com a ordem `[AI_PROVIDER, *fallbacks]`.
   - Provedor desconhecido, ou chave ausente de um provedor real → erro claro na inicialização.

4. `app/adapters/ai/fallback.py`: `FallbackAIProvider(providers: list[AIProvider])`.
   - Tenta cada provedor em ordem; se um levantar `AIProviderError`, tenta o próximo; se todos falharem, levanta `AIProviderError` agregando os motivos.
   - `name` reflete o provedor que respondeu (útil para gravar no banco).

**Aceite**
- Com `AI_PROVIDER=fake` tudo funciona sem chave.
- Testes (sem rede, usando `httpx.MockTransport`) cobrem: sucesso de cada adapter com payload falso; erro 401/429/timeout → `AIProviderError`.
- Testes do fallback: 1º falha e 2º responde; todos falham → erro agregado.
- Testes da factory: provedor válido, desconhecido, chave ausente, fallback montado.
- Trocar `AI_PROVIDER` no `.env` e reiniciar muda o provedor sem alterar código.
- Nenhum import de `httpx`/SDK de IA fora de `app/adapters/ai/`.

**Fora de escopo:** rotas, banco, n8n.
