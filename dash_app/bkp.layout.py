import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from sqlalchemy import text
from db import get_engine

engine = get_engine()

def get_active_lots():
    try:
        with engine.connect() as conn:
            df = pd.read_sql("SELECT id, identificador_lote FROM lotes WHERE status = 'Ativo' ORDER BY data_alojamento DESC", conn)
            return [{"label": row['identificador_lote'], "value": row['id']} for index, row in df.iterrows()]
    except Exception: return []

def get_all_lots():
    try:
        with engine.connect() as conn:
            df = pd.read_sql("SELECT id, identificador_lote FROM lotes ORDER BY data_alojamento DESC", conn)
            return [{"label": row['identificador_lote'], "value": row['id']} for index, row in df.iterrows()]
    except Exception: return []

def get_distinct_linhagens():
    try:
        with engine.connect() as conn:
            df = pd.read_sql("SELECT DISTINCT linhagem FROM metas_linhagem ORDER BY linhagem", conn)
            return [{"label": lin, "value": lin} for lin in df['linhagem']]
    except Exception: return []

def create_login_layout():
    return dbc.Container([
        dbc.Row(
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(html.H4("Login do Sistema", className="text-center")),
                    dbc.CardBody([
                        dbc.Alert("Por favor, insira suas credenciais para acessar.", color="info"),
                        dbc.Input(id="login-username", type="text", placeholder="Usuário", className="mb-3"),
                        dbc.Input(id="login-password", type="password", placeholder="Senha", className="mb-3"),
                        dbc.Button("Entrar", id="login-button", color="primary", n_clicks=0, className="w-100"),
                        html.Div(id="login-alert-div", className="mt-3")
                    ])
                ]),
                width=12, lg=4, md=6, sm=8
            ),
            justify="center",
            className="mt-5"
        )
    ], fluid=True)

def lotes_layout():
    return dbc.Container([
        html.H3("🛠️ Gestão de Lotes", className="text-center mb-4"),

        dbc.Row([
            # Formulário — ocupa toda a tela no mobile
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Cadastrar Novo Lote"),
                    dbc.CardBody([
                        dbc.Input(id="lote-identificador", placeholder="Identificador do Lote (Ex: Lote 2025-A)", className="mb-2"),
                        dbc.Input(id="lote-linhagem", placeholder="Linhagem (Ex: Cobb, Ross)", className="mb-2"),
                        dbc.Input(id="lote-aviario", placeholder="Aviário Alocado", className="mb-2"),
                        dcc.DatePickerSingle(id="lote-data", date=pd.to_datetime("today"), display_format="DD/MM/YYYY", className="mb-2 d-block"),
                        dbc.Input(id="lote-aves", type="number", placeholder="Nº de Aves Alojadas", className="mb-2"),
                        dbc.Button("Salvar Novo Lote", id="btn-lote-submit", color="primary", className="w-100"),
                        html.Div(id="lote-submit-status", className="mt-2")
                    ])
                ]),
                xs=12, md=6, lg=5, className="mb-4"
            ),

            # Tabela — ocupa toda a tela no mobile
            dbc.Col([
                html.H5("Lotes Registrados"),
                dbc.Spinner(html.Div(id="lotes-table-div")),
                dbc.Button("Finalizar Lote Selecionado", id="btn-lote-finalize", color="warning", className="mt-3 w-100", disabled=True)
            ], xs=12, md=6, lg=7)
        ])
    ], fluid=True)


