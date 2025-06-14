from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import app, db
from models import Usuario, Conta, Categoria, Transacao, Orcamento
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func, extract, and_

# Helper functions
def require_auth():
    if 'usuario_id' not in session:
        flash('Faça login primeiro!', 'warning')
        return redirect(url_for('login'))

    # Verifica se o usuário ainda existe no banco
    usuario = Usuario.query.get(session['usuario_id'])
    if not usuario:
        # Se o usuário não existe mais, remove a sessão e redireciona
        session.pop('usuario_id', None)
        flash('Sessão expirada. Faça login novamente!', 'warning')
        return redirect(url_for('login'))

    return None # Retorna None se a autenticação for bem-sucedida

def get_current_user():
    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        # Se o usuário não existe mais no banco, limpa a sessão
        if not usuario:
            session.pop('usuario_id', None)
            return None
        return usuario
    return None

# Context processor to make get_current_user available in templates
@app.context_processor
def inject_user():
    return dict(get_current_user=get_current_user)

# Authentication routes
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se já está logado e o usuário existe, redireciona para dashboard
    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        if usuario:
            return redirect(url_for('dashboard'))
        else:
            # Remove sessão inválida se o usuário não for encontrado no banco
            session.pop('usuario_id', None)

    if request.method == 'POST':
        email = request.form.get('email') # Usar .get() para evitar KeyError
        senha = request.form.get('senha') # Usar .get() para evitar KeyError

        if not email or not senha:
             flash('Por favor, preencha email e senha.', 'danger')
             return render_template('login.html')

        try:
            usuario = Usuario.query.filter_by(email=email).first()

            if usuario and usuario.check_password(senha):
                session['usuario_id'] = usuario.id
                # O Flask lida com a persistência da sessão (cookies) automaticamente
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Email ou senha incorretos.', 'danger')
        except Exception as e:
            # Captura exceções durante o processo de login (ex: problema com o banco)
            flash(f'Ocorreu um erro durante o login. Tente novamente. Detalhe: {str(e)}', 'danger')
            # Opcional: logar o erro 'e' para depuração

    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        email = request.form.get('email') # Usar .get()
        senha = request.form.get('senha') # Usar .get()
        nome = request.form.get('nome', '')

        if not email or not senha:
             flash('Por favor, preencha email e senha.', 'danger')
             return redirect(url_for('cadastro'))

        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'danger')
            return redirect(url_for('cadastro'))

        try:
            novo_usuario = Usuario(email=email, nome=nome)
            novo_usuario.set_password(senha)
            db.session.add(novo_usuario)
            # db.session.commit() # Commit inicial para obter o ID do novo usuário

            # Create default categories
            categorias_default = [
                ('Salário', 'receita', '#28a745', '💼'),
                ('Freelance', 'receita', '#17a2b8', '💻'),
                ('Investimentos', 'receita', '#20c997', '📈'),
                ('Alimentação', 'despesa', '#dc3545', '🍽️'),
                ('Transporte', 'despesa', '#fd7e14', '🚗'),
                ('Moradia', 'despesa', '#6610f2', '🏠'),
                ('Saúde', 'despesa', '#e83e8c', '🏥'),
                ('Educação', 'despesa', '#20c997', '📚'),
                ('Lazer', 'despesa', '#ffc107', '🎮'),
                ('Outros', 'despesa', '#6c757d', '📦'),
            ]

            # Associar categorias ao novo usuário antes do commit final
            for nome_cat, tipo, cor, icone in categorias_default:
                categoria = Categoria(
                    nome=nome_cat, tipo=tipo, cor=cor, icone=icone,
                    usuario_id=novo_usuario.id # Associa ao novo usuário
                )
                db.session.add(categoria)

            # Create default account
            conta_default = Conta(
                nome='Conta Principal',
                tipo='conta_corrente',
                banco='Banco Principal',
                saldo_inicial=0, # Definir saldo inicial
                saldo_atual=0, # Definir saldo atual
                usuario_id=novo_usuario.id # Associa ao novo usuário
            )
            db.session.add(conta_default)

            db.session.commit() # Commit final após adicionar usuário, categorias e conta

            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback() # Em caso de erro, desfaz as alterações no banco
            flash(f'Ocorreu um erro ao realizar o cadastro: {str(e)}', 'danger')
            # Opcional: logar o erro 'e' para depuração

    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    flash('Você saiu da sessão.', 'info')
    return redirect(url_for('login'))

