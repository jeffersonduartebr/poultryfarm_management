import os
import dash
import dash_bootstrap_components as dbc
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
    external_stylesheets=[
        dbc.themes.BOOTSTRAP  # Bootstrap responsivo
        # Removido dbc.icons.BOOTSTRAP para evitar AttributeError se não existir na versão instalada
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        # Essencial para mobile (e evita zoom automático em alguns teclados)
        {"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1"}
    ]
)
app.title = "Dashboard de Gestão de Avicultura"
server.config.update(SECRET_KEY=os.urandom(24))

# --- Login Manager ---
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

# --- Layout Dinâmico / Roteamento ---
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', style={"minHeight": "100vh"})
])

@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    # ✅ Rota pública: /public/lote/<id>  (sem login)
    if pathname and pathname.startswith('/public/lote/'):
        try:
            lote_id = int(pathname.split('/')[3])
        except Exception:
            return html.Div(
                dbc.Alert("URL inválida. Lote não identificado.", color="danger"),
                style={"padding": "1rem"}
            )
        from layout import layout_public_lote
        return layout_public_lote(lote_id)

    # 🔐 Rotas privadas (requer login)
    if current_user.is_authenticated:
        if pathname == '/login':
            return dcc.Location(pathname='/', id='redirect-to-home')
        if pathname == '/logout':
            logout_user()
            return dcc.Location(pathname='/login', id='redirect-after-logout')
        from layout import create_layout
        return create_layout()
    else:
        from layout import create_login_layout
        if pathname == '/login':
            return create_login_layout()
        return dcc.Location(pathname='/login', id='redirect-to-login')


# --- Inicialização Banco e Callbacks ---
engine = get_engine()
init_db(engine)
register_callbacks(app)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8050, debug=False)
