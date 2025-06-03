import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Carregar variáveis de ambiente do .env (somente em desenvolvimento local)
load_dotenv()

# Classe base para modelos SQLAlchemy
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Criar a aplicação Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Corrigir headers quando atrás de proxy (como no Render)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configurar URL do banco de dados
database_url = os.environ.get("DATABASE_URL", "sqlite:///financeiro.db")

# Corrigir prefixo para PostgreSQL (Render usa 'postgres://')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Configurar SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar extensão do banco de dados
db.init_app(app)

# Verificar se a variável DATABASE_URL está presente (boa prática para produção)
if not database_url:
    raise RuntimeError("DATABASE_URL não foi definida. Verifique as variáveis de ambiente.")

# Criar tabelas e importar rotas
with app.app_context():
    import models   # Certifique-se de que models.py existe
    import routes   # Certifique-se de que routes.py existe

    db.create_all()