def view_layout():
    lotes_options = get_all_lots()
    if not lotes_options:
        return dbc.Alert("Nenhum lote encontrado. Cadastre um lote na aba 'Gestão de Lotes'.", color="info")

    return dbc.Container([
        html.H3("📊 Indicadores de Desempenho do Lote", className="text-center mb-3"),

        # Dropdown centralizado - ocupa 100% no mobile e 50% no desktop
        dbc.Row([
            dbc.Col(
                dcc.Dropdown(
                    id="dropdown-lote-indicadores",
                    options=lotes_options,
                    placeholder="Selecione um lote para visualizar"
                ),
                xs=12, sm=12, md=8, lg=6, className="mb-3"
            )
        ], justify="center"),

        html.Hr(),

        # Gráficos com responsividade total
        dbc.Row([
            dbc.Col(
                dbc.Spinner(dcc.Graph(id="graph-peso-medio", config={"responsive": True}, style={"width": "100%"})),
                xs=12, md=6, className="mb-3"
            ),
            dbc.Col(
                dbc.Spinner(dcc.Graph(id="graph-mortalidade-acumulada", config={"responsive": True}, style={"width": "100%"})),
                xs=12, md=6, className="mb-3"
            )
        ]),

        dbc.Row([
            dbc.Col(
                dbc.Spinner(dcc.Graph(id="graph-consumo-comparativo", config={"responsive": True}, style={"width": "100%"})),
                xs=12, md=6, className="mb-3"
            ),
            dbc.Col(
                dbc.Spinner(dcc.Graph(id="graph-conversao-alimentar", config={"responsive": True}, style={"width": "100%"})),
                xs=12, md=6, className="mb-3"
            )
        ])
    ], fluid=True)


def insert_weekly_layout():
    return dbc.Container([
        html.H3("📝 Inserir Dados Semanais do Lote", className="text-center mb-4"),

        dcc.Dropdown(
            id="dropdown-lote-weekly",
            options=get_active_lots(),
            placeholder="Selecione um Lote Ativo",
            className="mb-3"
        ),

        html.Div(id='weekly-form-div', children=[
            dbc.Row([
                dbc.Col([dbc.Label("Semana (idade)"), dbc.Input(id="input-semana", type="number", min=1, placeholder="Informe a semana")], xs=6, md=3),
                dbc.Col([dbc.Label("N° aves na semana"), dbc.Input(id="input-aves-semana", type="number", disabled=True)], xs=6, md=3),
                dbc.Col([dbc.Label("Data de Pesagem"), dcc.DatePickerSingle(id="input-data-pesagem", date=pd.to_datetime("today"), display_format="DD/MM/YYYY")], xs=12, md=3)
            ], className="mb-3"),

            html.H5("Mortalidades da Semana"),

            dbc.Row([
                *[
                    dbc.Col(dbc.Input(id=f"input-mort-dia-{i}", type="number", value=0, placeholder=f"D{i}"), xs=4, md=1, className="mb-2")
                    for i in range(1, 8)
                ],
                dbc.Col([dbc.Label("Total"), dbc.Input(id="input-mort-total", type="number", disabled=True)], xs=12, md=2)
            ], className="mb-3"),

            html.H5("Desempenho da Semana"),

            dbc.Row([
                dbc.Col([dbc.Label("Peso médio (g)"), dbc.Input(id="input-peso-med", type="number")], xs=12, md=6),
                dbc.Col([dbc.Label("Consumo Real (g/ave/dia)"), dbc.Input(id="input-consumo-real", type="number")], xs=12, md=6)
            ], className="mb-3"),

            dbc.Button("Enviar Semana", id="btn-submit-weekly", color="primary", className="w-100"),
            html.Div(id="submit-status-weekly", className="mt-2")
        ], style={'display': 'none'})
    ], fluid=True)


