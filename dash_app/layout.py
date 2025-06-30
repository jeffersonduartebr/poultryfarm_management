import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
import plotly.graph_objects as go
from sqlalchemy import text
from db import get_engine

engine = get_engine()

def insert_weekly_layout():
    return dbc.Container([
        html.H3("📝 Inserir Dados da Semana"),
        dbc.Row([
            dbc.Col(dbc.Label("Aviário"), width=2),
            dbc.Col(dbc.Input(id="input-aviario", placeholder="Aviário 01"), width=1),
            dbc.Col(dbc.Label("N° aves alojadas"), width=1),
            dbc.Col(dbc.Input(id="input-n-aves", type="number", value=690), width=1),
            dbc.Col(dbc.Label("Peso médio chegada (g)"), width=1),
            dbc.Col(dbc.Input(id="input-peso-medio", type="number", value=466), width=1),
        ], className="mb-4", align="end"),
        html.H5("Mortalidades da Semana"),
        dbc.Row([
            dbc.Col(dbc.Label("Semana (idade)"), width=2),
            dbc.Col(dbc.Input(id="input-semana", type="number", min=1), width=1),
            dbc.Col(dbc.Label("N° aves na semana"), width=2),
            dbc.Col(dbc.Input(id="input-aves-semana", type="number"), width=1),
        ], className="mb-4", align="center"),
        dbc.Row([
            *[dbc.Col(html.Div([dbc.Label(f"Dia {i}"), dbc.Input(id=f"input-mort-dia-{i}", type="number", value=0)]), width=1) for i in range(1, 8)],
            dbc.Label("Mortalidade total"),
            dbc.Col(dbc.Input(id="input-mort-total", type="number", disabled=True), width=1),
            dbc.Label("Mortalidade acumulada"),
            dbc.Col(dbc.Input(id="input-mort-acum", type="number", step=0.01, disabled=True), width=1),
        ], className="mb-4", align="center"),
        html.H5("Peso Corporal em Gramas"),
        dbc.Row([
            dbc.Col(dbc.Label("Data de Pesagem"), width=1),
            dbc.Col(dcc.DatePickerSingle(id="input-data-pesagem", date=pd.to_datetime("today"), display_format="DD/MM/YYYY"), width=2),
            dbc.Col(dbc.Label("Peso médio"), width=1),
            dbc.Col(dbc.Input(id="input-peso-med", type="number"), width=1),
            dbc.Col(dbc.Label("Mínimo"), width=1),
            dbc.Col(dbc.Input(id="input-peso-min", type="number"), width=1),
            dbc.Col(dbc.Label("Máximo"), width=1),
            dbc.Col(dbc.Input(id="input-peso-max", type="number"), width=1),
        ], className="mb-4", align="end"),
        html.H5("Consumo de Ração (g)"),
        dbc.Row([
            dbc.Col(dbc.Label("Média (REAL)"), width=1),
            dbc.Col(dbc.Input(id="input-consumo-real", type="number"), width=1),
            dbc.Col(dbc.Label("Média (PADRÃO)"), width=1),
            dbc.Col(dbc.Input(id="input-consumo-padrao", type="text"), width=1),
            dbc.Col(dbc.Label("Acum. (REAL)"), width=1),
            dbc.Col(dbc.Input(id="input-consumo-acum-real", type="number", disabled=True), width=1),
            dbc.Col(dbc.Label("Acum. (PADRÃO)"), width=1),
            dbc.Col(dbc.Input(id="input-consumo-acum-padrao", type="number", disabled=True), width=1),
        ], className="mb-4", align="end"),
        dbc.Button("Enviar Semana", id="btn-submit-weekly", color="primary"),
        html.Div(id="submit-status-weekly", style={"marginTop": 20})
    ], fluid=True)

def view_layout():
    try:
        with engine.connect() as conn:
            aviarios = pd.read_sql("SELECT DISTINCT aviario FROM producao_aves", conn)['aviario'].dropna().tolist()
    except Exception as e:
        print(f"Erro ao buscar aviarios: {e}")
        aviarios = []
        
    if not aviarios:
        return dbc.Alert("Nenhum aviário encontrado na base de dados para exibir indicadores.", color="warning")

    return html.Div([
        html.H3("Indicadores da Criação"),
        dbc.Row([
            dbc.Col(dbc.Label("Selecionar Aviário"), width="auto"),
            dbc.Col(dcc.Dropdown(id="dropdown-aviario-indicadores", options=[{"label": av, "value": av} for av in aviarios], placeholder="Selecione um aviário"), width=3)
        ], className="mb-4", align="center"),
        html.Hr(),
        dbc.Spinner(dcc.Graph(id="graph-peso-medio"), color="primary"),
        dbc.Spinner(dcc.Graph(id="graph-mortalidade"), color="danger"),
        dbc.Spinner(dcc.Graph(id="graph-consumo"), color="success"),
        dbc.Spinner(dcc.Graph(id="graph-mortalidade-acumulada"), color="secondary"),
        dbc.Spinner(dcc.Graph(id="graph-consumo-comparativo"), color="info")
    ])

