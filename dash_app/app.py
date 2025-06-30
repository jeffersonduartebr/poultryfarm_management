import dash
import dash_bootstrap_components as dbc
from db import get_engine, init_db
from layout import create_layout
from callbacks import register_callbacks

# Inicializa banco de dados e tabelas
engine = get_engine()
init_db(engine)

# Inicializa aplicação Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "Dashboard Criação de Aves"
app.layout = create_layout()

# Registra callbacks
register_callbacks(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)