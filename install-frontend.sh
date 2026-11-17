#!/bin/bash

# Script para instalar dependências do Frontend Sandbox

echo "📦 Instalando dependências do Frontend Sandbox..."
echo ""

# Verifica se estamos no diretório correto
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Erro: Este script deve ser executado no raiz do projeto."
    exit 1
fi

# Verifica se venv existe
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment não encontrado. Crie com 'python3.12 -m venv .venv'"
    exit 1
fi

# Ativa o venv
source .venv/bin/activate

# Instala Streamlit
echo "✅ Instalando Streamlit..."
pip install -q streamlit==1.37.0

# Instala requests
echo "✅ Instalando requests..."
pip install -q requests==2.32.3

# Verifica instalação
echo ""
echo "🔍 Verificando instalação..."
if python -c "import streamlit, requests" 2>/dev/null; then
    echo "✅ Todas as dependências instaladas com sucesso!"
    echo ""
    echo "Para rodar o frontend:"
    echo "  streamlit run frontend/app.py"
else
    echo "❌ Erro ao verificar instalação"
    exit 1
fi
