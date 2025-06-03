Sistema de Gestão Financeira Pessoal
Sistema completo de gestão financeira pessoal desenvolvido em Flask, permitindo controle de receitas, despesas, contas e orçamentos.

Funcionalidades
Autenticação de Usuários: Sistema de login e cadastro
Dashboard: Visão geral das finanças com gráficos e resumos
Transações: Controle completo de receitas e despesas
Contas: Gerenciamento de contas bancárias e cartões
Categorias: Organização por categorias personalizáveis
Orçamentos: Planejamento e controle de gastos mensais
Relatórios: Análise detalhada com gráficos interativos
Estrutura do Projeto
/
├── app.py                 # Configuração principal da aplicação
├── main.py               # Ponto de entrada
├── models.py             # Modelos do banco de dados
├── routes.py             # Rotas da aplicação
├── templates/            # Templates HTML
│   ├── base.html
│   ├── login.html
│   ├── cadastro.html
│   ├── dashboard.html
│   ├── transactions.html
│   ├── edit_transaction.html
│   ├── accounts.html
│   ├── categories.html
│   ├── budgets.html
│   └── reports.html
├── static/               # Arquivos estáticos
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js
│       └── charts.js
├── render_requirements.txt
└── README.md
Configuração para Desenvolvimento Local (VS Code)
Pré-requisitos
Python 3.11+
PostgreSQL (ou SQLite para desenvolvimento)
Instalação
Clone o repositório ou baixe os arquivos
Crie um ambiente virtual:
python -m venv venv
Ative o ambiente virtual:
Windows: venv\Scripts\activate
macOS/Linux: source venv/bin/activate
Instale as dependências:
pip install -r render_requirements.txt
Configure as variáveis de ambiente criando um arquivo .env:
DATABASE_URL=postgresql://usuario:senha@localhost/financeiro
SESSION_SECRET=sua_chave_secreta_aqui
Para desenvolvimento local com SQLite, use:

DATABASE_URL=sqlite:///financeiro.db
SESSION_SECRET=chave_de_desenvolvimento
Execute a aplicação:
python main.py
A aplicação estará disponível em http://localhost:5000

Configuração para Deploy no Render
1. Preparação dos Arquivos
Certifique-se de que os seguintes arquivos estão na raiz do projeto:

main.py (ponto de entrada)
render_requirements.txt (dependências)
Todos os outros arquivos Python e pastas
2. Configuração no Render
Conecte seu repositório no Render

Configure o serviço:

Environment: Python 3
Build Command: pip install -r render_requirements.txt
Start Command: gunicorn --bind 0.0.0.0:$PORT main:app
Variáveis de Ambiente (adicione no painel do Render):

DATABASE_URL: URL do PostgreSQL fornecida pelo Render
SESSION_SECRET: Uma chave secreta forte
3. Banco de Dados
Crie um PostgreSQL no Render
Copie a URL de conexão e adicione na variável DATABASE_URL
As tabelas serão criadas automaticamente na primeira execução
Uso da Aplicação
1. Primeiro Acesso
Acesse a aplicação e clique em "Cadastrar"
Crie sua conta com email e senha
Faça login para acessar o sistema
2. Configuração Inicial
Contas: Cadastre suas contas bancárias, cartões, etc.
Categorias: Crie categorias para organizar suas transações
Orçamentos: Defina orçamentos mensais por categoria
3. Uso Diário
Transações: Registre suas receitas e despesas
Dashboard: Acompanhe o resumo das suas finanças
Relatórios: Analise seus gastos com gráficos detalhados
Tecnologias Utilizadas
Backend: Flask, SQLAlchemy
Frontend: Bootstrap 5, Chart.js
Banco de Dados: PostgreSQL (produção) / SQLite (desenvolvimento)
Deploy: Render, Gunicorn
Funcionalidades Detalhadas
Transações
Cadastro de receitas e despesas
Filtros por data, categoria, conta e vencimento
Edição e exclusão de transações
Marcação de transações como pagas
Totalização automática dos filtros aplicados
Contas
Múltiplas contas (bancárias, cartões, dinheiro)
Controle de saldo automático
Cores e ícones personalizáveis
Categorias
Categorias de receita e despesa
Cores e ícones personalizáveis
Organização hierárquica
Orçamentos
Orçamentos mensais por categoria
Acompanhamento de progresso
Alertas de limite ultrapassado
Análise de economia
Dashboard
Resumo financeiro do mês
Gráficos de receitas vs despesas
Transações recentes
Contas a vencer
Solução de Problemas
Erro de Conexão com Banco
Verifique se a variável DATABASE_URL está configurada corretamente.

Erro 500 na Aplicação
Verifique os logs do servidor para identificar o problema específico.

Problemas de Assets Estáticos
Certifique-se de que as pastas static/css e static/js estão no local correto.

Contribuição
Para contribuir com o projeto:

Faça um fork do repositório
Crie uma branch para sua feature
Faça commit das mudanças
Abra um Pull Request
Licença
Este projeto é para uso pessoal e educacional.