def insert_daily_layout():
    return dbc.Container([
        html.H3("🐔 Produção Diária de Ovos"),
        dbc.Row([dbc.Col(dbc.Label("Data"), width=2), dbc.Col(dcc.DatePickerSingle(id="daily-date", date=pd.to_datetime("today"), display_format="DD/MM/YYYY"), width=3)], className="mb-3", align="center"),
        dbc.Row([dbc.Col(dbc.Label("Aviário"), width=1), dbc.Col(dbc.Input(id="daily-aviario", type="text", placeholder="ex. 1"), width=1)], className="mb-3", align="center"),
        dbc.Row([dbc.Col(dbc.Label("Total de aves"), width=1), dbc.Col(dbc.Input(id="daily-total-birds", type="number", value=0), width=1)], className="mb-3", align="center"),
        html.Br(),
        dbc.Row([
            dbc.Col(dbc.Label("Total de ovos"), width=1), dbc.Col(dbc.Input(id="daily-total-eggs", type="number", value=0), width=1),
            dbc.Col(dbc.Label("Produção (%)"), width=1), dbc.Col(dbc.Input(id="daily-pct", type="number", step=0.01, disabled=True), width=1),
        ], className="mb-3", align="center"),
        dbc.Button("Enviar Produção Diária", id="btn-daily-submit", color="primary"),
        html.Div(id="daily-submit-status", style={"marginTop": "1rem"}),
        html.Hr(),
        html.H4("📈 Produção dos Últimos 7 Dias"),
        dbc.Spinner(dcc.Graph(id="graph-7d-eggs"), color="info")
    ], fluid=True)

def bedding_layout():
    return dbc.Container([
        html.H3("🛏️ Registro de Camas"),
        dbc.Row([dbc.Col(dbc.Label("Data de alojamento"), width=2), dbc.Col(dcc.DatePickerSingle(id="bed-date-lot", date=pd.to_datetime("today"), display_format="DD/MM/YYYY"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Data de implantação"), width=2), dbc.Col(dcc.DatePickerSingle(id="bed-date-implant", display_format="DD/MM/YYYY"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Material utilizado"), width=2), dbc.Col(dbc.Input(id="bed-material", type="text"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Data de retirada"), width=2), dbc.Col(dcc.DatePickerSingle(id="bed-date-remove", display_format="DD/MM/YYYY"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Tratamento"), width=2), dbc.Col(dbc.Input(id="bed-treatment", type="text"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Destino da cama"), width=2), dbc.Col(dbc.Input(id="bed-destination", type="text"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Contato do comprador"), width=2), dbc.Col(dbc.Input(id="bed-contact", type="text"), width=3)], className="mb-3"),
        dbc.Button("Enviar Registro", id="btn-bed-submit", color="primary"),
        html.Div(id="bed-submit-status", style={"marginTop": "1rem"})
    ], fluid=True)

def bait_layout():
    return dbc.Container([
        html.H3("🪤 Inspeção de Iscas"),
        dbc.Row([
            dbc.Col([dbc.Label("Nº da Isca"), dbc.Input(id="field-n_isca", type="number", min=1)], width=2),
            dbc.Col([dbc.Label("Produto"), dbc.Input(id="field-produto", type="text")], width=3),
            dbc.Col([dbc.Label("Local"), dbc.Input(id="field-local", type="text")], width=3),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([dbc.Label("Data da Vistoria"), dcc.DatePickerSingle(id="field-data-vistoria", display_format="DD/MM/YYYY")], width='auto'),
            dbc.Col([dbc.Label("Consumida"), dbc.Input(id="field-consumida", type="number", min=0)], width=1),
            dbc.Col([dbc.Label("Intacta"), dbc.Input(id="field-intacta", type="number", min=0)], width=1),
            dbc.Col([dbc.Label("Mofada"), dbc.Input(id="field-mofada", type="number", min=0)], width=1),
            dbc.Col([dbc.Label("Responsável"), dbc.Input(id="field-responsavel", type="text")], width=3),
        ], className="mb-3"),
        dbc.Button("Enviar Inspeção", id="btn-bait-submit", color="primary"),
        html.Div(id="bait-submit-status", style={"marginTop": "1rem"}),
        html.Hr(),
        html.H4("Últimas 5 Inspeções", className="my-3"),
        dbc.Spinner(dash_table.DataTable(id='bait-history-table', style_cell={'textAlign': 'left'}, style_header={'fontWeight': 'bold'}))
    ], fluid=True)