# ... (restante do seu código para dashboard, transacoes, contas, categorias, orcamentos, relatorios, api)
# Como essas rotas não foram o foco do problema de login, não foram modificadas neste exemplo.

# Dashboard
@app.route('/dashboard')
def dashboard():
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    hoje = date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year
    
    # Summary calculations
    total_receitas = db.session.query(func.sum(Transacao.valor)).filter(
        Transacao.usuario_id == usuario.id,
        Transacao.tipo == 'receita',
        Transacao.paga == True,
        extract('month', Transacao.data) == mes_atual,
        extract('year', Transacao.data) == ano_atual
    ).scalar() or 0
    
    total_despesas = db.session.query(func.sum(Transacao.valor)).filter(
        Transacao.usuario_id == usuario.id,
        Transacao.tipo == 'despesa',
        Transacao.paga == True,
        extract('month', Transacao.data) == mes_atual,
        extract('year', Transacao.data) == ano_atual
    ).scalar() or 0
    
    saldo_mes = total_receitas - total_despesas
    
    # Pending transactions
    contas_vencidas = Transacao.query.filter(
        Transacao.usuario_id == usuario.id,
        Transacao.paga == False,
        Transacao.data_vencimento < hoje
    ).count()
    
    # Calculate next month's first day for "contas a vencer"
    if mes_atual == 12:
        proximo_mes = 1
        proximo_ano = ano_atual + 1
    else:
        proximo_mes = mes_atual + 1
        proximo_ano = ano_atual
    
    contas_vencer = Transacao.query.filter(
        Transacao.usuario_id == usuario.id,
        Transacao.paga == False,
        Transacao.data_vencimento >= hoje,
        Transacao.data_vencimento < date(proximo_ano, proximo_mes, 1)
    ).count()
    
    # Recent transactions
    transacoes_recentes = Transacao.query.filter(
        Transacao.usuario_id == usuario.id
    ).order_by(Transacao.created_at.desc()).limit(5).all()
    
    # Account balances
    contas = Conta.query.filter(
        Conta.usuario_id == usuario.id,
        Conta.ativa == True
    ).all()
    
    return render_template('dashboard.html', 
                         usuario=usuario,
                         total_receitas=total_receitas,
                         total_despesas=total_despesas,
                         saldo_mes=saldo_mes,
                         contas_vencidas=contas_vencidas,
                         contas_vencer=contas_vencer,
                         transacoes_recentes=transacoes_recentes,
                         contas=contas)

