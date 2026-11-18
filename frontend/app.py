
import requests
import streamlit as st

# Configurações da API
API_BASE_URL = "http://api:8000/api/v1"

# Configurações de autenticação
SANDBOX_API_KEY = "kodie-sandbox-token"

@st.cache_resource
def get_api_key():
    """Retorna a API key do sandbox.

    Lê SANDBOX_API_KEY (não API_KEY): o Streamlit promove chaves de
    secrets.toml para os.environ, e API_KEY é a setting de autenticação
    do backend (SPEC-06) — colisão que exigiria X-API-Key nas rotas.
    """
    return st.secrets.get("SANDBOX_API_KEY", "") or SANDBOX_API_KEY

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

def classify_text(texto, use_real_ai=False):
    """Classifica um texto."""
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

        # Se usar IA real, chama /api/v1/classify (salva e notifica)
        # Se usar modo sandbox, chama /api/v1/classify (apenas classifica)
        if use_real_ai:
            # Fluxo completo com persistência e notificação
            endpoint = "/messages"
            timeout = 30
        else:
            # Apenas classificação (sem persistência)
            endpoint = "/classify"
            timeout = 5

        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            headers=headers,
            timeout=timeout
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

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        api_key = st.secrets.get("SANDBOX_API_KEY", "")
        if api_key:
            st.info(f"API Key: {api_key[:20]}...")
        else:
            st.info("API Key não configurada")

        st.divider()

        st.header("📋 Menu")
        page = st.radio(
            "Navegação",
            ["🏠 Início", "🧪 Classificar", "📊 Histórico"],
            label_visibility="collapsed"
        )

    # Status do provedor de IA (endpoint /health/ai)
    st.header("🤖 Status da IA")
    n8n_status = get_ai_status()
    if n8n_status["responded"]:
        status_color = "🟢"
        status_text = "Operacional"
    else:
        status_color = "🔴"
        status_text = "Indisponível"

    st.markdown(f"""
    **Provedor**: {status_color} {status_text} ({n8n_status['provider']})
    """)

    # Renderiza os elementos da UI
    if page == "🏠 Início":
        render_home()
    elif page == "🧪 Classificar":
        render_classifier()
    elif page == "📊 Histórico":
        render_history()

def render_home():
    """Página inicial com resumo."""
    st.header("🏠 Dashboard")

    # Status da IA consultado uma vez e reutilizado nos cards
    ai_status = get_ai_status()
    provider = ai_status["provider"]
    delta_ia = "Operacional" if ai_status["responded"] else "Sem resposta"

    # Cards de estatísticas
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Provedor de IA", provider, delta=delta_ia)

    with col2:
        try:
            response = requests.get(f"{API_BASE_URL}/messages", params={"limit": 1}, timeout=5)
            if response.status_code == 200:
                messages = response.json()
                st.metric("Mensagens Processadas", len(messages), delta="Total")
            else:
                st.metric("Mensagens Processadas", "0", delta="Sem dados")
        except Exception:
            st.metric("Mensagens Processadas", "Erro", delta="Indisponível")

    st.divider()

    st.header("📝 Como Testar")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧪 Opção 1: Teste Rápido")
        st.markdown("""
        1. Digite uma mensagem no campo de classificação
        2. Clique em **"Classificar"** (sem salvar no banco)
        3. Veja o resultado imediatamente

        **Vantagem**: Resultado instantâneo sem persistência.
        """)

        with st.expander("Exemplos de mensagens"):
            examples = [
                "Meu pedido ainda não chegou, o que aconteceu?",
                "Gostaria de saber o status da minha fatura de 123456",
                "O produto está muito ruim, devolvo agora!",
                "Obrigado pelo atendimento, ótimo produto!"
            ]
            for ex in examples:
                if st.button(ex, key=f"ex_1_{hash(ex)}"):
                    st.session_state.current_text = ex
                    st.session_state.page = "🧪 Classificar"

    with col2:
        st.subheader("⚡ Opção 2: Fluxo Completo")
        st.markdown("""
        1. Digite uma mensagem
        2. Clique em **"Salvar & Notificar n8n"**
        3. A mensagem é salva no banco e o n8n recebe o webhook
        4. Visualize o resultado completo no histórico

        **Vantagem**: Simula o fluxo de produção real.
        """)

        with st.expander("Exemplos de mensagens"):
            examples = [
                "Estou com problema na minha conta, preciso de ajuda urgente",
                "Gostaria de falar com o setor de financeiro",
                "O produto chegou com defeito, preciso de troca",
                "Aproveitamento do desconto para compra futura"
            ]
            for ex in examples:
                if st.button(ex, key=f"ex_2_{hash(ex)}"):
                    st.session_state.current_text = ex
                    st.session_state.page = "🧪 Classificar"

    st.divider()

    st.header("📊 Exemplo de Resultado")

    example = {
        "categoria": "reclamacao",
        "setor": "logistica",
        "prioridade": "alta",
        "sentimento": "negativo",
        "resumo": "Cliente relata atraso na entrega do pedido.",
        "confianca": 0.92
    }

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Categoria", example["categoria"].title(), delta="")

    with col2:
        st.metric("Setor", example["setor"].title(), delta="")

    with col3:
        st.metric("Prioridade", example["prioridade"].upper(), delta="")

    st.markdown(f"""
    **Resumo**: {example['resumo']} (Confiança: {example['confianca']:.2f})
    """)

