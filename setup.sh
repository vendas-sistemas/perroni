#!/bin/bash

# Script de configuração rápida do Sistema de Fiscalização de Obras
# Execute: chmod +x setup.sh && ./setup.sh

echo "🏗️  Sistema de Fiscalização de Obras - Setup"
echo "=========================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verifica Python
echo "1️⃣  Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 não encontrado. Instale Python 3.9 ou superior.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $(python3 --version) encontrado${NC}"
echo ""

# Verifica PostgreSQL
echo "2️⃣  Verificando PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL não encontrado. Instale PostgreSQL 12+${NC}"
    echo "Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
    echo "macOS: brew install postgresql"
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL encontrado${NC}"
echo ""

# Criar ambiente virtual
echo "3️⃣  Criando ambiente virtual..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Ambiente virtual já existe. Pulando...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Ambiente virtual criado${NC}"
fi
echo ""

# Ativar ambiente virtual
echo "4️⃣  Ativando ambiente virtual..."
source venv/bin/activate
echo -e "${GREEN}✅ Ambiente virtual ativado${NC}"
echo ""

# Instalar dependências
echo "5️⃣  Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependências instaladas${NC}"
echo ""

# Configurar .env
echo "6️⃣  Configurando variáveis de ambiente..."
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env já existe. Pulando...${NC}"
else
    cp .env.example .env
    echo -e "${GREEN}✅ Arquivo .env criado${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANTE: Edite o arquivo .env com suas configurações!${NC}"
fi
echo ""

# Criar diretórios necessários
echo "7️⃣  Criando diretórios..."
mkdir -p media/fiscalizacao
mkdir -p media/funcionarios/fotos
mkdir -p media/ferramentas/fotos
mkdir -p static
mkdir -p staticfiles
echo -e "${GREEN}✅ Diretórios criados${NC}"
echo ""

# Instruções para banco de dados
echo "8️⃣  Configuração do Banco de Dados"
echo -e "${YELLOW}"
echo "Execute os seguintes comandos no PostgreSQL:"
echo ""
echo "sudo -u postgres psql"
echo "CREATE DATABASE fiscalizacao_obras;"
echo "CREATE USER fiscal_user WITH PASSWORD 'sua_senha';"
echo "ALTER ROLE fiscal_user SET client_encoding TO 'utf8';"
echo "ALTER ROLE fiscal_user SET default_transaction_isolation TO 'read committed';"
echo "ALTER ROLE fiscal_user SET timezone TO 'America/Sao_Paulo';"
echo "GRANT ALL PRIVILEGES ON DATABASE fiscalizacao_obras TO fiscal_user;"
echo "\q"
echo -e "${NC}"
echo ""
read -p "Pressione ENTER depois de configurar o banco de dados..."

# Executar migrations
echo "9️⃣  Executando migrations..."
python manage.py makemigrations
python manage.py migrate
echo -e "${GREEN}✅ Migrations executadas${NC}"
echo ""

# Criar superusuário
echo "🔟 Criando superusuário..."
echo -e "${YELLOW}Preencha os dados do administrador:${NC}"
python manage.py createsuperuser
echo ""

# Coletar arquivos estáticos
echo "1️⃣1️⃣  Coletando arquivos estáticos..."
python manage.py collectstatic --noinput
echo -e "${GREEN}✅ Arquivos estáticos coletados${NC}"
echo ""

# Mensagem final
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup concluído com sucesso!${NC}"
echo "=========================================="
echo ""
echo "📋 Próximos passos:"
echo ""
echo "1. Edite o arquivo .env com suas configurações"
echo "2. Inicie o servidor:"
echo "   python manage.py runserver"
echo ""
echo "3. Acesse:"
echo "   http://localhost:8000 - Sistema"
echo "   http://localhost:8000/admin - Painel Admin"
echo ""
echo "4. Leia COMO_PEDIR_IA.md para continuar o desenvolvimento"
echo ""
echo -e "${YELLOW}⭐ Desenvolvido para otimizar fiscalização de obras${NC}"
echo ""
