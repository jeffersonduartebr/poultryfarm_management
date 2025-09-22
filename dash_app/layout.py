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
        html.H3("🛠️ Gestão de Lotes"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Cadastrar Novo Lote"),
                dbc.CardBody([
                    dbc.Input(id="lote-identificador", placeholder="Identificador do Lote (Ex: Lote 2025-A)", className="mb-2"),
                    dbc.Input(id="lote-linhagem", placeholder="Linhagem (Ex: Cobb, Ross)", className="mb-2"),
                    dbc.Input(id="lote-aviario", placeholder="Aviário Alocado", className="mb-2"),
                    dcc.DatePickerSingle(id="lote-data", date=pd.to_datetime("today"), display_format="DD/MM/YYYY", className="mb-2 d-block"),
                    dbc.Input(id="lote-aves", type="number", placeholder="Nº de Aves Alojadas", className="mb-2"),
                    dbc.Button("Salvar Novo Lote", id="btn-lote-submit", color="primary"),
                    html.Div(id="lote-submit-status", className="mt-2")
                ])
            ]), width=5),
            dbc.Col([
                html.H5("Lotes Registrados"),
                dbc.Spinner(html.Div(id="lotes-table-div")),
                dbc.Button("Finalizar Lote Selecionado", id="btn-lote-finalize", color="warning", className="mt-2", disabled=True)
            ], width=7)
        ]),
    ], fluid=True)

def view_layout():
    lotes_options = get_all_lots()
    if not lotes_options:
        return dbc.Alert("Nenhum lote encontrado. Cadastre um lote na aba 'Gestão de Lotes'.", color="info")
    return html.Div([
        html.H3("📊 Indicadores de Desempenho do Lote"),
        dbc.Row([
            dbc.Col(dcc.Dropdown(id="dropdown-lote-indicadores", options=lotes_options, placeholder="Selecione um lote para visualizar"), width=6)
        ], className="mb-4", justify="center"),
        html.Hr(),
        dbc.Row([
            dbc.Col(dbc.Spinner(dcc.Graph(id="graph-peso-medio")), width=6),
            dbc.Col(dbc.Spinner(dcc.Graph(id="graph-mortalidade-acumulada")), width=6)
        ]),
        dbc.Row([
            dbc.Col(dbc.Spinner(dcc.Graph(id="graph-consumo-comparativo")), width=6),
            dbc.Col(dbc.Spinner(dcc.Graph(id="graph-conversao-alimentar")), width=6)
        ])
    ])

def insert_weekly_layout():
    return dbc.Container([
        html.H3("📝 Inserir Dados Semanais do Lote"),
        dcc.Dropdown(id="dropdown-lote-weekly", options=get_active_lots(), placeholder="Selecione um Lote Ativo", className="mb-3"),
        html.Div(id='weekly-form-div', children=[
            dbc.Row([
                dbc.Col([dbc.Label("Semana (idade)"), dbc.Input(id="input-semana", type="number", min=1, disabled=True)], width=3),
                dbc.Col([dbc.Label("N° aves na semana"), dbc.Input(id="input-aves-semana", type="number", disabled=True)], width=3),
                dbc.Col([dbc.Label("Data de Pesagem"), dcc.DatePickerSingle(id="input-data-pesagem", date=pd.to_datetime("today"), display_format="DD/MM/YYYY")], width=3)
            ], className="mb-3"),
            html.H5("Mortalidades da Semana"),
            dbc.Row([*[dbc.Col(dbc.Input(id=f"input-mort-dia-{i}", type="number", value=0, placeholder=f"Dia {i}"), width=1) for i in range(1, 8)],
                     dbc.Col([dbc.Label("Total Semana"), dbc.Input(id="input-mort-total", type="number", disabled=True)], width=2)], className="mb-3"),
            html.H5("Desempenho da Semana"),
            dbc.Row([
                dbc.Col([dbc.Label("Peso médio (g)"), dbc.Input(id="input-peso-med", type="number")], width=4),
                dbc.Col([dbc.Label("Consumo Real (g/ave/dia)"), dbc.Input(id="input-consumo-real", type="number")], width=4)
            ], className="mb-3"),
            dbc.Button("Enviar Semana", id="btn-submit-weekly", color="primary"),
            html.Div(id="submit-status-weekly", className="mt-2")
        ], style={'display': 'none'})
    ], fluid=True)

