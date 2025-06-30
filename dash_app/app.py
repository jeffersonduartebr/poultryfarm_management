import os
import dash
import dash_bootstrap_components as dbc
# Importamos apenas o que é necessário, sem o Redirect
from dash import dcc, html, Output, Input 
from flask import Flask
from flask_login import LoginManager, current_user, logout_user

from db import get_engine, init_db
from layout import create_layout, create_login_layout
from callbacks import register_callbacks
from user_management import get_user_by_id

# --- Inicialização ---
server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
app.title = "Dashboard de Gestão de Avicultura"

server.config.update(SECRET_KEY=os.urandom(24))

# --- Configuração do LoginManager ---
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

# --- Layout Dinâmico e Roteamento ---
app.layout = html.Div([
    # O componente dcc.Location principal que lê a URL
    dcc.Location(id='url', refresh=False),
    # O conteúdo da página será renderizado aqui
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    # Lógica de redirecionamento para usuário LOGADO
    if current_user.is_authenticated:
        if pathname == '/login':
            # Se tentar acessar /login, redireciona para a home
            return dcc.Location(pathname='/', id='redirect-to-home')
        if pathname == '/logout':
            logout_user()
            # Redireciona para o login após sair
            return dcc.Location(pathname='/login', id='redirect-after-logout')
        # Se estiver em qualquer outra página, mostra o layout principal
        return create_layout()
    # Lógica de redirecionamento para usuário NÃO LOGADO
    else:
        if pathname == '/login':
            # Se já estiver na página de login, mostra o layout de login
            return create_login_layout()
        # Se tentar acessar qualquer outra página, redireciona para o login
        return dcc.Location(pathname='/login', id='redirect-to-login')

# --- Inicialização Final ---
engine = get_engine()
init_db(engine)
register_callbacks(app)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8050, debug=False)