import os
from dotenv import load_dotenv
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from extensions import db  # Instância do SQLAlchemy

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Corrige URL do banco se necessário
database_url = os.environ.get("DATABASE_URL", "sqlite:///financeiro.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Tenta importar modelos e rotas + criar as tabelas
try:
    with app.app_context():
        import models
        import routes
        db.create_all()
except Exception as e:
    print("❌ Erro ao conectar ou inicializar o banco de dados:", e)

if __name__ == "__main__":
    app.run(debug=True)