def financeiro_layout():
    return dbc.Container([
        html.H3("💰 Gestão Financeira do Lote", className="text-center mb-3"),

        dcc.Dropdown(
            id="dropdown-lote-financeiro",
            options=get_all_lots(),
            placeholder="Selecione um Lote para gerenciar as finanças",
            className="mb-3"
        ),

        html.Hr(),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Registrar Custo"),
                dbc.CardBody([
                    dcc.DatePickerSingle(id='custo-data', date=pd.to_datetime('today'), display_format='DD/MM/YYYY', className="d-block mb-2"),
                    dbc.Input(id='custo-tipo', placeholder='Tipo de Custo (ex: Ração)', className="mb-2"),
                    dbc.Textarea(id='custo-descricao', placeholder='Descrição (opcional)', className="mb-2"),
                    dbc.Input(id='custo-valor', type='number', placeholder='Valor (R$)', className="mb-2"),
                    dbc.Button('Salvar Custo', id='btn-custo-submit', color='danger', disabled=True, className="w-100"),
                    html.Div(id='custo-submit-status', className='mt-2')
                ])
            ]), xs=12, md=6, className="mb-4"),

            dbc.Col(dbc.Card([
                dbc.CardHeader("Registrar Receita"),
                dbc.CardBody([
                    dcc.DatePickerSingle(id='receita-data', date=pd.to_datetime('today'), display_format='DD/MM/YYYY', className="d-block mb-2"),
                    dbc.Input(id='receita-tipo', placeholder='Tipo de Receita (ex: Venda)', className="mb-2"),
                    dbc.Textarea(id='receita-descricao', placeholder='Descrição (opcional)', className="mb-2"),
                    dbc.Input(id='receita-valor', type='number', placeholder='Valor (R$)', className="mb-2"),
                    dbc.Button('Salvar Receita', id='btn-receita-submit', color='success', disabled=True, className="w-100"),
                    html.Div(id='receita-submit-status', className='mt-2')
                ])
            ]), xs=12, md=6, className="mb-4"),
        ]),

        html.Hr(),
        html.H4("Resumo Financeiro do Lote", className="text-center"),
        dbc.Spinner(html.Div(id='financeiro-resumo-div'))
    ], fluid=True)


def treat_layout():
    return dbc.Container([
        html.H3("💊 Registro de Tratamentos", className="text-center mb-3"),

        dcc.Dropdown(id="dropdown-lote-treat", options=get_active_lots(), placeholder="Selecione um Lote Ativo", className="mb-3"),

        dbc.Row([
            dbc.Col([dbc.Label("Medicação"), dbc.Input(id="treat-medicacao", type="text")], xs=12, md=4, className="mb-2"),
            dbc.Col([dbc.Label("Início"), dcc.DatePickerSingle(id="treat-inicio", display_format="DD/MM/YYYY")], xs=6, md=4, className="mb-2"),
            dbc.Col([dbc.Label("Término"), dcc.DatePickerSingle(id="treat-termino", display_format="DD/MM/YYYY")], xs=6, md=4, className="mb-2")
        ]),

        dbc.Row([
            dbc.Col([dbc.Label("Período de Carência (dias)"), dbc.Input(id="treat-carencia", type="number", min=0, value=0)], xs=12, md=4, className="mb-3"),
            dbc.Col([dbc.Label("Forma de Administração"), dbc.Input(id="treat-forma", type="text")], xs=12, md=4, className="mb-3"),
            dbc.Col([dbc.Label("Motivação"), dbc.Textarea(id="treat-motivo")], xs=12, md=4, className="mb-3"),
        ]),

        dbc.Button("Registrar Tratamento", id="btn-treat-submit", color="primary", disabled=True, className="w-100"),
        html.Div(id="treat-submit-status", className="mt-2"),

        html.Hr(),
        html.H4("Histórico de Tratamentos do Lote", className="text-center"),
        dbc.Spinner(dash_table.DataTable(id='treatments-history-table', style_cell={'textAlign': 'left'}, style_header={'fontWeight': 'bold'}))
    ], fluid=True)


def reports_layout():
    return dbc.Container([
        html.H3("📄 Gerar Relatório em PDF", className="text-center mb-3"),

        dcc.Dropdown(id="dropdown-lote-report", options=get_all_lots(), placeholder="Selecione um lote para o relatório", className="mb-3"),

        dbc.Button("Gerar Relatório PDF", id="btn-generate-report", color="success", disabled=True, className="w-100"),

        html.Div(id="report-generation-status", className="mt-3 text-center"),
        dcc.Download(id="download-pdf-report")
    ], fluid=True)


