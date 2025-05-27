from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    contas_pagar = db.relationship('ContaPagar', backref='usuario', lazy=True, cascade='all, delete-orphan')
    contas_receber = db.relationship('ContaReceber', backref='usuario', lazy=True, cascade='all, delete-orphan')
    transacoes = db.relationship('Transacao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    contatos = db.relationship('Contato', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)
    
    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)
    
    def get_saldo_total(self):
        """Calcula o saldo total baseado nas transações"""
        total_receitas = sum(t.valor for t in self.transacoes if t.tipo == 'receita' and t.status == 'confirmada')
        total_despesas = sum(t.valor for t in self.transacoes if t.tipo == 'despesa' and t.status == 'confirmada')
        return total_receitas - total_despesas
    
    def get_total_a_receber(self):
        """Total de contas a receber pendentes"""
        return sum(c.valor for c in self.contas_receber if c.status == 'pendente')
    
    def get_total_a_pagar(self):
        """Total de contas a pagar pendentes"""
        return sum(c.valor for c in self.contas_pagar if c.status == 'pendente')

class Contato(db.Model):
    __tablename__ = 'contatos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.Text)
    tipo = db.Column(db.String(20), nullable=False)  # 'cliente' ou 'fornecedor'
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    contas_pagar = db.relationship('ContaPagar', backref='contato', lazy=True)
    contas_receber = db.relationship('ContaReceber', backref='contato', lazy=True)

class ContaPagar(db.Model):
    __tablename__ = 'contas_pagar'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_lancamento = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date)
    status = db.Column(db.String(20), default='pendente')  # 'pendente', 'paga', 'vencida'
    observacoes = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    contato_id = db.Column(db.Integer, db.ForeignKey('contatos.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_vencida(self):
        from datetime import date
        return self.status == 'pendente' and self.data_vencimento < date.today()

class ContaReceber(db.Model):
    __tablename__ = 'contas_receber'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    data_lancamento = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_recebimento = db.Column(db.Date)
    status = db.Column(db.String(20), default='pendente')  # 'pendente', 'recebida', 'vencida'
    observacoes = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    contato_id = db.Column(db.Integer, db.ForeignKey('contatos.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_vencida(self):
        from datetime import date
        return self.status == 'pendente' and self.data_vencimento < date.today()

class Transacao(db.Model):
    __tablename__ = 'transacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'receita' ou 'despesa'
    categoria = db.Column(db.String(50))
    data_transacao = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='confirmada')  # 'confirmada', 'pendente'
    observacoes = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    conta_pagar_id = db.Column(db.Integer, db.ForeignKey('contas_pagar.id'))
    conta_receber_id = db.Column(db.Integer, db.ForeignKey('contas_receber.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
