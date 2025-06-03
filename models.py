from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from decimal import Decimal

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, default='')
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relationships
    contas = db.relationship('Conta', backref='usuario', lazy=True, cascade='all, delete-orphan')
    categorias = db.relationship('Categoria', backref='usuario', lazy=True, cascade='all, delete-orphan')
    transacoes = db.relationship('Transacao', backref='usuario', lazy=True, cascade='all, delete-orphan')
    orcamentos = db.relationship('Orcamento', backref='usuario', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.senha_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.senha_hash, password)
    
    def __repr__(self):
        return f'<Usuario {self.email}>'

class Conta(db.Model):
    __tablename__ = 'contas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # conta_corrente, poupanca, cartao_credito, etc
    banco = db.Column(db.String(100))
    saldo_inicial = db.Column(db.Numeric(15, 2), default=0)
    saldo_atual = db.Column(db.Numeric(15, 2), default=0)
    cor = db.Column(db.String(7), default='#6a0dad')
    icone = db.Column(db.String(10), default='🏦')
    ativa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Relationships
    transacoes = db.relationship('Transacao', backref='conta', lazy=True)
    
    @property
    def saldo_formatado(self):
        return f"R$ {self.saldo_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def __repr__(self):
        return f'<Conta {self.nome}>'

class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # receita ou despesa
    cor = db.Column(db.String(7), default='#6a0dad')
    icone = db.Column(db.String(10), default='💰')
    ativa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Relationships
    transacoes = db.relationship('Transacao', backref='categoria', lazy=True)
    orcamentos = db.relationship('Orcamento', backref='categoria', lazy=True)
    
    def __repr__(self):
        return f'<Categoria {self.nome}>'

class Transacao(db.Model):
    __tablename__ = 'transacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Numeric(15, 2), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # receita ou despesa
    data = db.Column(db.Date, nullable=False, default=date.today)
    data_vencimento = db.Column(db.Date)
    paga = db.Column(db.Boolean, default=False)
    observacoes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    conta_id = db.Column(db.Integer, db.ForeignKey('contas.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    
    @property
    def valor_formatado(self):
        return f"R$ {self.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def status(self):
        if self.paga:
            return 'paga'
        elif self.data_vencimento and self.data_vencimento < date.today():
            return 'vencida'
        else:
            return 'pendente'
    
    @property
    def status_class(self):
        status_map = {
            'paga': 'success',
            'vencida': 'danger',
            'pendente': 'warning'
        }
        return status_map.get(self.status, 'secondary')
    
    def __repr__(self):
        return f'<Transacao {self.descricao}: {self.valor}>'

class Orcamento(db.Model):
    __tablename__ = 'orcamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    valor_planejado = db.Column(db.Numeric(15, 2), nullable=False)
    mes = db.Column(db.Integer, nullable=False)  # 1-12
    ano = db.Column(db.Integer, nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    
    @property
    def valor_gasto(self):
        # Calculate spent amount for this budget period
        from sqlalchemy import and_, extract
        return db.session.query(db.func.sum(Transacao.valor)).filter(
            and_(
                Transacao.categoria_id == self.categoria_id,
                Transacao.usuario_id == self.usuario_id,
                Transacao.paga == True,
                extract('month', Transacao.data) == self.mes,
                extract('year', Transacao.data) == self.ano
            )
        ).scalar() or Decimal('0')
    
    @property
    def percentual_usado(self):
        if self.valor_planejado > 0:
            return min(float(self.valor_gasto / self.valor_planejado * 100), 100)
        return 0
    
    @property
    def valor_restante(self):
        return max(self.valor_planejado - self.valor_gasto, Decimal('0'))
    
    @property
    def status(self):
        percentual = self.percentual_usado
        if percentual >= 100:
            return 'danger'
        elif percentual >= 80:
            return 'warning'
        else:
            return 'success'
    
    def __repr__(self):
        return f'<Orcamento {self.nome}: {self.valor_planejado}>'