def financeiro_layout():
    return dbc.Container([
        html.H3("💰 Gestão Financeira do Lote"),
        dcc.Dropdown(id="dropdown-lote-financeiro", options=get_all_lots(), placeholder="Selecione um Lote para gerenciar as finanças", className="mb-3"),
        html.Hr(),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Registrar Custo"),
                dbc.CardBody([
                    dcc.DatePickerSingle(id='custo-data', date=pd.to_datetime('today'), display_format='DD/MM/YYYY', className="mb-2 d-block"),
                    dbc.Input(id='custo-tipo', placeholder='Tipo de Custo (ex: Ração)', className="mb-2"),
                    dbc.Textarea(id='custo-descricao', placeholder='Descrição (opcional)', className="mb-2"),
                    dbc.Input(id='custo-valor', type='number', placeholder='Valor (R$)', className="mb-2"),
                    dbc.Button('Salvar Custo', id='btn-custo-submit', color='danger', disabled=True),
                    html.Div(id='custo-submit-status', className='mt-2')
                ])
            ]), width=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Registrar Receita"),
                dbc.CardBody([
                    dcc.DatePickerSingle(id='receita-data', date=pd.to_datetime('today'), display_format='DD/MM/YYYY', className="mb-2 d-block"),
                    dbc.Input(id='receita-tipo', placeholder='Tipo de Receita (ex: Venda)', className="mb-2"),
                    dbc.Textarea(id='receita-descricao', placeholder='Descrição (opcional)', className="mb-2"),
                    dbc.Input(id='receita-valor', type='number', placeholder='Valor (R$)', className="mb-2"),
                    dbc.Button('Salvar Receita', id='btn-receita-submit', color='success', disabled=True),
                    html.Div(id='receita-submit-status', className='mt-2')
                ])
            ]), width=6)
        ]),
        html.Hr(),
        html.H4("Resumo Financeiro do Lote"),
        dbc.Spinner(html.Div(id='financeiro-resumo-div'))
    ], fluid=True)

def treat_layout():
    return dbc.Container([
        html.H3("💊 Registro de Tratamentos"),
        dcc.Dropdown(id="dropdown-lote-treat", options=get_active_lots(), placeholder="Selecione um Lote Ativo", className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Medicação"), width=2), dbc.Col(dbc.Input(id="treat-medicacao", type="text"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Início"), width=2), dbc.Col(dcc.DatePickerSingle(id="treat-inicio", display_format="DD/MM/YYYY"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Término"), width=2), dbc.Col(dcc.DatePickerSingle(id="treat-termino", display_format="DD/MM/YYYY"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Período de Carência (dias)"), width=2), dbc.Col(dbc.Input(id="treat-carencia", type="number", min=0, value=0), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Forma de Admin."), width=2), dbc.Col(dbc.Input(id="treat-forma", type="text"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Motivação"), width=2), dbc.Col(dbc.Textarea(id="treat-motivo"), width=6)], className="mb-3"),
        dbc.Button("Registrar Tratamento", id="btn-treat-submit", color="primary", disabled=True),
        html.Div(id="treat-submit-status", className="mt-2"),
        html.Hr(),
        html.H4("Histórico de Tratamentos do Lote"),
        dbc.Spinner(dash_table.DataTable(id='treatments-history-table', style_cell={'textAlign': 'left'}, style_header={'fontWeight': 'bold'}))
    ], fluid=True)

