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
        email = request.form.get('email')
        senha = request.form.get('senha')
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
            db.session.flush()  # Aqui geramos o ID do usuário no banco

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

            for nome_cat, tipo, cor, icone in categorias_default:
                categoria = Categoria(
                    nome=nome_cat,
                    tipo=tipo,
                    cor=cor,
                    icone=icone,
                    usuario_id=novo_usuario.id
                )
                db.session.add(categoria)

            conta_default = Conta(
                nome='Conta Principal',
                tipo='conta_corrente',
                banco='Banco Principal',
                saldo_inicial=0,
                saldo_atual=0,
                usuario_id=novo_usuario.id
            )
            db.session.add(conta_default)

            db.session.commit()

            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao realizar o cadastro: {str(e)}', 'danger')

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
from dateutil.relativedelta import relativedelta  # IMPORTAÇÃO NECESSÁRIA no topo do seu arquivo
from decimal import Decimal
from datetime import datetime, date

@app.route('/dashboard/nova-transacao', methods=['GET', 'POST'])
def nova_transacao_dashboard():
    auth_check = require_auth()
    if auth_check:
        return auth_check

    usuario = get_current_user()
    
    contas = Conta.query.filter_by(usuario_id=usuario.id, ativa=True).all()
    categorias = Categoria.query.filter_by(usuario_id=usuario.id).all()

    if request.method == 'POST':
        # Lógica para salvar a nova transação (você pode completar depois)
        pass

    return render_template('nova_transacao_dashboard.html', contas=contas, categorias=categorias)

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
    descricao_filtro = request.args.get('descricao', '').strip()  # Novo filtro

    # Filtrar transações do usuário E não pagas
    query = Transacao.query.filter(
        Transacao.usuario_id == usuario.id,
        Transacao.paga == False
    )
    
    # Aplicar filtros opcionais
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
    if descricao_filtro:
        query = query.filter(Transacao.descricao.ilike(f"%{descricao_filtro}%"))  # Filtro por descrição
    
    # Calcular totais somente para as transações não pagas (filtradas)
    filtered_transacoes = query.all()
    total_receitas = sum(t.valor for t in filtered_transacoes if t.tipo == 'receita')
    total_despesas = sum(t.valor for t in filtered_transacoes if t.tipo == 'despesa')
    total_saldo = total_receitas - total_despesas
    
    transacoes = query.order_by(Transacao.data.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    categorias = Categoria.query.filter(Categoria.usuario_id == usuario.id, Categoria.ativa == True).all()
    contas = Conta.query.filter(Conta.usuario_id == usuario.id, Conta.ativa == True).all()
    
    # Formatar valores para exibição
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
                         descricao_filtro=descricao_filtro,  # Passar para o template
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
            descricao = request.form['descricao']
            valor_parcela = Decimal(request.form['valor'])  # agora representa o valor de cada parcela
            tipo = request.form['tipo']
            data_primeira = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
            data_vencimento_primeira = None
            if request.form.get('data_vencimento'):
                data_vencimento_primeira = datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date()
            paga = bool(request.form.get('paga'))
            observacoes = request.form.get('observacoes', '')
            conta_id = int(request.form['conta_id'])
            categoria_id = int(request.form['categoria_id'])
            qtd_parcelas = int(request.form.get('parcelas', 1))

            for i in range(qtd_parcelas):
                data_parcela = data_primeira + relativedelta(months=i)
                data_vencimento_parcela = None
                if data_vencimento_primeira:
                    # Mantém o mesmo dia, só mudando o mês
                    data_vencimento_parcela = data_vencimento_primeira + relativedelta(months=i)

                transacao = Transacao(
                    descricao=f"{descricao} ({i+1}/{qtd_parcelas})" if qtd_parcelas > 1 else descricao,
                    valor=valor_parcela,
                    tipo=tipo,
                    data=data_parcela,
                    data_vencimento=data_vencimento_parcela,
                    paga=paga if qtd_parcelas == 1 else False,
                    observacoes=observacoes,
                    usuario_id=usuario.id,
                    conta_id=conta_id,
                    categoria_id=categoria_id
                )
                db.session.add(transacao)

                if transacao.paga:
                    conta = Conta.query.get(conta_id)
                    if tipo == 'receita':
                        conta.saldo_atual += valor_parcela
                    else:
                        conta.saldo_atual -= valor_parcela

            db.session.commit()
            flash('Transação criada com sucesso!', 'success')
            return redirect(url_for('transacoes'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar transação: {str(e)}', 'danger')

    categorias = Categoria.query.filter_by(usuario_id=usuario.id, ativa=True).all()
    contas = Conta.query.filter_by(usuario_id=usuario.id, ativa=True).all()

    return render_template(
        'nova_transacao.html',
        categorias=categorias,
        contas=contas
    )

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

        # Atualiza saldo da conta
        conta = Conta.query.get(transacao.conta_id)
        if transacao.tipo == 'receita':
            conta.saldo_atual += transacao.valor
        else:
            conta.saldo_atual -= transacao.valor

        db.session.commit()
        flash('Transação marcada como paga!', 'success')

    # Captura os filtros atuais da URL (se houver)
    filtros = {
        'page': request.args.get('page'),
        'tipo': request.args.get('tipo'),
        'categoria': request.args.get('categoria'),
        'conta': request.args.get('conta'),
        'data_inicio': request.args.get('data_inicio'),
        'data_fim': request.args.get('data_fim'),
        'venc_inicio': request.args.get('venc_inicio'),
        'venc_fim': request.args.get('venc_fim')
    }

    # Remove chaves com valor None para não poluir a URL
    filtros_limpos = {k: v for k, v in filtros.items() if v}

    return redirect(url_for('transacoes', **filtros_limpos))


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

# Lista de movimentações pagas (receitas/despesas pagas)
@app.route('/movimentacoes')
def movimentacoes():
    auth_check = require_auth()
    if auth_check:
        return auth_check

    usuario = get_current_user()
    page = request.args.get('page', 1, type=int)
    per_page = 10

    movimentacoes_pagas = Transacao.query.filter_by(
        usuario_id=usuario.id,
        paga=True
    ).order_by(Transacao.data.desc()).paginate(page=page, per_page=per_page)

    return render_template('movimentacoes.html', movimentacoes=movimentacoes_pagas)

# Excluir movimentação do histórico
@app.route('/movimentacoes/excluir/<int:id>', methods=['POST'])
def excluir_movimentacao(id):
    auth_check = require_auth()
    if auth_check:
        return auth_check

    transacao = Transacao.query.get_or_404(id)
    usuario = get_current_user()

    if transacao.usuario_id != usuario.id:
        flash('Operação não autorizada.', 'danger')
        return redirect(url_for('movimentacoes'))

    db.session.delete(transacao)
    db.session.commit()
    flash('Movimentação excluída com sucesso!', 'success')
    return redirect(url_for('movimentacoes'))

# Adicionar nova movimentação manualmente
@app.route('/movimentacoes/nova', methods=['GET', 'POST'])
def nova_movimentacao():
    auth_check = require_auth()
    if auth_check:
        return auth_check

    usuario = get_current_user()

    if request.method == 'POST':
        tipo = request.form['tipo']
        categoria_id = request.form['categoria_id']
        conta_id = request.form['conta_id']
        valor = Decimal(request.form['valor'].replace(',', '.'))
        data = datetime.strptime(request.form['data'], '%Y-%m-%d')
        descricao = request.form['descricao']

        nova = Transacao(
            tipo=tipo,
            categoria_id=categoria_id,
            conta_id=conta_id,
            valor=valor,
            data=data,
            descricao=descricao,
            paga=True,  # já entra como paga
            usuario_id=usuario.id
        )

        db.session.add(nova)
        db.session.commit()
        flash('Movimentação adicionada com sucesso!', 'success')
        return redirect(url_for('movimentacoes'))

    categorias = Categoria.query.filter_by(usuario_id=usuario.id).all()
    contas = Conta.query.filter_by(usuario_id=usuario.id).all()
    return render_template('nova_movimentacao.html', categorias=categorias, contas=contas)

from flask import request, redirect, url_for, render_template, flash

@app.route('/contas/editar/<int:conta_id>', methods=['GET', 'POST'])
def editar_conta(conta_id):
    conta = Conta.query.get_or_404(conta_id)  # Busca a conta ou retorna 404 se não achar

    if request.method == 'POST':
        # Atualiza os dados da conta com o que veio do formulário
        conta.nome = request.form['nome']
        conta.tipo = request.form['tipo']
        conta.saldo_inicial = float(request.form['saldo_inicial'])
        conta.banco = request.form.get('banco')
        conta.cor = request.form.get('cor')
        conta.icone = request.form.get('icone')

        db.session.commit()  # Salva no banco

        flash('Conta atualizada com sucesso!', 'success')
        return redirect(url_for('contas'))

    # Se GET, mostra o formulário preenchido
    return render_template('editar_conta.html', conta=conta)

@app.route('/contas/excluir/<int:conta_id>', methods=['POST'])
def excluir_conta(conta_id):
    conta = Conta.query.get_or_404(conta_id)
    db.session.delete(conta)
    db.session.commit()
    flash('Conta excluída com sucesso!', 'success')
    return redirect(url_for('contas'))