def render_classifier():
    """Página de classificação."""
    st.header("🧪 Classificador de Mensagens")

    # Coluna esquerda: Input
    with st.columns([1, 2])[0]:
        st.subheader("Digite sua mensagem")
        texto = st.text_area(
            "Mensagem:",
            height=200,
            placeholder="Digite aqui sua mensagem para classificar...",
            label_visibility="collapsed"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            use_real_ai = st.checkbox(
                "Usar IA Real",
                value=False,
                help="Marque para usar modelos reais (OpenAI/Gemini/Groq)"
            )

        with col2:
            modo_fluxo = st.selectbox(
                "Modo de execução:",
                ["Classificar (Rápido)", "Salvar & Notificar"],
                label_visibility="collapsed"
            )

        with col3:
            submit_btn = st.button("🎯 Processar", use_container_width=True)

    # Coluna direita: Resultado
    with st.columns([2, 1])[1]:
        st.subheader("Status do Processo")

        status_placeholder = st.empty()

        if "classificacao" in st.session_state:
            # Renderiza resultado
            resultado = st.session_state.classificacao

            col1, col2, col3 = st.columns(3)

            with col1:
                delta = ""
                if resultado["prioridade"] == "alta":
                    delta = "🔴 Alta"
                elif resultado["prioridade"] == "media":
                    delta = "🟡 Média"
                else:
                    delta = "🟢 Baixa"

                st.metric("Prioridade", resultado["prioridade"].upper(), delta=delta)

            with col2:
                st.metric("Categoria", resultado["categoria"].title(), delta="")

            with col3:
                st.metric("Setor", resultado["setor"].title(), delta="")

            st.metric("Sentimento", resultado["sentimento"].title(), delta="")

            st.markdown(f"""
            **Confiança**: {resultado['confianca']:.2f}
            **Resumo**: {resultado['resumo']}
            """)

            if resultado["confianca"] < 0.6:
                st.warning("⚠️ Confiança baixa - provável necessidade de revisão humana")
            else:
                st.success("✅ Confiança alta - classificação confiável")

        elif "processed_message" in st.session_state:
            # Renderiza mensagem processada completa
            resultado = st.session_state.processed_message

            col1, col2, col3 = st.columns(3)

            with col1:
                delta = ""
                if resultado["classificacao"]["prioridade"] == "alta":
                    delta = "🔴 Alta"
                elif resultado["classificacao"]["prioridade"] == "media":
                    delta = "🟡 Média"
                else:
                    delta = "🟢 Baixa"

                st.metric("Prioridade", resultado["classificacao"]["prioridade"].upper(), delta=delta)

            with col2:
                st.metric("Categoria", resultado["classificacao"]["categoria"].title(), delta="")

            with col3:
                st.metric("Setor", resultado["classificacao"]["setor"].title(), delta="")

            st.metric("Sentimento", resultado["classificacao"]["sentimento"].title(), delta="")

            st.markdown(f"""
            **Confiança**: {resultado['classificacao']['confianca']:.2f}
            **Resumo**: {resultado['classificacao']['resumo']}
            """)

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Provedor", resultado["provedor"], delta="")

            with col2:
                if resultado["notificado"]:
                    st.metric("Status n8n", "✅ Notificado", delta_color="inverse")
                else:
                    st.metric("Status n8n", "❌ Não notificado", delta_color="inverse")

            if resultado["notificado"]:
                st.success("✅ Mensagem salva e notificada com sucesso!")

    # Ações
    if submit_btn and texto:
        with status_placeholder.container():
            status_placeholder.info("⏳ Processando...")

        try:
            if modo_fluxo == "Salvar & Notificar":
                result = save_and_notify(texto)

                if result:
                    st.session_state.processed_message = result
                    st.success("✅ Mensagem processada com sucesso!")
            else:
                result = classify_text(texto, use_real_ai=use_real_ai)

                if result:
                    st.session_state.classificacao = result
                    st.success("✅ Classificação concluída!")

        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

    # Botão para limpar
    if st.button("🔄 Limpar Resultados", type="secondary"):
        st.session_state.classificacao = None
        st.session_state.processed_message = None
        status_placeholder.empty()

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
