#!/bin/bash

# Script de setup rápido para o Frontend Sandbox

echo "🚀 Iniciando setup do Frontend Sandbox..."
echo ""

# 1. Verifica se estamos no diretório correto
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Erro: Este script deve ser executado no raiz do projeto."
    exit 1
fi

# 2. Verifica se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker não encontrado. Instale Docker antes de continuar."
    exit 1
fi

# 3. Verifica se as imagens existem
echo "🔍 Verificando imagens Docker..."
if docker images | grep -q "ia-classifier-api"; then
    echo "✅ Imagens do projeto encontradas"
else
    echo "⚠️  Nenhuma imagem encontrada. Execute 'docker compose build' primeiro."
fi

echo ""
echo "📊 Próximos passos:"
echo ""
echo "1. Iniciar o backend (API, Postgres, n8n):"
echo "   docker compose up --build -d"
echo ""
echo "2. Importar o workflow do n8n (uma vez):"
echo "   docker compose --profile import run --rm n8n-import"
echo ""
echo "3. Iniciar o Frontend Sandbox:"
echo "   docker compose --profile demo up --build frontend"
echo ""
echo "4. Acessar o frontend:"
echo "   http://localhost:8501"
echo ""
echo "5. Testar com exemplos:"
echo "   - No homepage, clique nos botões de exemplo"
echo "   - No painel de classificação, digite mensagens e clique em 'Processar'"
echo "   - Para fluxo completo, use o modo 'Salvar & Notificar'"
echo ""
echo "6. Visualizar histórico:"
echo "   - Vá para a aba 'Histórico' no frontend"
echo "   - Veja todas as mensagens salvas no banco"
echo ""
echo "7. Testes unitários:"
echo "   pytest tests/frontend/test_app.py"
echo ""
echo "8. Limpar o ambiente:"
echo "   docker compose down"
echo "   docker compose down -v"
echo ""
echo "📝 Documentação:"
echo "   - frontend/README.md - Guia completo do frontend"
echo "   - README.md - Documentação geral do projeto"
echo ""
echo "🎉 Setup concluído!"
