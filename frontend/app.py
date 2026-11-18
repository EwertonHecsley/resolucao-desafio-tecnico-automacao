
import requests
import streamlit as st

# Configurações da API
API_BASE_URL = "http://api:8000/api/v1"

@st.cache_resource
def get_api_key() -> str:
    """Retorna a API key do sandbox (token de autenticação da API).

    Lê SANDBOX_API_KEY (não API_KEY): o Streamlit promove chaves de
    secrets.toml para os.environ, e API_KEY é a setting de autenticação
    do backend (SPEC-06) — colisão que exigiria X-API-Key nas rotas.
    """
    return str(st.secrets.get("SANDBOX_API_KEY", ""))

def health_check():
    """Verifica se a API está saudável."""
    try:
        # Endpoint /health está no nível raiz da API, não sob /api/v1
        response = requests.get("http://api:8000/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def fetch_recent_messages(limit=10):
    """Busca as mensagens mais recentes do histórico."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/messages",
            params={"limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Erro ao buscar histórico: {str(e)}")
        return []

def classify_text(texto):
    """Classifica com IA real, sem salvar nem notificar."""
    try:
        payload = {
            "texto": texto,
            "remetente": "demo@kodie.com",
            "canal": "sandbox"
        }

        headers = {}
        api_key = get_api_key()
        if api_key:
            headers["X-API-Key"] = api_key

        response = requests.post(
            f"{API_BASE_URL}/classify",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("API Key inválida. Configure a API_KEY no .env")
            return None
        else:
            st.error(f"Erro: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro na classificação: {str(e)}")
        return None

def save_and_notify(texto):
    """Salva a mensagem e notifica o n8n (fluxo completo)."""
    try:
        payload = {
            "texto": texto,
            "remetente": "demo@kodie.com",
            "canal": "sandbox"
        }

        headers = {}
        api_key = get_api_key()
        if api_key:
            headers["X-API-Key"] = api_key

        response = requests.post(
            f"{API_BASE_URL}/messages",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 201:
            return response.json()
        elif response.status_code == 401:
            st.error("API Key inválida. Configure a API_KEY no .env")
            return None
        else:
            st.error(f"Erro: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro ao salvar: {str(e)}")
        return None

def get_ai_config():
    """Busca metadados públicos do provedor de IA no backend."""
    try:
        response = requests.get(f"{API_BASE_URL}/config/ai", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"provider": "unknown", "is_real": False, "key_configured": False}
    except Exception:
        return {"provider": "unknown", "is_real": False, "key_configured": False}


def get_ai_status():
    """Verifica o status do provedor de IA."""
    try:
        response = requests.get(f"{API_BASE_URL}/health/ai", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "provider": data.get("provider", "unknown"),
                "responded": data.get("responded", False),
                "error": data.get("error")
            }
    except Exception as e:
        return {"provider": "unknown", "responded": False, "error": str(e)}
    return {"provider": "unknown", "responded": False}

def main():
    st.set_page_config(
        page_title="Kodie Sandbox - IA Classifier",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🎯 Kodie Sandbox - Classificador com IA")
    st.markdown("""
    Ambiente de demonstração para testar o classificador de mensagens com IA.
    O fluxo completo inclui: classificação → persistência → notificação n8n.
    """)

    # Verifica saúde da API
    api_healthy = health_check()

    if not api_healthy:
        st.error("❌ API não está respondendo. Verifique se o serviço está rodando.")
        st.stop()

    # Exige IA real configurada no backend — sem chave, sandbox não funciona
    ai_config = get_ai_config()
    if not ai_config.get("is_real") or not ai_config.get("key_configured"):
        st.error(
            "🚫 **Sandbox indisponível: IA real não configurada.**\n\n"
            "Este ambiente exige um provedor de IA real com chave válida. "
            "Configure `AI_PROVIDER` (gemini, groq ou openai) e a chave "
            "correspondente no `.env` da API, reinicie o backend e recarregue "
            "esta página.\n\n"
            f"Provedor atual: `{ai_config.get('provider', 'unknown')}` — "
            "o modo `fake` serve apenas para testes automatizados."
        )
        st.stop()

    ai_status = get_ai_status()
    if not ai_status.get("responded"):
        st.error(
            f"🚫 **O provedor `{ai_config['provider']}` não respondeu.** "
            f"Verifique a chave no `.env` da API. Detalhe: {ai_status.get('error')}"
        )
        st.stop()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        st.info(
            f"🤖 IA real ativa: **{ai_config['provider']}**"
            + (f" (`{ai_config['model']}`)" if ai_config.get("model") else "")
        )

        st.divider()

        st.header("📋 Menu")
        page = st.radio(
            "Navegação",
            ["🏠 Início", "🧪 Classificar", "📊 Histórico"],
            key="page",
            label_visibility="collapsed"
        )

    # Renderiza os elementos da UI
    if page == "🏠 Início":
        render_home()
    elif page == "🧪 Classificar":
        render_classifier()
    elif page == "📊 Histórico":
        render_history()

def render_home():
    """Página inicial: visão geral do sandbox (sem executar testes)."""
    st.header("📖 Como funciona o Sandbox")

    st.markdown("""
    Este é um ambiente controlado para testar a classificação de mensagens
    de clientes com **IA real**. Toda requisição é enviada à API FastAPI,
    validada com Pydantic e processada pelo fluxo de automação.
    """)

    st.subheader("Fluxo de ponta a ponta")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**1️⃣ Escreva**")
        st.caption("Na aba **🧪 Classificar**, informe a mensagem do cliente.")

    with col2:
        st.markdown("**2️⃣ IA classifica**")
        st.caption(
            "O prompt estruturado gera um JSON com categoria, setor, "
            "prioridade, sentimento, resumo e confiança."
        )

    with col3:
        st.markdown("**3️⃣ Escolha o destino**")
        st.caption(
            "**Resposta rápida** devolve só a classificação. "
            "**Salvar + notificar** persiste no Postgres e dispara o n8n."
        )

    with col4:
        st.markdown("**4️⃣ Consulte**")
        st.caption(
            "Na aba **📊 Histórico** você vê as mensagens salvas e o status "
            "da notificação."
        )

    st.divider()
    st.info(
        "👉 **Comece por aqui:** abra **🧪 Classificar** no menu lateral, "
        "escolha o modo de teste e envie uma mensagem de exemplo."
    )

    st.subheader("Exemplo ilustrativo de classificação")
    example = {
        "categoria": "reclamacao",
        "setor": "logistica",
        "prioridade": "alta",
        "sentimento": "negativo",
        "resumo": "Cliente relata atraso na entrega do pedido.",
        "confianca": 0.92,
    }
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Categoria", example["categoria"].title())
    with col2:
        st.metric("Setor", example["setor"].title())
    with col3:
        st.metric("Prioridade", example["prioridade"].upper())

    st.markdown(
        f"**Resumo**: {example['resumo']} "
        f"(Confiança: {example['confianca']:.2f})"
    )

    with st.expander("Ver exemplos de mensagens para testar"):
        exemplos = [
            "Meu pedido ainda não chegou, o que aconteceu?",
            "Gostaria de saber o status da minha fatura de 123456",
            "O produto está muito ruim, devolvo agora!",
            "Obrigado pelo atendimento, ótimo produto!",
        ]
        for ex in exemplos:
            if st.button(ex, key=f"ex_{hash(ex)}"):
                st.session_state.pending_text = ex
                st.session_state.page = "🧪 Classificar"
                st.rerun()


def render_classifier():
    """Página de classificação: IA real sempre ativa, com 2 modos de teste."""
    st.header("🧪 Classificar Mensagem")
    st.caption("✅ IA real sempre ativa — a chave está configurada no backend.")

    pending = st.session_state.pop("pending_text", "")
    texto = st.text_area(
        "Mensagem:",
        value=pending,
        height=180,
        placeholder="Digite aqui a mensagem do cliente...",
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        modo = st.radio(
            "Modo de teste",
            ["Resposta rápida (sem salvar)", "Salvar + notificar n8n"],
            horizontal=True,
            key="modo_teste",
        )
    with col2:
        submit_btn = st.button("🎯 Processar", use_container_width=True, type="primary")

    if submit_btn and not texto.strip():
        st.warning("Digite uma mensagem antes de processar.")
        return

    if submit_btn:
        with st.spinner("Classificando com IA real..."):
            if modo == "Salvar + notificar n8n":
                st.session_state.classificacao = None
                result = save_and_notify(texto)
                if result:
                    st.session_state.processed_message = result
                    st.success("✅ Mensagem salva e notificada!")
            else:
                st.session_state.processed_message = None
                result = classify_text(texto)
                if result:
                    st.session_state.classificacao = result
                    st.success("✅ Classificação concluída!")

    st.divider()

    resultado = st.session_state.get("classificacao") or st.session_state.get("processed_message")
    if not resultado:
        st.info("O resultado da classificação aparecerá aqui.")
        return

    classificacao = resultado.get("classificacao", resultado)
    col1, col2, col3 = st.columns(3)
    with col1:
        prioridade = classificacao["prioridade"]
        delta = {"alta": "🔴 Alta", "media": "🟡 Média"}.get(prioridade, "🟢 Baixa")
        st.metric("Prioridade", prioridade.upper(), delta=delta)
    with col2:
        st.metric("Categoria", classificacao["categoria"].title())
    with col3:
        st.metric("Setor", classificacao["setor"].title())

    st.metric("Sentimento", classificacao["sentimento"].title())
    st.markdown(
        f"**Resumo**: {classificacao['resumo']}  \n"
        f"**Confiança**: {classificacao['confianca']:.2f}"
    )
    if classificacao["confianca"] < 0.6:
        st.warning("⚠️ Confiança baixa — provável necessidade de revisão humana.")
    else:
        st.success("✅ Confiança alta — classificação confiável.")

    if "processed_message" in st.session_state and st.session_state.processed_message:
        pm = st.session_state.processed_message
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Provedor", pm["provedor"])
        with col2:
            st.metric(
                "Status n8n",
                "✅ Notificado" if pm["notificado"] else "❌ Não notificado",
            )
        st.caption(f"ID: `{pm.get('id', '—')}` · Criado em: {pm.get('criado_em', '—')}")

    if st.button("🔄 Limpar resultado"):
        st.session_state.classificacao = None
        st.session_state.processed_message = None
        st.rerun()


def render_history():
    """Página de histórico de mensagens."""
    st.header("📊 Histórico de Mensagens")

    col1, col2 = st.columns([2, 1])

    with col1:
        limit = st.number_input(
            "Limite de mensagens:",
            min_value=1,
            max_value=100,
            value=50,
            step=1
        )

        refresh_btn = st.button("🔄 Atualizar", use_container_width=True)

    with col2:
        st.info("""
        **Info**: Lista as mensagens salvas no banco.
        A última mensagem mostrada já foi processada e notificada.
        """)

    # Carrega mensagens
    if refresh_btn or "messages" not in st.session_state:
        with st.spinner("Carregando histórico..."):
            messages = fetch_recent_messages(limit)
            st.session_state.messages = messages

    messages = st.session_state.messages

    if not messages:
        st.warning("📭 Nenhuma mensagem encontrada no histórico.")
        return

    # Tabs para categorias
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Todas",
        "Dúvidas",
        "Reclamações",
        "Solicitações",
        "Elogios"
    ])

    with tab1:
        render_messages_table(messages)

    with tab2:
        render_filtered_messages(messages, "duvida")

    with tab3:
        render_filtered_messages(messages, "reclamacao")

    with tab4:
        render_filtered_messages(messages, "solicitacao")

    with tab5:
        render_filtered_messages(messages, "elogio")

def render_messages_table(messages):
    """Renderiza tabela completa de mensagens."""
    for msg in messages:
        with st.expander(
            f"📋 {msg['entrada']['texto'][:80]}...",
            expanded=True
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Categoria",
                    msg["classificacao"]["categoria"].title(),
                    delta=msg["classificacao"]["setor"].title()
                )

            with col2:
                prioridade = msg["classificacao"]["prioridade"]
                delta = ""
                if prioridade == "alta":
                    delta = "🔴 Alta"
                elif prioridade == "media":
                    delta = "🟡 Média"
                else:
                    delta = "🟢 Baixa"

                st.metric("Prioridade", prioridade.upper(), delta=delta)

            with col3:
                if msg["notificado"]:
                    st.metric("n8n", "✅ Notificado", delta_color="inverse")
                else:
                    st.metric("n8n", "❌ Não notificado", delta_color="inverse")

            st.markdown(f"""
            **Sentimento**: {msg['classificacao']['sentimento'].title()}
            **Confiança**: {msg['classificacao']['confianca']:.2f}
            **Resumo**: {msg['classificacao']['resumo']}
            **Provedor**: {msg['provedor']}
            **Criado em**: {msg['criado_em']}
            """)

def render_filtered_messages(messages, categoria):
    """Renderiza mensagens filtradas por categoria."""
    filtered = [msg for msg in messages if msg["classificacao"]["categoria"] == categoria]

    if not filtered:
        st.info(f"📭 Nenhuma mensagem de **{categoria.title()}** encontrada.")
        return

    for msg in filtered:
        with st.expander(
            f"📋 {msg['entrada']['texto'][:80]}...",
            expanded=True
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Categoria", categoria.title(), delta=msg["classificacao"]["setor"].title())

            with col2:
                prioridade = msg["classificacao"]["prioridade"]
                delta = ""
                if prioridade == "alta":
                    delta = "🔴 Alta"
                elif prioridade == "media":
                    delta = "🟡 Média"
                else:
                    delta = "🟢 Baixa"

                st.metric("Prioridade", prioridade.upper(), delta=delta)

            with col3:
                if msg["notificado"]:
                    st.metric("n8n", "✅ Notificado", delta_color="inverse")
                else:
                    st.metric("n8n", "❌ Não notificado", delta_color="inverse")

            st.markdown(f"""
            **Sentimento**: {msg['classificacao']['sentimento'].title()}
            **Confiança**: {msg['classificacao']['confianca']:.2f}
            **Resumo**: {msg['classificacao']['resumo']}
            """)

if __name__ == "__main__":
    main()
