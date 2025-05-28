from flask import Flask, render_template, session, redirect
import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect('/login')

    usuario = {
        'id': session['usuario_id'],
        'nome': session['usuario_nome']
    }

    # Simulações de dados — substituir por dados reais do banco depois
    saldo_total = 3500.75
    total_a_receber = 2000.00
    total_a_pagar = 1500.25
    saldo_mes = 500.50

    movimentacoes_recentes = [
        {
            'descricao': 'Venda produto X',
            'data_transacao': datetime.datetime(2025, 5, 25),
            'valor': 150.00,
            'tipo': 'receita'
        },
        {
            'descricao': 'Conta de luz',
            'data_transacao': datetime.datetime(2025, 5, 24),
            'valor': 120.00,
            'tipo': 'despesa'
        }
    ]

    proximos_vencimentos = [
        {
            'descricao': 'Aluguel',
            'data_vencimento': datetime.datetime(2025, 6, 1),
            'valor': 1000.00
        },
        {
            'descricao': 'Internet',
            'data_vencimento': datetime.datetime(2025, 6, 3),
            'valor': 150.00
        }
    ]

    return render_template('dashboard.html',
                           usuario=usuario,
                           saldo_total=saldo_total,
                           total_a_receber=total_a_receber,
                           total_a_pagar=total_a_pagar,
                           saldo_mes=saldo_mes,
                           movimentacoes_recentes=movimentacoes_recentes,
                           proximos_vencimentos=proximos_vencimentos)

# Exemplo de sessão para testar
@app.route('/login')
def login():
    session['usuario_id'] = 1
    session['usuario_nome'] = 'João Silva'
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
