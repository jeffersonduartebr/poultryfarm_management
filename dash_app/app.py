import dash
import dash_bootstrap_components as dbc
from db import get_engine, init_db
from layout import create_layout
from callbacks import register_callbacks

# 1. Inicializa a conexão com o banco de dados
engine = get_engine()

# 2. Garante que todas as tabelas (incluindo as novas) existam
#    Rode o script SQL de migração antes de iniciar a app pela primeira vez
init_db(engine)

# 3. Inicializa a aplicação Dash
app = dash.Dash(
    __name__, 
    external_stylesheets=[dbc.themes.BOOTSTRAP], 
    suppress_callback_exceptions=True,
    # Adiciona meta tag para responsividade em dispositivos móveis
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
app.title = "Dashboard de Gestão de Avicultura"

# 4. Define o layout da aplicação a partir do layout.py
app.layout = create_layout()

# 5. Registra todos os callbacks definidos em callbacks.py
register_callbacks(app)

# 6. Executa o servidor
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)