def metas_layout():
    return dbc.Container([
        html.H3("🎯 Gestão de Padrões de Linhagem", className="text-center mb-3"),
        html.P("Cadastre os valores de referência semanais para cada linhagem de ave.", className="text-center"),

        dbc.Row([
            # Formulário
            dbc.Col(dbc.Card([
                dbc.CardHeader("Cadastrar ou Atualizar Padrão Semanal"),
                dbc.CardBody([
                    dbc.Input(id="meta-linhagem", placeholder="Nome da Linhagem", className="mb-2"),
                    dbc.Input(id="meta-semana", type="number", min=1, placeholder="Semana de Idade", className="mb-2"),
                    dbc.Input(id="meta-peso", type="number", placeholder="Peso Médio (g)", className="mb-2"),
                    dbc.Input(id="meta-consumo-dia", type="number", placeholder="Consumo Ave/Dia (g)", className="mb-2"),
                    dbc.Input(id="meta-consumo-acum", type="number", placeholder="Consumo Acumulado (g)", className="mb-2"),
                    dbc.Input(id="meta-mortalidade-acum", type="number", placeholder="Mortalidade Acumulada (%)", className="mb-2"),
                    dbc.Button("Salvar Padrão", id="btn-meta-submit", color="primary", className="w-100"),
                    html.Div(id="meta-submit-status", className="mt-2")
                ])
            ]), xs=12, md=4, className="mb-4"),

            # Tabela
            dbc.Col([
                html.H5("Padrões Cadastrados"),
                dcc.Dropdown(id="dropdown-linhagem-filter", placeholder="Filtrar por Linhagem...", className="mb-2"),
                dbc.Spinner(html.Div(id="metas-table-div"))
            ], xs=12, md=8)
        ])
    ], fluid=True)


def producao_layout():
    return dbc.Container([
        html.H3("🥚 Registro de Produção de Ovos", className="text-center mb-3"),

        dcc.Dropdown(
            id="dropdown-lote-producao",
            options=get_active_lots(),
            placeholder="Selecione um Lote Ativo",
            className="mb-3"
        ),

        dbc.Row([
            dbc.Col([
                dbc.Label("Data da Produção"),
                dcc.DatePickerSingle(
                    id="producao-data",
                    date=pd.to_datetime("today"),
                    display_format="DD/MM/YYYY",
                    className="d-block"
                )
            ], xs=12, md=4, className="mb-3"),

            dbc.Col([
                dbc.Label("Total de Ovos Produzidos"),
                dbc.Input(id="producao-total-ovos", type="number", min=0)
            ], xs=12, md=4, className="mb-3"),

            dbc.Col([
                dbc.Label("Ovos Quebrados/Trincados"),
                dbc.Input(id="producao-ovos-quebrados", type="number", min=0, value=0)
            ], xs=12, md=4, className="mb-3"),
        ]),

        dbc.Button("Salvar Produção", id="btn-producao-submit", color="primary", disabled=True, className="w-100"),
        html.Div(id="producao-submit-status", className="mt-2"),

        html.Hr(className="my-4"),
        html.H4("Produção do Mês Atual", className="text-center"),
        dbc.Spinner(html.Div(id='producao-table-div')),  # MÊS ATUAL

        html.Hr(className="my-4"),
        html.H4("Resumo dos Últimos 3 Meses (Excluindo o Atual)", className="text-center"),
        dbc.Spinner(html.Div(id='producao-resumo-mensal'))  # TABELA RESUMO
    ], fluid=True)



def create_layout():
    navbar = dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("Dashboard de Gestão de Avicultura", className="ms-2 fw-bold"),

            # Itens visíveis apenas no DESKTOP
            dbc.Nav(
                [
                    dbc.NavLink("Sair", href="/logout", className="text-white"),
                ],
                className="d-none d-md-flex"  # Esconde no mobile
            ),

            # Menu hambúrguer para MOBILE
            dbc.DropdownMenu(
                children=[
                    dbc.DropdownMenuItem("Sair", href="/logout"),
                ],
                nav=True,
                in_navbar=True,
                label="☰ Menu",
                className="d-md-none text-white fw-bold"
            )
        ], fluid=True),
        color="primary",
        dark=True,
        className="mb-3"
    )

    # Tabs com scroll horizontal em mobile
    tabs = dcc.Tabs(
        id="tabs",
        value="tab-view",
        children=[
            dcc.Tab(label="Visão Geral", value="tab-view"),
            dcc.Tab(label="Gestão de Lotes", value="tab-lotes"),
            dcc.Tab(label="Produção", value="tab-producao"),
            dcc.Tab(label="Peso & Mortalidade", value="tab-insert-weekly"),
            dcc.Tab(label="Qualidade da Água", value="tab-agua"),
            dcc.Tab(label="Financeiro", value="tab-financeiro"),
            dcc.Tab(label="Tratamentos", value="tab-treat"),
            dcc.Tab(label="Padrões (Metas)", value="tab-metas"),
            dcc.Tab(label="Relatórios", value="tab-reports"),
        ],
        style={"overflowX": "auto", "whiteSpace": "nowrap"}  # ✅ Faz o scroll horizontal em mobile
    )

    return html.Div([
        dcc.Store(id='store-active-lotes', data=get_active_lots()),
        dcc.Interval(id='interval-alerts', interval=60 * 1000, n_intervals=0),

        navbar,   # ✅ Navbar responsivo
        tabs,     # ✅ Tabs com scroll em mobile
        html.Div(id="tab-content", style={"padding": "1rem"})
    ])