def visits_layout():
    return dbc.Container([
        html.H3("📝 Registro de Visitas"),
        dbc.Row([dbc.Col(dbc.Label("Data"), width=2), dbc.Col(dcc.DatePickerSingle(id="visit-date", display_format="DD/MM/YYYY"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Objetivo"), width=2), dbc.Col(dbc.Textarea(id="visit-objetivo"), width=6)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Contato"), width=2), dbc.Col(dbc.Input(id="visit-contato", type="text"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Placa Veículo"), width=2), dbc.Col(dbc.Input(id="visit-placa", type="text"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Assinatura"), width=2), dbc.Col(dbc.Input(id="visit-assinatura", type="text"), width=3)], className="mb-3"),
        dbc.Button("Registrar Visita", id="btn-visits-submit", color="primary"),
        html.Div(id="visits-submit-status", style={"marginTop": "1rem"}),
        html.Hr(),
        html.H4("Últimas 5 Visitas", className="my-3"),
        dbc.Spinner(dash_table.DataTable(id='visits-history-table', style_cell={'textAlign': 'left'}, style_header={'fontWeight': 'bold'}))
    ], fluid=True)

def treat_layout():
    return dbc.Container([
        html.H3("💊 Registro de Tratamentos"),
        dbc.Row([dbc.Col(dbc.Label("Aviário"), width=2), dbc.Col(dbc.Input(id="treat-aviario", type="text"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Medicação"), width=2), dbc.Col(dbc.Input(id="treat-medicacao", type="text"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Início"), width=2), dbc.Col(dcc.DatePickerSingle(id="treat-inicio", display_format="DD/MM/YYYY"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Término"), width=2), dbc.Col(dcc.DatePickerSingle(id="treat-termino", display_format="DD/MM/YYYY"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Forma de Admin."), width=2), dbc.Col(dbc.Input(id="treat-forma", type="text"), width=3)], className="mb-3"),
        dbc.Row([dbc.Col(dbc.Label("Motivação"), width=2), dbc.Col(dbc.Textarea(id="treat-motivo"), width=6)], className="mb-3"),
        dbc.Button("Registrar Tratamento", id="btn-treat-submit", color="primary"),
        html.Div(id="treat-submit-status", style={"marginTop": "1rem"}),
        html.Hr(),
        html.H4("Últimos 5 Tratamentos", className="my-3"),
        dbc.Spinner(dash_table.DataTable(id='treatments-history-table', style_cell={'textAlign': 'left'}, style_header={'fontWeight': 'bold'}))
    ], fluid=True)

def reports_layout():
    report_options = [
        {'label': 'Indicadores da Criação', 'value': 'tab-view'},
        {'label': 'Inspeção de Iscas (Histórico)', 'value': 'tab-bait'},
        {'label': 'Registro de Visitas (Histórico)', 'value': 'tab-visits'},
        {'label': 'Registro de Tratamentos (Histórico)', 'value': 'tab-treat'}
    ]
    return dbc.Container([
        html.H3("📄 Gerar Relatório em PDF"),
        html.P("Selecione as seções que deseja incluir no relatório PDF."),
        dbc.Row([dbc.Col(dcc.Checklist(id='report-sections-checklist', options=report_options, value=['tab-view'], labelStyle={'display': 'block'}), width=6)], className="my-4"),
        dbc.Spinner(dbc.Button("Gerar Relatório PDF", id="btn-generate-report", color="success")),
        html.Div(id="report-generation-status", className="mt-3"),
        dcc.Download(id="download-pdf-report")
    ], fluid=True)

def create_layout():
    return html.Div([
        dcc.Store(id='app-memory', storage_type='session'),
        dcc.Tabs(id="tabs", value="tab-insert-weekly", children=[
            dcc.Tab(label="Inserir Dados Semanais", value="tab-insert-weekly"),
            dcc.Tab(label="Visualizar Indicadores", value="tab-view"),
            dcc.Tab(label="Produção Diária de Ovos", value="tab-insert-daily"),
            dcc.Tab(label="Registro de Camas", value="tab-bedding"),
            dcc.Tab(label="Inspeção de Iscas", value="tab-bait"),
            dcc.Tab(label="Registro de Visitas", value="tab-visits"),
            dcc.Tab(label="Registro de Tratamentos", value="tab-treat"),
            dcc.Tab(label="Relatórios", value="tab-reports"),
        ]),
        html.Div(id="tab-content", style={"padding": "1rem"})
    ])