from flask import render_template, request, redirect, session, url_for, flash, jsonify
from app import app, db
from models import Usuario, Contato, ContaPagar, ContaReceber, Transacao
from datetime import datetime, date
from sqlalchemy import desc, extract

@app.route('/')
def index():
    return redirect('/login')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        # Verificar se o email já existe
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'danger')
            return render_template('cadastro.html')
        
        try:
            usuario = Usuario(nome=nome, email=email)
            usuario.set_senha(senha)
            db.session.add(usuario)
            db.session.commit()
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect('/login')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar usuário!', 'danger')
            app.logger.error(f"Erro no cadastro: {e}")
    
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_senha(senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            return redirect('/dashboard')
        else:
            flash('Credenciais inválidas!', 'danger')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    usuario = Usuario.query.get(session['usuario_id'])
    
    # Calcular métricas do dashboard
    saldo_total = usuario.get_saldo_total()
    total_a_receber = usuario.get_total_a_receber()
    total_a_pagar = usuario.get_total_a_pagar()
    
    # Transações do mês atual
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    transacoes_mes = Transacao.query.filter(
        Transacao.usuario_id == usuario.id,
        extract('month', Transacao.data_transacao) == mes_atual,
        extract('year', Transacao.data_transacao) == ano_atual
    ).all()
    
    receitas_mes = sum(t.valor for t in transacoes_mes if t.tipo == 'receita')
    despesas_mes = sum(t.valor for t in transacoes_mes if t.tipo == 'despesa')
    saldo_mes = receitas_mes - despesas_mes
    
    # Movimentações recentes
    movimentacoes_recentes = Transacao.query.filter_by(usuario_id=usuario.id)\
        .order_by(desc(Transacao.created_at)).limit(5).all()
    
    # Próximos vencimentos
    hoje = date.today()
    proximos_vencimentos = []
    
    # Contas a pagar próximas do vencimento
    contas_pagar_proximas = ContaPagar.query.filter(
        ContaPagar.usuario_id == usuario.id,
        ContaPagar.status == 'pendente',
        ContaPagar.data_vencimento >= hoje
    ).order_by(ContaPagar.data_vencimento).limit(5).all()
    
    # Contas a receber próximas do vencimento
    contas_receber_proximas = ContaReceber.query.filter(
        ContaReceber.usuario_id == usuario.id,
        ContaReceber.status == 'pendente',
        ContaReceber.data_vencimento >= hoje
    ).order_by(ContaReceber.data_vencimento).limit(5).all()
    
    proximos_vencimentos = contas_pagar_proximas + contas_receber_proximas
    
    return render_template('dashboard.html', 
                         usuario=usuario,
                         saldo_total=saldo_total,
                         total_a_receber=total_a_receber,
                         total_a_pagar=total_a_pagar,
                         saldo_mes=saldo_mes,
                         movimentacoes_recentes=movimentacoes_recentes,
                         proximos_vencimentos=proximos_vencimentos)

@app.route('/contas_pagar', methods=['GET', 'POST'])
def contas_pagar():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        try:
            descricao = request.form['descricao']
            valor = float(request.form['valor'])
            data_lancamento = datetime.strptime(request.form['data_lancamento'], '%Y-%m-%d').date()
            data_vencimento = datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date()
            contato_nome = request.form.get('contato')
            observacoes = request.form.get('observacoes', '')
            
            # Criar ou encontrar contato
            contato = None
            if contato_nome:
                contato = Contato.query.filter_by(
                    nome=contato_nome, 
                    usuario_id=session['usuario_id'],
                    tipo='fornecedor'
                ).first()
                
                if not contato:
                    contato = Contato(
                        nome=contato_nome,
                        tipo='fornecedor',
                        usuario_id=session['usuario_id']
                    )
                    db.session.add(contato)
                    db.session.flush()
            
            conta = ContaPagar(
                descricao=descricao,
                valor=valor,
                data_lancamento=data_lancamento,
                data_vencimento=data_vencimento,
                observacoes=observacoes,
                usuario_id=session['usuario_id'],
                contato_id=contato.id if contato else None
            )
            
            db.session.add(conta)
            db.session.commit()
            flash('Conta a pagar registrada com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao registrar conta!', 'danger')
            app.logger.error(f"Erro ao registrar conta a pagar: {e}")
    
    # Filtros de pesquisa
    query = ContaPagar.query.filter_by(usuario_id=session['usuario_id'])
    
    # Aplicar filtros se existirem
    search_descricao = request.args.get('search_descricao', '')
    search_fornecedor = request.args.get('search_fornecedor', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    
    if search_descricao:
        query = query.filter(ContaPagar.descricao.ilike(f'%{search_descricao}%'))
    
    if search_fornecedor:
        query = query.join(Contato, ContaPagar.contato_id == Contato.id, isouter=True)\
                     .filter(Contato.nome.ilike(f'%{search_fornecedor}%'))
    
    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        query = query.filter(ContaPagar.data_vencimento >= data_inicio_obj)
    
    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
        query = query.filter(ContaPagar.data_vencimento <= data_fim_obj)
    
    contas = query.order_by(desc(ContaPagar.data_vencimento)).all()
    
    return render_template('contas_pagar.html', contas=contas,
                         search_descricao=search_descricao,
                         search_fornecedor=search_fornecedor,
                         data_inicio=data_inicio,
                         data_fim=data_fim)

@app.route('/pagar_conta/<int:conta_id>')
def pagar_conta(conta_id):
    if 'usuario_id' not in session:
        return redirect('/login')
    
    conta = ContaPagar.query.filter_by(id=conta_id, usuario_id=session['usuario_id']).first()
    if conta:
        conta.status = 'paga'
        conta.data_pagamento = date.today()
        
        # Criar transação correspondente
        transacao = Transacao(
            descricao=f"Pagamento: {conta.descricao}",
            valor=conta.valor,
            tipo='despesa',
            data_transacao=date.today(),
            usuario_id=session['usuario_id'],
            conta_pagar_id=conta.id
        )
        
        db.session.add(transacao)
        db.session.commit()
        flash('Conta marcada como paga!', 'success')
    
    return redirect('/contas_pagar')

@app.route('/excluir_conta_pagar/<int:conta_id>')
def excluir_conta_pagar(conta_id):
    if 'usuario_id' not in session:
        return redirect('/login')
    
    conta = ContaPagar.query.filter_by(id=conta_id, usuario_id=session['usuario_id']).first()
    if conta:
        db.session.delete(conta)
        db.session.commit()
        flash('Conta a pagar excluída com sucesso!', 'success')
    
    return redirect('/contas_pagar')

@app.route('/contas_receber', methods=['GET', 'POST'])
def contas_receber():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        try:
            descricao = request.form['descricao']
            valor = float(request.form['valor'])
            data_lancamento = datetime.strptime(request.form['data_lancamento'], '%Y-%m-%d').date()
            data_vencimento = datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date()
            contato_nome = request.form.get('contato')
            observacoes = request.form.get('observacoes', '')
            
            # Criar ou encontrar contato
            contato = None
            if contato_nome:
                contato = Contato.query.filter_by(
                    nome=contato_nome, 
                    usuario_id=session['usuario_id'],
                    tipo='cliente'
                ).first()
                
                if not contato:
                    contato = Contato(
                        nome=contato_nome,
                        tipo='cliente',
                        usuario_id=session['usuario_id']
                    )
                    db.session.add(contato)
                    db.session.flush()
            
            conta = ContaReceber(
                descricao=descricao,
                valor=valor,
                data_lancamento=data_lancamento,
                data_vencimento=data_vencimento,
                observacoes=observacoes,
                usuario_id=session['usuario_id'],
                contato_id=contato.id if contato else None
            )
            
            db.session.add(conta)
            db.session.commit()
            flash('Conta a receber registrada com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao registrar conta!', 'danger')
            app.logger.error(f"Erro ao registrar conta a receber: {e}")
    
    # Filtros de pesquisa
    query = ContaReceber.query.filter_by(usuario_id=session['usuario_id'])
    
    # Aplicar filtros se existirem
    search_descricao = request.args.get('search_descricao', '')
    search_cliente = request.args.get('search_cliente', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    
    if search_descricao:
        query = query.filter(ContaReceber.descricao.ilike(f'%{search_descricao}%'))
    
    if search_cliente:
        query = query.join(Contato, ContaReceber.contato_id == Contato.id, isouter=True)\
                     .filter(Contato.nome.ilike(f'%{search_cliente}%'))
    
    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        query = query.filter(ContaReceber.data_vencimento >= data_inicio_obj)
    
    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
        query = query.filter(ContaReceber.data_vencimento <= data_fim_obj)
    
    contas = query.order_by(desc(ContaReceber.data_vencimento)).all()
    
    return render_template('contas_receber.html', contas=contas,
                         search_descricao=search_descricao,
                         search_cliente=search_cliente,
                         data_inicio=data_inicio,
                         data_fim=data_fim)

@app.route('/receber_conta/<int:conta_id>')
def receber_conta(conta_id):
    if 'usuario_id' not in session:
        return redirect('/login')
    
    conta = ContaReceber.query.filter_by(id=conta_id, usuario_id=session['usuario_id']).first()
    if conta:
        conta.status = 'recebida'
        conta.data_recebimento = date.today()
        
        # Criar transação correspondente
        transacao = Transacao(
            descricao=f"Recebimento: {conta.descricao}",
            valor=conta.valor,
            tipo='receita',
            data_transacao=date.today(),
            usuario_id=session['usuario_id'],
            conta_receber_id=conta.id
        )
        
        db.session.add(transacao)
        db.session.commit()
        flash('Conta marcada como recebida!', 'success')
    
    return redirect('/contas_receber')

@app.route('/excluir_conta_receber/<int:conta_id>')
def excluir_conta_receber(conta_id):
    if 'usuario_id' not in session:
        return redirect('/login')
    
    conta = ContaReceber.query.filter_by(id=conta_id, usuario_id=session['usuario_id']).first()
    if conta:
        db.session.delete(conta)
        db.session.commit()
        flash('Conta a receber excluída com sucesso!', 'success')
    
    return redirect('/contas_receber')

@app.route('/carteira', methods=['GET', 'POST'])
def carteira():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        try:
            descricao = request.form['descricao']
            valor = float(request.form['valor'])
            tipo = request.form['tipo']
            categoria = request.form.get('categoria', '')
            data_transacao = datetime.strptime(request.form['data_transacao'], '%Y-%m-%d').date()
            observacoes = request.form.get('observacoes', '')
            
            transacao = Transacao(
                descricao=descricao,
                valor=valor,
                tipo=tipo,
                categoria=categoria,
                data_transacao=data_transacao,
                observacoes=observacoes,
                usuario_id=session['usuario_id']
            )
            
            db.session.add(transacao)
            db.session.commit()
            flash('Transação registrada com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao registrar transação!', 'danger')
            app.logger.error(f"Erro ao registrar transação: {e}")
    
    # Filtros de pesquisa
    query = Transacao.query.filter_by(usuario_id=session['usuario_id'])
    
    # Aplicar filtros se existirem
    search_descricao = request.args.get('search_descricao', '')
    search_categoria = request.args.get('search_categoria', '')
    search_tipo = request.args.get('search_tipo', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    
    if search_descricao:
        query = query.filter(Transacao.descricao.ilike(f'%{search_descricao}%'))
    
    if search_categoria:
        query = query.filter(Transacao.categoria.ilike(f'%{search_categoria}%'))
    
    if search_tipo:
        query = query.filter(Transacao.tipo == search_tipo)
    
    if data_inicio:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        query = query.filter(Transacao.data_transacao >= data_inicio_obj)
    
    if data_fim:
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
        query = query.filter(Transacao.data_transacao <= data_fim_obj)
    
    transacoes = query.order_by(desc(Transacao.data_transacao)).all()
    
    usuario = Usuario.query.get(session['usuario_id'])
    saldo_total = usuario.get_saldo_total()
    
    return render_template('carteira.html', transacoes=transacoes, saldo_total=saldo_total,
                         search_descricao=search_descricao,
                         search_categoria=search_categoria,
                         search_tipo=search_tipo,
                         data_inicio=data_inicio,
                         data_fim=data_fim)

@app.route('/contatos', methods=['GET', 'POST'])
def contatos():
    if 'usuario_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        try:
            nome = request.form['nome']
            email = request.form.get('email', '')
            telefone = request.form.get('telefone', '')
            endereco = request.form.get('endereco', '')
            tipo = request.form['tipo']
            
            contato = Contato(
                nome=nome,
                email=email,
                telefone=telefone,
                endereco=endereco,
                tipo=tipo,
                usuario_id=session['usuario_id']
            )
            
            db.session.add(contato)
            db.session.commit()
            flash('Contato adicionado com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao adicionar contato!', 'danger')
            app.logger.error(f"Erro ao adicionar contato: {e}")
    
    # Listar contatos
    contatos_list = Contato.query.filter_by(usuario_id=session['usuario_id'])\
        .order_by(Contato.nome).all()
    
    return render_template('contatos.html', contatos=contatos_list)

@app.route('/excluir_contato/<int:contato_id>')
def excluir_contato(contato_id):
    if 'usuario_id' not in session:
        return redirect('/login')
    
    contato = Contato.query.filter_by(id=contato_id, usuario_id=session['usuario_id']).first()
    if contato:
        db.session.delete(contato)
        db.session.commit()
        flash('Contato excluído com sucesso!', 'success')
    
    return redirect('/contatos')

@app.route('/excluir_transacao/<int:transacao_id>')
def excluir_transacao(transacao_id):
    if 'usuario_id' not in session:
        return redirect('/login')
    
    transacao = Transacao.query.filter_by(id=transacao_id, usuario_id=session['usuario_id']).first()
    if transacao:
        db.session.delete(transacao)
        db.session.commit()
        flash('Transação excluída com sucesso!', 'success')
    
    return redirect('/carteira')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