# Transactions
@app.route('/transacoes')
def transacoes():
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    page = request.args.get('page', 1, type=int)
    tipo_filtro = request.args.get('tipo', '')
    categoria_filtro = request.args.get('categoria', '', type=int)
    conta_filtro = request.args.get('conta', '', type=int)
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    venc_inicio = request.args.get('venc_inicio', '')
    venc_fim = request.args.get('venc_fim', '')
    
    query = Transacao.query.filter(Transacao.usuario_id == usuario.id)
    
    # Apply filters
    if tipo_filtro:
        query = query.filter(Transacao.tipo == tipo_filtro)
    if categoria_filtro:
        query = query.filter(Transacao.categoria_id == categoria_filtro)
    if conta_filtro:
        query = query.filter(Transacao.conta_id == conta_filtro)
    if data_inicio:
        query = query.filter(Transacao.data >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
    if data_fim:
        query = query.filter(Transacao.data <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    if venc_inicio:
        query = query.filter(Transacao.data_vencimento >= datetime.strptime(venc_inicio, '%Y-%m-%d').date())
    if venc_fim:
        query = query.filter(Transacao.data_vencimento <= datetime.strptime(venc_fim, '%Y-%m-%d').date())
    
    # Calculate totals for filtered results
    filtered_transacoes = query.all()
    total_receitas = sum(t.valor for t in filtered_transacoes if t.tipo == 'receita')
    total_despesas = sum(t.valor for t in filtered_transacoes if t.tipo == 'despesa')
    total_saldo = total_receitas - total_despesas
    
    transacoes = query.order_by(Transacao.data.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    categorias = Categoria.query.filter(Categoria.usuario_id == usuario.id, Categoria.ativa == True).all()
    contas = Conta.query.filter(Conta.usuario_id == usuario.id, Conta.ativa == True).all()
    
    # Format totals for display
    total_receitas_formatado = f"R$ {total_receitas:.2f}"
    total_despesas_formatado = f"R$ {total_despesas:.2f}"
    total_saldo_formatado = f"R$ {total_saldo:.2f}"
    
    return render_template('transactions.html', 
                         transacoes=transacoes,
                         categorias=categorias,
                         contas=contas,
                         tipo_filtro=tipo_filtro,
                         categoria_filtro=categoria_filtro,
                         conta_filtro=conta_filtro,
                         data_inicio=data_inicio,
                         data_fim=data_fim,
                         venc_inicio=venc_inicio,
                         venc_fim=venc_fim,
                         total_receitas=total_receitas,
                         total_despesas=total_despesas,
                         total_saldo=total_saldo,
                         total_receitas_formatado=total_receitas_formatado,
                         total_despesas_formatado=total_despesas_formatado,
                         total_saldo_formatado=total_saldo_formatado,
                         hoje=date.today())

@app.route('/transacoes/nova', methods=['GET', 'POST'])
def nova_transacao():
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    
    if request.method == 'POST':
        try:
            transacao = Transacao(
                descricao=request.form['descricao'],
                valor=Decimal(request.form['valor']),
                tipo=request.form['tipo'],
                data=datetime.strptime(request.form['data'], '%Y-%m-%d').date(),
                data_vencimento=datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date() if request.form.get('data_vencimento') else None,
                paga=bool(request.form.get('paga')),
                observacoes=request.form.get('observacoes', ''),
                usuario_id=usuario.id,
                conta_id=int(request.form['conta_id']),
                categoria_id=int(request.form['categoria_id'])
            )
            
            db.session.add(transacao)
            
            # Update account balance if transaction is paid
            if transacao.paga:
                conta = Conta.query.get(transacao.conta_id)
                if transacao.tipo == 'receita':
                    conta.saldo_atual += transacao.valor
                else:
                    conta.saldo_atual -= transacao.valor
            
            db.session.commit()
            flash('Transação criada com sucesso!', 'success')
            return redirect(url_for('transacoes'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar transação: {str(e)}', 'danger')
    
    categorias = Categoria.query.filter(Categoria.usuario_id == usuario.id, Categoria.ativa == True).all()
    contas = Conta.query.filter(Conta.usuario_id == usuario.id, Conta.ativa == True).all()
    
    return render_template('transactions.html', 
                         categorias=categorias,
                         contas=contas,
                         nova_transacao=True,
                         transacoes=None)

@app.route('/transacoes/<int:id>/pagar', methods=['POST'])
def pagar_transacao(id):
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    transacao = Transacao.query.filter(
        Transacao.id == id,
        Transacao.usuario_id == usuario.id
    ).first_or_404()
    
    if not transacao.paga:
        transacao.paga = True
        
        # Update account balance
        conta = Conta.query.get(transacao.conta_id)
        if transacao.tipo == 'receita':
            conta.saldo_atual += transacao.valor
        else:
            conta.saldo_atual -= transacao.valor
        
        db.session.commit()
        flash('Transação marcada como paga!', 'success')
    
    return redirect(url_for('transacoes'))

@app.route('/transacoes/<int:id>/editar', methods=['GET', 'POST'])
def editar_transacao(id):
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    transacao = Transacao.query.filter(
        Transacao.id == id,
        Transacao.usuario_id == usuario.id
    ).first_or_404()
    
    if request.method == 'POST':
        try:
            # Store old values for balance adjustment
            old_valor = transacao.valor
            old_tipo = transacao.tipo
            old_conta_id = transacao.conta_id
            old_paga = transacao.paga
            
            # Update transaction
            transacao.descricao = request.form['descricao']
            transacao.valor = Decimal(request.form['valor'])
            transacao.tipo = request.form['tipo']
            transacao.data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
            transacao.data_vencimento = datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date() if request.form.get('data_vencimento') else None
            transacao.observacoes = request.form.get('observacoes', '')
            transacao.conta_id = int(request.form['conta_id'])
            transacao.categoria_id = int(request.form['categoria_id'])
            new_paga = bool(request.form.get('paga'))
            
            # Adjust account balances if necessary
            if old_paga:
                # Remove old transaction from balance
                old_conta = Conta.query.get(old_conta_id)
                if old_tipo == 'receita':
                    old_conta.saldo_atual -= old_valor
                else:
                    old_conta.saldo_atual += old_valor
            
            if new_paga:
                # Add new transaction to balance
                nova_conta = Conta.query.get(transacao.conta_id)
                if transacao.tipo == 'receita':
                    nova_conta.saldo_atual += transacao.valor
                else:
                    nova_conta.saldo_atual -= transacao.valor
            
            transacao.paga = new_paga
            
            db.session.commit()
            flash('Transação atualizada com sucesso!', 'success')
            return redirect(url_for('transacoes'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar transação: {str(e)}', 'danger')
    
    categorias = Categoria.query.filter(Categoria.usuario_id == usuario.id, Categoria.ativa == True).all()
    contas = Conta.query.filter(Conta.usuario_id == usuario.id, Conta.ativa == True).all()
    
    return render_template('edit_transaction.html', 
                         transacao=transacao,
                         categorias=categorias,
                         contas=contas)

@app.route('/transacoes/<int:id>/excluir', methods=['POST'])
def excluir_transacao(id):
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    transacao = Transacao.query.filter(
        Transacao.id == id,
        Transacao.usuario_id == usuario.id
    ).first_or_404()
    
    try:
        # Adjust account balance if transaction was paid
        if transacao.paga:
            conta = Conta.query.get(transacao.conta_id)
            if transacao.tipo == 'receita':
                conta.saldo_atual -= transacao.valor
            else:
                conta.saldo_atual += transacao.valor
        
        db.session.delete(transacao)
        db.session.commit()
        flash('Transação excluída com sucesso!', 'success')
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir transação: {str(e)}', 'danger')
    
    return redirect(url_for('transacoes'))

# Accounts
@app.route('/contas')
def contas():
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    contas = Conta.query.filter(
        Conta.usuario_id == usuario.id,
        Conta.ativa == True
    ).all()
    
    return render_template('accounts.html', contas=contas)

@app.route('/contas/nova', methods=['GET', 'POST'])
def nova_conta():
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    
    if request.method == 'POST':
        try:
            saldo_inicial = Decimal(request.form.get('saldo_inicial', '0'))
            conta = Conta(
                nome=request.form['nome'],
                tipo=request.form['tipo'],
                banco=request.form.get('banco', ''),
                saldo_inicial=saldo_inicial,
                saldo_atual=saldo_inicial,
                cor=request.form.get('cor', '#6a0dad'),
                icone=request.form.get('icone', '🏦'),
                usuario_id=usuario.id
            )
            
            db.session.add(conta)
            db.session.commit()
            flash('Conta criada com sucesso!', 'success')
            return redirect(url_for('contas'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar conta: {str(e)}', 'danger')
    
    return render_template('accounts.html', nova_conta=True)

# Categories
@app.route('/categorias')
def categorias():
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    categorias = Categoria.query.filter(
        Categoria.usuario_id == usuario.id,
        Categoria.ativa == True
    ).all()
    
    return render_template('categories.html', categorias=categorias)

@app.route('/categorias/nova', methods=['GET', 'POST'])
def nova_categoria():
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    
    if request.method == 'POST':
        try:
            categoria = Categoria(
                nome=request.form['nome'],
                tipo=request.form['tipo'],
                cor=request.form.get('cor', '#6a0dad'),
                icone=request.form.get('icone', '💰'),
                usuario_id=usuario.id
            )
            
            db.session.add(categoria)
            db.session.commit()
            flash('Categoria criada com sucesso!', 'success')
            return redirect(url_for('categorias'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar categoria: {str(e)}', 'danger')
    
    return render_template('categories.html', nova_categoria=True)

# Budgets
@app.route('/orcamentos')
def orcamentos():
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    hoje = date.today()
    
    orcamentos = Orcamento.query.filter(
        Orcamento.usuario_id == usuario.id,
        Orcamento.mes == hoje.month,
        Orcamento.ano == hoje.year,
        Orcamento.ativo == True
    ).all()
    
    return render_template('budgets.html', orcamentos=orcamentos)

@app.route('/orcamentos/novo', methods=['GET', 'POST'])
def novo_orcamento():
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    
    if request.method == 'POST':
        try:
            orcamento = Orcamento(
                nome=request.form['nome'],
                valor_planejado=Decimal(request.form['valor_planejado']),
                mes=int(request.form['mes']),
                ano=int(request.form['ano']),
                usuario_id=usuario.id,
                categoria_id=int(request.form['categoria_id'])
            )
            
            db.session.add(orcamento)
            db.session.commit()
            flash('Orçamento criado com sucesso!', 'success')
            return redirect(url_for('orcamentos'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar orçamento: {str(e)}', 'danger')
    
    categorias = Categoria.query.filter(
        Categoria.usuario_id == usuario.id, 
        Categoria.ativa == True,
        Categoria.tipo == 'despesa'
    ).all()
    
    return render_template('budgets.html', categorias=categorias, novo_orcamento=True, now=datetime.now())

# Reports
@app.route('/relatorios')
def relatorios():
    auth_check = require_auth()
    if auth_check:
        return auth_check
    
    usuario = get_current_user()
    return render_template('reports.html', usuario=usuario)

# API endpoints for charts
@app.route('/api/receitas-despesas/<int:ano>')
def api_receitas_despesas(ano):
    auth_check = require_auth()
    if auth_check:
        return jsonify({'error': 'Not authenticated'}), 401
    
    usuario = get_current_user()
    
    dados = []
    for mes in range(1, 13):
        receitas = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.usuario_id == usuario.id,
            Transacao.tipo == 'receita',
            Transacao.paga == True,
            extract('month', Transacao.data) == mes,
            extract('year', Transacao.data) == ano
        ).scalar() or 0
        
        despesas = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.usuario_id == usuario.id,
            Transacao.tipo == 'despesa',
            Transacao.paga == True,
            extract('month', Transacao.data) == mes,
            extract('year', Transacao.data) == ano
        ).scalar() or 0
        
        dados.append({
            'mes': mes,
            'receitas': float(receitas),
            'despesas': float(despesas)
        })
    
    return jsonify(dados)

@app.route('/api/gastos-categoria/<int:ano>/<int:mes>')
def api_gastos_categoria(ano, mes):
    auth_check = require_auth()
    if auth_check:
        return jsonify({'error': 'Not authenticated'}), 401
    
    usuario = get_current_user()
    
    resultado = db.session.query(
        Categoria.nome,
        Categoria.cor,
        func.sum(Transacao.valor).label('total')
    ).join(Transacao).filter(
        Transacao.usuario_id == usuario.id,
        Transacao.tipo == 'despesa',
        Transacao.paga == True,
        extract('month', Transacao.data) == mes,
        extract('year', Transacao.data) == ano
    ).group_by(Categoria.id).all()
    
    dados = []
    for categoria, cor, total in resultado:
        dados.append({
            'categoria': categoria,
            'cor': cor,
            'valor': float(total)
        })
    
    return jsonify(dados)
