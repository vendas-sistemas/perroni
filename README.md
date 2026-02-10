# Sistema de Fiscalização de Obras

Sistema completo em Django para fiscalização de obras com controle de etapas, gestão de funcionários, ferramentas e análise de desempenho.

## 📋 Funcionalidades

### 🏗️ Gestão de Obras
- Cadastro completo de obras
- Controle de 5 etapas principais (29.9%, 45%, 70%, 84%, 95%)
- Cada etapa com suas fases específicas de execução
- Cálculo automático de percentual concluído

### 📸 Fiscalização Diária
- Registro diário com mínimo 6 fotos
- Campos de clima, lixo, placa instalada
- Registro de ociosidade e retrabalho
- Interface otimizada para mobile

### 👷 Gestão de Funcionários
- Cadastro completo com foto
- Diferenciação entre pedreiros e serventes
- Apontamento diário de funcionários
- Fechamento semanal individual
- Cálculo automático de custos

### 🔧 Controle de Ferramentas
- Cadastro de ferramentas com código
- Movimentação entre obras e depósito
- Conferência diária pelo fiscal
- Histórico completo de movimentações

### 📊 Analytics e Relatórios
- Ranking dos 3 melhores e piores pedreiros por etapa
- Média de dias para execução de cada etapa
- Rendimento individual de pedreiros
- Custo de mão de obra por obra
- Dashboard geral do sistema

## 🚀 Instalação

### Pré-requisitos
- Python 3.9+
- PostgreSQL 12+
- pip e virtualenv

### Passo a passo

1. **Clone o repositório**
```bash
cd fiscalizacao_obras
```

2. **Crie e ative o ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure o banco de dados PostgreSQL**
```bash
# Entre no PostgreSQL
psql -U postgres

# Crie o banco de dados
CREATE DATABASE fiscalizacao_obras;
CREATE USER fiscal_user WITH PASSWORD 'sua_senha';
ALTER ROLE fiscal_user SET client_encoding TO 'utf8';
ALTER ROLE fiscal_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE fiscal_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE fiscalizacao_obras TO fiscal_user;
\q
```

5. **Configure as variáveis de ambiente**
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o .env com suas configurações
nano .env
```

Exemplo de `.env`:
```env
SECRET_KEY=sua-chave-secreta-super-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=fiscalizacao_obras
DB_USER=fiscal_user
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
```

6. **Execute as migrações**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Crie um superusuário**
```bash
python manage.py createsuperuser
```

8. **Colete arquivos estáticos**
```bash
mkdir -p static
python manage.py collectstatic --noinput
```

9. **Inicie o servidor**
```bash
python manage.py runserver
```

Acesse: http://localhost:8000

## 📁 Estrutura do Projeto

```
fiscalizacao_obras/
├── config/                 # Configurações principais
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── obras/             # Gestão de obras e etapas
│   │   ├── models.py      # 6 models (Obra + 5 etapas)
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   ├── fiscalizacao/      # Registros diários
│   │   ├── models.py      # Registro + Fotos
│   │   ├── views.py
│   │   └── admin.py
│   ├── funcionarios/      # Gestão de RH
│   │   ├── models.py      # Funcionário + Apontamentos + Fechamentos
│   │   ├── views.py
│   │   └── admin.py
│   ├── ferramentas/       # Controle de ferramentas
│   │   ├── models.py      # Ferramenta + Movimentação + Conferência
│   │   ├── views.py
│   │   └── admin.py
│   └── analytics/         # Análises e relatórios
│       ├── services.py    # Lógica de análise
│       ├── views.py
│       └── urls.py
├── templates/             # Templates HTML
├── static/               # Arquivos estáticos
├── media/                # Uploads (fotos)
├── requirements.txt
└── manage.py
```

## 🎯 Uso do Sistema

### Criando uma Obra

1. Acesse o admin: http://localhost:8000/admin
2. Vá em "Obras" → "Adicionar Obra"
3. Preencha os dados básicos
4. Salve e adicione as etapas

### Registrando Fiscalização Diária

1. Acesse "Fiscalização" → "Nova Fiscalização"
2. Selecione a obra
3. Preencha clima, lixo, placa
4. Informe ociosidade/retrabalho se houver
5. Faça upload de no mínimo 6 fotos
6. Salve o registro

### Apontando Funcionários

1. Acesse "Funcionários" → "Apontamentos"
2. Clique em "Novo Apontamento"
3. Selecione funcionário e obra
4. Confirme o valor da diária
5. Salve

### Conferindo Ferramentas

1. Acesse "Ferramentas" → "Conferência"
2. Selecione a obra
3. Marque status de cada ferramenta (OK/Ausente/Danificada)
4. Registre movimentações se necessário

### Visualizando Análises

1. Acesse "Analytics" → "Dashboard"
2. Veja métricas gerais do sistema
3. Acesse "Rankings" para ver desempenho de pedreiros
4. Clique em um pedreiro para ver rendimento individual

## 📊 Modelos de Dados

### Obra
- Informações básicas (nome, cliente, endereço)
- Status (planejamento, em andamento, pausada, concluída)
- Percentual concluído (calculado automaticamente)

### Etapas (5 tipos)
1. **Etapa 1 (29.9%)**: Fundação
2. **Etapa 2 (45%)**: Estrutura
3. **Etapa 3 (70%)**: Revestimentos e Instalações
4. **Etapa 4 (84%)**: Acabamentos
5. **Etapa 5 (95%)**: Finalização

### Funcionário
- Dados pessoais completos
- Função (pedreiro/servente)
- Valor da diária
- Status (ativo/inativo)

### Registro de Fiscalização
- Data e fiscal responsável
- Clima, lixo, placa
- Ociosidade e retrabalho
- Mínimo 6 fotos

## 🔒 Segurança

- Autenticação obrigatória para todas as views
- Permissões baseadas em grupos
- Proteção CSRF ativada
- Validação de dados em todos os formulários

## 🎨 Próximos Passos (Implementação)

Para completar o sistema, ainda é necessário:

1. **Templates HTML**
   - Criar templates base
   - Templates para cada view
   - Formulários responsivos

2. **Formulários**
   - Forms.py para cada app
   - Validações customizadas
   - Upload múltiplo de imagens

3. **API REST** (opcional)
   - Serializers
   - ViewSets
   - Endpoints para mobile

4. **Testes**
   - Testes unitários
   - Testes de integração
   - Coverage

## 📱 Mobile-Friendly

O sistema foi projetado pensando no uso em campo:
- Interface responsiva
- Formulários simplificados
- Upload de fotos otimizado
- Campos obrigatórios mínimos

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📝 Licença

Este projeto é de uso interno.

## 👥 Suporte

Para dúvidas ou problemas, contate o administrador do sistema.

---

**Desenvolvido para otimizar a fiscalização e gestão de obras**
