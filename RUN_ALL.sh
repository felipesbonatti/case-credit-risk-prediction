#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

clear
echo "================================================================================"
echo "   SISTEMA DE ANALISE DE CREDITO E INADIMPLENCIA - SANTANDER"
echo "   Inicializacao Automatica - Linux/macOS"
echo "================================================================================"
echo ""

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar Python
if ! command_exists python3; then
    echo -e "${RED}[ERRO]${NC} Python 3 nao encontrado!"
    echo "Por favor, instale Python 3.11 ou superior:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
    echo "  macOS: brew install python@3.11"
    exit 1
fi

# Verificar Node.js
if ! command_exists node; then
    echo -e "${RED}[ERRO]${NC} Node.js nao encontrado!"
    echo "Por favor, instale Node.js 18 ou superior:"
    echo "  Ubuntu/Debian: sudo apt-get install nodejs npm"
    echo "  macOS: brew install node"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python e Node.js encontrados!"
echo ""

# --------------------------------------------------------------------------------
# AUTOMACAO .ENV
# --------------------------------------------------------------------------------
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}[AVISO]${NC} Arquivo .env nao encontrado. Criando a partir de .env.example..."
        cp .env.example .env
        echo -e "${GREEN}[OK]${NC} Arquivo .env criado com sucesso."
    else
        echo -e "${RED}[ERRO]${NC} Arquivo .env.example nao encontrado. Nao e possivel criar .env."
        exit 1
    fi
else
    echo -e "${GREEN}[OK]${NC} Arquivo .env ja existe. Pulando criacao automatica."
fi
echo ""
# --------------------------------------------------------------------------------

# Instalar dependências da API
echo "================================================================================"
echo -e "${BLUE}[1/4]${NC} Instalando dependencias da API..."
echo "================================================================================"
cd api || exit 1

if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual Python..."
    python3 -m venv venv
fi

echo "Ativando ambiente virtual..."
source venv/bin/activate

echo "Instalando pacotes Python..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

cd ..
echo ""

# Instalar dependências do Dashboard
echo "================================================================================"
echo -e "${BLUE}[2/4]${NC} Instalando dependencias do Dashboard..."
echo "================================================================================"
cd dashboard_premium || exit 1

if [ ! -d "node_modules" ]; then
    echo "Instalando pacotes Node.js..."
    npm install
else
    echo "Dependencias ja instaladas!"
fi

cd ..
echo ""

# Função para cleanup ao encerrar
cleanup() {
    echo ""
    echo "================================================================================"
    echo "Encerrando sistema..."
    echo "================================================================================"
    
    # Matar processos
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null
        echo "API encerrada."
    fi
    
    if [ ! -z "$DASHBOARD_PID" ]; then
        kill $DASHBOARD_PID 2>/dev/null
        echo "Dashboard encerrado."
    fi
    
    # Matar processos por porta (fallback)
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    
    echo "Sistema encerrado com sucesso!"
    exit 0
}

# Registrar função de cleanup
trap cleanup SIGINT SIGTERM EXIT

# Iniciar API em background
echo "================================================================================"
echo -e "${BLUE}[3/4]${NC} Iniciando API na porta 8000..."
echo "================================================================================"
cd api || exit 1
source venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
API_PID=$!
cd ..
echo -e "${GREEN}API iniciada em segundo plano!${NC} (PID: $API_PID)"
echo "Aguardando 5 segundos para API inicializar..."
sleep 5
echo ""

# Verificar se API está rodando
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${YELLOW}[AVISO]${NC} API pode nao ter iniciado corretamente."
    echo "Verifique o arquivo api/api.log para detalhes."
    echo ""
fi

# Iniciar Dashboard
echo "================================================================================"
echo -e "${BLUE}[4/4]${NC} Iniciando Dashboard na porta 5173..."
echo "================================================================================"
cd dashboard_premium || exit 1
echo ""
echo "================================================================================"
echo -e "${GREEN}   SISTEMA PRONTO!${NC}"
echo "================================================================================"
echo ""
echo "   API Backend:     http://localhost:8000"
echo "   API Docs:        http://localhost:8000/docs"
echo "   Dashboard:       http://localhost:3000"
echo ""
echo "   O navegador sera aberto automaticamente em alguns segundos..."
echo "   Pressione Ctrl+C para encerrar o sistema."
echo ""
echo "================================================================================"
echo ""

# Iniciar servidor de desenvolvimento
npm run dev

# Aguardar
wait
