from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'chave_secreta_segura'

# Banco de dados
def criar_banco():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

criar_banco()

# Página inicial
@app.route('/')
def index():
    return redirect('/login')

# Cadastro
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        try:
            conn = sqlite3.connect('usuarios.db')
            c = conn.cursor()
            c.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
            conn.commit()
            conn.close()
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('Email já cadastrado!', 'danger')
    return render_template('cadastro.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        conn = sqlite3.connect('usuarios.db')
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
        usuario = c.fetchone()
        conn.close()
        if usuario:
            session['usuario_id'] = usuario[0]
            session['usuario_nome'] = usuario[1]
            return redirect('/dashboard')
        else:
            flash('Credenciais inválidas!', 'danger')
    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect('/login')
    nome = session['usuario_nome']
    return render_template('dashboard.html', nome=nome)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
@app.route('/contas_pagar', methods=['GET', 'POST'])
def contas_pagar():
    if request.method == 'POST':
        # Aqui você irá salvar a conta no banco de dados
        descricao = request.form['descricao']
        valor = request.form['valor']
        data_lancamento = request.form['data_lancamento']
        data_vencimento = request.form['data_vencimento']
        contato = request.form['contato']
        # (Você pode salvar isso em uma lista, arquivo ou banco de dados)

        flash("Conta registrada com sucesso!", "success")

    return render_template('contas_pagar.html')


if __name__ == '__main__':
    app.run(debug=True)