def reports_layout():
    return dbc.Container([
        html.H3("📄 Gerar Relatório em PDF"),
        dcc.Dropdown(id="dropdown-lote-report", options=get_all_lots(), placeholder="Selecione um lote para o relatório", className="mb-3"),
        dbc.Button("Gerar Relatório PDF", id="btn-generate-report", color="success", disabled=True),
        html.Div(id="report-generation-status", className="mt-3"),
        dcc.Download(id="download-pdf-report")
    ], fluid=True)

def metas_layout():
    return dbc.Container([
        html.H3("🎯 Gestão de Padrões de Linhagem"),
        html.P("Cadastre os valores de referência semanais para cada linhagem de ave."),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Cadastrar ou Atualizar Padrão Semanal"),
                dbc.CardBody([
                    dbc.Input(id="meta-linhagem", placeholder="Nome da Linhagem", className="mb-2"),
                    dbc.Input(id="meta-semana", type="number", min=1, placeholder="Semana de Idade", className="mb-2"),
                    dbc.Input(id="meta-peso", type="number", placeholder="Peso Médio (g)", className="mb-2"),
                    dbc.Input(id="meta-consumo-dia", type="number", placeholder="Consumo Ave/Dia (g)", className="mb-2"),
                    dbc.Input(id="meta-consumo-acum", type="number", placeholder="Consumo Acumulado (g)", className="mb-2"),
                    dbc.Input(id="meta-mortalidade-acum", type="number", placeholder="Mortalidade Acumulada (%)", className="mb-2"),
                    dbc.Button("Salvar Padrão", id="btn-meta-submit", color="primary"),
                    html.Div(id="meta-submit-status", className="mt-2")
                ])
            ]), width=4),
            dbc.Col([
                html.H5("Padrões Cadastrados"),
                dcc.Dropdown(id="dropdown-linhagem-filter", placeholder="Filtrar por Linhagem...", className="mb-2"),
                dbc.Spinner(html.Div(id="metas-table-div"))
            ], width=8)
        ])
    ], fluid=True)

def producao_layout():
    return dbc.Container([
        html.H3("🥚 Registro de Produção de Ovos"),
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
            ], width=4),
            dbc.Col([
                dbc.Label("Total de Ovos Produzidos"),
                dbc.Input(id="producao-total-ovos", type="number", min=0)
            ], width=4),
            dbc.Col([
                dbc.Label("Ovos Quebrados/Trincados"),
                dbc.Input(id="producao-ovos-quebrados", type="number", min=0, value=0)
            ], width=4),
        ], className="mb-3"),
        dbc.Button("Salvar Produção", id="btn-producao-submit", color="primary", disabled=True),
        html.Div(id="producao-submit-status", className="mt-2"),
        html.Hr(className="my-4"),
        html.H4("Últimos 7 Dias de Produção Registrada"),
        dbc.Spinner(html.Div(id="producao-table-div"))
    ], fluid=True)

def create_layout():
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dcc.Link("Sair", href="/logout", className="nav-link text-white"))
        ],
        brand="Dashboard de Gestão de Avicultura",
        color="primary",
        dark=True,
        className="mb-3"
    )

    return html.Div([
        dcc.Store(id='store-active-lotes', data=get_active_lots()),
        dcc.Interval(id='interval-alerts', interval=60 * 1000, n_intervals=0),
        navbar,
        dcc.Tabs(id="tabs", value="tab-view", children=[
            dcc.Tab(label="Visão Geral", value="tab-view"),
            dcc.Tab(label="Gestão de Lotes", value="tab-lotes"),
            dcc.Tab(label="Produção", value="tab-producao"),
            dcc.Tab(label="Peso e mortalidade", value="tab-insert-weekly"),
            dcc.Tab(label="Financeiro", value="tab-financeiro"),
            dcc.Tab(label="Tratamentos", value="tab-treat"),
            dcc.Tab(label="Padrões (Metas)", value="tab-metas"),
            dcc.Tab(label="Relatórios", value="tab-reports"),
        ]),
        html.Div(id="tab-content", style={"padding": "1rem"})
    ])