def layout_public_lote(lote_id: int):
    """
    Layout público (somente leitura) para o Lote.
    Conteúdo: Produção, Mortalidade e Tratamentos.
    SEM navbar/tabs; acesso direto via /public/lote/<id>.
    """
    return dbc.Container([
        dcc.Store(id="public-store-lote-id", data=lote_id),

        html.Div([
            html.H3(f"📌 Lote {lote_id} — Visualização Pública (Somente Leitura)", className="mb-2"),
            html.P("Esta é uma página de acesso público. Edição desabilitada.", className="text-muted"),
        ], className="mt-3 mb-3"),

        html.Hr(),

        html.H4("📊 Produção (últimos 180 dias)"),
        dbc.Spinner(dcc.Graph(id="public-graph-producao", config={"responsive": True}, style={"width": "100%"}), size="sm"),
        dbc.Spinner(html.Div(id="public-table-producao"), size="sm"),

        html.Hr(className="my-4"),

        html.H4("📉 Mortalidade & Desempenho (últimos 180 dias)"),
        dbc.Spinner(dcc.Graph(id="public-graph-mortalidade", config={"responsive": True}, style={"width": "100%"}), size="sm"),

        html.Hr(className="my-4"),

        html.H4("🩺 Tratamentos (últimos 180 dias)"),
        dbc.Spinner(html.Div(id="public-table-trat"), size="sm"),

        html.Hr(className="my-4"),
        html.P("© SGA - Visualização pública gerada automaticamente.", className="text-muted")
    ], fluid=True)


def agua_layout():
    return dbc.Container([
        html.H3("💧 Qualidade da Água — Registro Diário", className="text-center mb-3"),

        dcc.Dropdown(
            id="dropdown-lote-agua",
            options=get_active_lots(),
            placeholder="Selecione um Lote Ativo",
            className="mb-3"
        ),

        dbc.Row([
            dbc.Col([
                dbc.Label("Data da Medição"),
                dcc.DatePickerSingle(
                    id="agua-data",
                    date=pd.to_datetime("today"),
                    display_format="DD/MM/YYYY",
                    className="d-block"
                )
            ], xs=12, md=4, className="mb-3"),

            dbc.Col([
                dbc.Label("pH"),
                dbc.Input(id="agua-ph", type="number", step="0.01", min=0, max=14, placeholder="Ex.: 7.20")
            ], xs=12, md=4, className="mb-3"),

            dbc.Col([
                dbc.Label("Alcalinidade (ppm)"),
                dbc.Input(id="agua-alc", type="number", min=0, placeholder="Ex.: 120")
            ], xs=12, md=4, className="mb-3"),
        ]),

        dbc.Button("Salvar Registro", id="btn-agua-submit", color="primary", disabled=True, className="w-100"),
        html.Div(id="agua-submit-status", className="mt-2"),

        html.Hr(className="my-4"),
        html.H4("Tendência (últimos 30 dias)", className="text-center"),
        dbc.Spinner(dcc.Graph(id="agua-graph", config={"responsive": True}, style={"width": "100%"}), size="sm"),

        html.Hr(className="my-4"),
        html.H4("Histórico (últimos 30 dias)", className="text-center"),
        dbc.Spinner(html.Div(id="agua-table-div"), size="sm")
    ], fluid=True)
