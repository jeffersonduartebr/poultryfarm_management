from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import text
from db import get_engine
import dash_bootstrap_components as dbc
import dash
from dash import html, dcc, dash_table
from flask_login import login_user
import base64
from weasyprint import HTML
from datetime import datetime, timedelta

from user_management import get_user_by_username
from layout import (view_layout, lotes_layout, insert_weekly_layout,
                    financeiro_layout, treat_layout, metas_layout, reports_layout,
                    producao_layout, get_distinct_linhagens)

def register_callbacks(app):
    @app.callback(Output('tab-content', 'children'), Input('tabs', 'value'))
    def render_content(tab):
        layouts = {
            'tab-view': view_layout, 'tab-lotes': lotes_layout,
            'tab-insert-weekly': insert_weekly_layout,
            'tab-producao': producao_layout,  
            'tab-financeiro': financeiro_layout,
            'tab-treat': treat_layout, 'tab-metas': metas_layout, 'tab-reports': reports_layout
        }
        return layouts.get(tab, lambda: html.H3("Página não encontrada"))()

    # --- CALLBACK DE LOGIN ---
    @app.callback(
        [Output('url', 'pathname', allow_duplicate=True),
         Output('login-alert-div', 'children')],
        Input('login-button', 'n_clicks'),
        [State('login-username', 'value'),
         State('login-password', 'value')],
        prevent_initial_call=True
    )
    def login_callback(n_clicks, username, password):
        if not username or not password:
            return dash.no_update, dbc.Alert("Usuário e senha são obrigatórios.", color="warning")

        user = get_user_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            return '/', None
        else:
            return dash.no_update, dbc.Alert("Credenciais inválidas.", color="danger")

    # --- CALLBACKS DE LOTES ---
    @app.callback(
        [Output("lote-submit-status", "children"), Output("store-active-lotes", "data")],
        Input("btn-lote-submit", "n_clicks"),
        [State("lote-identificador", "value"), State("lote-linhagem", "value"),
         State("lote-aviario", "value"), State("lote-data", "date"), State("lote-aves", "value"),
         State("store-active-lotes", "data")],
        prevent_initial_call=True
    )
    def insert_lote(n, identificador, linhagem, aviario, data, aves, current_lotes):
        if not all([identificador, data, aves]):
            return dbc.Alert("Identificador, Data e Nº de Aves são obrigatórios.", color="warning"), current_lotes
        try:
            engine = get_engine()
            with engine.begin() as conn:
                q = text("INSERT INTO lotes (identificador_lote, linhagem, aviario_alocado, data_alojamento, aves_alojadas, status) VALUES (:id, :lin, :avi, :dt, :aves, 'Ativo')")
                conn.execute(q, {"id": identificador, "lin": linhagem, "avi": aviario, "dt": data, "aves": aves})
            from layout import get_active_lots
            return dbc.Alert(f"Lote '{identificador}' cadastrado!", color="success"), get_active_lots()
        except Exception as e:
            return dbc.Alert(f"Erro: {e}", color="danger"), current_lotes

    @app.callback(
        Output("lotes-table-div", "children"),
        [Input("lote-submit-status", "children"), Input("tabs", "value")]
    )
    def update_lotes_table(status, tab):
        if tab != 'tab-lotes': raise PreventUpdate
        engine = get_engine()
        df = pd.read_sql("SELECT id, identificador_lote as 'Lote', linhagem as 'Linhagem', aviario_alocado as 'Aviário', data_alojamento as 'Data', aves_alojadas as 'Aves', status as 'Status' FROM lotes ORDER BY data_alojamento DESC", engine)
        return dash_table.DataTable(id='lotes-table', columns=[{"name": i, "id": i, "deletable": False} for i in df.columns], data=df.to_dict('records'), row_selectable="single", selected_rows=[])

    @app.callback(Output("btn-lote-finalize", "disabled"), Input("lotes-table", "selected_rows"))
    def toggle_finalize_button(selected_rows):
        return not selected_rows

    @app.callback(
        Output("lote-submit-status", "children", allow_duplicate=True),
        Input("btn-lote-finalize", "n_clicks"),
        State("lotes-table", "selected_rows"),
        State("lotes-table", "data"),
        prevent_initial_call=True
    )
    def finalize_lote(n, selected_rows, data):
        if not n or not selected_rows: raise PreventUpdate
        lote_id = data[selected_rows[0]]['id']
        engine = get_engine()
        try:
            with engine.begin() as conn:
                conn.execute(text("UPDATE lotes SET status = 'Finalizado' WHERE id = :id"), {"id": lote_id})
            return dbc.Alert(f"Lote ID {lote_id} finalizado.", color="info")
        except Exception as e:
            return dbc.Alert(f"Erro ao finalizar lote: {e}", color="danger")

    # --- CALLBACKS DE DADOS SEMANAIS ---
    @app.callback(
        [Output("weekly-form-div", "style"), Output("input-aves-semana", "value"), Output("input-semana", "value")],
        Input("dropdown-lote-weekly", "value"),
        prevent_initial_call=True
    )
    def show_and_fill_weekly_form(lote_id):
        if not lote_id: return {'display': 'none'}, None, None
        engine = get_engine()
        with engine.connect() as conn:
            aves_alojadas = conn.execute(text("SELECT aves_alojadas FROM lotes WHERE id = :id"), {"id": lote_id}).scalar() or 0
            mort_acumulada = conn.execute(text("SELECT COALESCE(SUM(mort_total), 0) FROM producao_aves WHERE lote_id = :id"), {"id": lote_id}).scalar() or 0
            ultima_semana = conn.execute(text("SELECT COALESCE(MAX(semana_idade), 0) FROM producao_aves WHERE lote_id = :id"), {"id": lote_id}).scalar() or 0
        aves_atuais = aves_alojadas - mort_acumulada
        proxima_semana = ultima_semana + 1
        return {'display': 'block'}, aves_atuais, proxima_semana

    @app.callback(Output("input-mort-total", "value"), [Input(f"input-mort-dia-{i}", "value") for i in range(1, 8)])
    def calc_mort_total(*dias):
        return sum(v or 0 for v in dias)

    @app.callback(
        Output("submit-status-weekly", "children"),
        Input("btn-submit-weekly", "n_clicks"),
        [State("dropdown-lote-weekly", "value"), State("input-semana", "value"), State("input-aves-semana", "value"),
         *[State(f"input-mort-dia-{i}", "value") for i in range(1, 8)],
         State("input-mort-total", "value"), State("input-data-pesagem", "date"), State("input-peso-med", "value"), State("input-consumo-real", "value")],
        prevent_initial_call=True
    )
    def insert_weekly_data(n, lote_id, semana, aves_semana, *args):
        if not lote_id or not semana: return dbc.Alert("Selecione um lote e informe a semana.", color="warning")
        
        mort_dias = args[:7]
        mort_total, dt_pesagem, peso_medio, consumo_real = args[7:]
        
        engine = get_engine()
        try:
            with engine.begin() as conn:
                q = text("INSERT INTO producao_aves (lote_id, semana_idade, aves_na_semana, mort_d1, mort_d2, mort_d3, mort_d4, mort_d5, mort_d6, mort_d7, mort_total, data_pesagem, peso_medio, consumo_real_ave_dia) VALUES (:lote_id, :sem, :aves, :d1, :d2, :d3, :d4, :d5, :d6, :d7, :mt, :dt_p, :pm, :cr)")
                params = {"lote_id": lote_id, "sem": semana, "aves": aves_semana, **{f"d{i+1}": d for i, d in enumerate(mort_dias)}, "mt": mort_total, "dt_p": dt_pesagem, "pm": peso_medio, "cr": consumo_real}
                conn.execute(q, params)
            return dbc.Alert("Dados da semana inseridos com sucesso!", color="success")
        except Exception as e:
            return dbc.Alert(f"Erro: {e}", color="danger")

    # --- CALLBACKS DE VISUALIZAÇÃO ---
    @app.callback(
        [Output("graph-peso-medio", "figure"), Output("graph-mortalidade-acumulada", "figure"),
         Output("graph-consumo-comparativo", "figure"), Output("graph-conversao-alimentar", "figure")],
        Input("dropdown-lote-indicadores", "value")
    )
    def update_indicadores_graphs(lote_id):
        if not lote_id: return go.Figure(), go.Figure(), go.Figure(), go.Figure()
        
        engine = get_engine()
        with engine.connect() as conn:
            df_prod = pd.read_sql(text("SELECT * FROM producao_aves WHERE lote_id = :id ORDER BY semana_idade"), conn, params={"id": lote_id})
            lote_info = conn.execute(text("SELECT linhagem, aves_alojadas FROM lotes WHERE id = :id"), {"id": lote_id}).mappings().first()
            
            df_metas = pd.DataFrame()
            if lote_info and lote_info['linhagem']:
                df_metas = pd.read_sql(text("SELECT * FROM metas_linhagem WHERE linhagem = :lin ORDER BY semana_idade"), conn, params={"lin": lote_info['linhagem']})

        if df_prod.empty: return go.Figure(), go.Figure(), go.Figure(), go.Figure()

        fig_peso = go.Figure()
        fig_peso.add_trace(go.Scatter(x=df_prod['semana_idade'], y=df_prod['peso_medio'], name='Peso Real', mode='lines+markers'))
        if not df_metas.empty: fig_peso.add_trace(go.Scatter(x=df_metas['semana_idade'], y=df_metas['peso_medio_g'], name='Padrão', mode='lines', line=dict(dash='dash', color='red')))
        fig_peso.update_layout(title_text="Peso Médio (g) vs. Padrão", template='plotly_white', legend_title_text='Legenda')

        df_prod['mort_acum'] = df_prod['mort_total'].cumsum()
        df_prod['mort_acum_pct'] = (df_prod['mort_acum'] / lote_info['aves_alojadas']) * 100
        fig_mort = go.Figure()
        fig_mort.add_trace(go.Scatter(x=df_prod['semana_idade'], y=df_prod['mort_acum_pct'], name='Mortalidade Real', mode='lines+markers'))
        if not df_metas.empty: fig_mort.add_trace(go.Scatter(x=df_metas['semana_idade'], y=df_metas['mortalidade_acum_pct'], name='Padrão', mode='lines', line=dict(dash='dash', color='red')))
        fig_mort.update_layout(title_text="Mortalidade Acumulada (%) vs. Padrão", yaxis_title="%", template='plotly_white', legend_title_text='Legenda')

        df_prod['consumo_acum_real'] = (df_prod['consumo_real_ave_dia'] * 7).cumsum()
        fig_cons = go.Figure()
        fig_cons.add_trace(go.Scatter(x=df_prod['semana_idade'], y=df_prod['consumo_acum_real'], name='Consumo Acum. Real', mode='lines+markers'))
        if not df_metas.empty: fig_cons.add_trace(go.Scatter(x=df_metas['semana_idade'], y=df_metas['consumo_acum_g'], name='Padrão', mode='lines', line=dict(dash='dash', color='red')))
        fig_cons.update_layout(title_text="Consumo Acumulado por Ave (g) vs. Padrão", template='plotly_white', legend_title_text='Legenda')
        
        df_prod['ganho_de_peso'] = df_prod['peso_medio'].diff().fillna(df_prod['peso_medio'])
        df_prod['consumo_semanal'] = df_prod['consumo_real_ave_dia'] * 7
        df_prod.loc[df_prod['ganho_de_peso'] <= 0, 'conv_alimentar'] = pd.NA
        df_prod.loc[df_prod['ganho_de_peso'] > 0, 'conv_alimentar'] = df_prod['consumo_semanal'] / df_prod['ganho_de_peso']
        fig_ca = px.line(df_prod.dropna(subset=['conv_alimentar']), x='semana_idade', y='conv_alimentar', title="Conversão Alimentar Semanal", template='plotly_white', markers=True)
        
        return fig_peso, fig_mort, fig_cons, fig_ca

    # --- CALLBACKS FINANCEIROS ---
    @app.callback(
        [Output("btn-custo-submit", "disabled"), Output("btn-receita-submit", "disabled")],
        Input("dropdown-lote-financeiro", "value")
    )
    def toggle_finance_buttons(lote_id):
        return (not lote_id, not lote_id)

    @app.callback(
        Output("custo-submit-status", "children"),
        Input("btn-custo-submit", "n_clicks"),
        [State("dropdown-lote-financeiro", "value"), State("custo-data", "date"), 
         State("custo-tipo", "value"), State("custo-descricao", "value"), State("custo-valor", "value")],
         prevent_initial_call=True
    )
    def insert_custo(n, lote_id, data, tipo, desc, valor):
        if not all([lote_id, data, tipo, valor]): return dbc.Alert("Todos os campos de custo são obrigatórios.", color="warning")
        engine = get_engine()
        try:
            with engine.begin() as conn:
                q = text("INSERT INTO custos_lote (lote_id, data, tipo_custo, descricao, valor) VALUES (:l, :d, :t, :desc, :v)")
                conn.execute(q, {"l": lote_id, "d": data, "t": tipo, "desc": desc, "v": valor})
            return dbc.Alert("Custo registrado!", color="success")
        except Exception as e: return dbc.Alert(f"Erro: {e}", color="danger")

    @app.callback(
        Output("receita-submit-status", "children"),
        Input("btn-receita-submit", "n_clicks"),
        [State("dropdown-lote-financeiro", "value"), State("receita-data", "date"), 
         State("receita-tipo", "value"), State("receita-descricao", "value"), State("receita-valor", "value")],
         prevent_initial_call=True
    )
    def insert_receita(n, lote_id, data, tipo, desc, valor):
        if not all([lote_id, data, tipo, valor]): return dbc.Alert("Todos os campos de receita são obrigatórios.", color="warning")
        engine = get_engine()
        try:
            with engine.begin() as conn:
                q = text("INSERT INTO receitas_lote (lote_id, data, tipo_receita, descricao, valor) VALUES (:l, :d, :t, :desc, :v)")
                conn.execute(q, {"l": lote_id, "d": data, "t": tipo, "desc": desc, "v": valor})
            return dbc.Alert("Receita registrada!", color="success")
        except Exception as e: return dbc.Alert(f"Erro: {e}", color="danger")

    @app.callback(
        Output("financeiro-resumo-div", "children"),
        [Input("dropdown-lote-financeiro", "value"), Input("custo-submit-status", "children"), Input("receita-submit-status", "children")],
    )
    def update_financeiro_resumo(lote_id, n1, n2):
        if not lote_id: return "Selecione um lote para ver o resumo financeiro."
        engine = get_engine()
        with engine.connect() as conn:
            total_custos = conn.execute(text("SELECT COALESCE(SUM(valor), 0) FROM custos_lote WHERE lote_id = :id"), {"id": lote_id}).scalar()
            total_receitas = conn.execute(text("SELECT COALESCE(SUM(valor), 0) FROM receitas_lote WHERE lote_id = :id"), {"id": lote_id}).scalar()

        saldo = total_receitas - total_custos
        cor_saldo = "success" if saldo >= 0 else "danger"
        return dbc.Card(dbc.CardBody([
            html.P(f"Total de Custos: R$ {total_custos:,.2f}", className="card-text text-danger"),
            html.P(f"Total de Receitas: R$ {total_receitas:,.2f}", className="card-text text-success"),
            html.H4(f"Saldo: R$ {saldo:,.2f}", className=f"text-{cor_saldo} fw-bold")
        ]))

    # --- CALLBACKS DE METAS ---
    @app.callback(
        Output("dropdown-linhagem-filter", "options"),
        [Input("meta-submit-status", "children"), Input("tabs", "value")]
    )
    def update_linhagem_filter_options(status, tab):
        if tab == 'tab-metas': return get_distinct_linhagens()
        raise PreventUpdate

    @app.callback(
        Output("meta-submit-status", "children"),
        Input("btn-meta-submit", "n_clicks"),
        [State("meta-linhagem", "value"), State("meta-semana", "value"),
         State("meta-peso", "value"), State("meta-consumo-dia", "value"),
         State("meta-consumo-acum", "value"), State("meta-mortalidade-acum", "value")],
        prevent_initial_call=True
    )
    def save_new_meta(n_clicks, linhagem, semana, peso, c_dia, c_acum, m_acum):
        if not all([linhagem, semana]): return dbc.Alert("Linhagem e Semana são campos obrigatórios.", color="warning")
        
        engine = get_engine()
        try:
            with engine.begin() as conn:
                q_check = text("SELECT id FROM metas_linhagem WHERE linhagem = :lin AND semana_idade = :sem")
                existing = conn.execute(q_check, {"lin": linhagem, "sem": semana}).scalar()
                
                if existing:
                    q_update = text("UPDATE metas_linhagem SET peso_medio_g = :peso, consumo_ave_dia_g = :c_dia, consumo_acum_g = :c_acum, mortalidade_acum_pct = :m_acum WHERE id = :id")
                    conn.execute(q_update, {"peso": peso, "c_dia": c_dia, "c_acum": c_acum, "m_acum": m_acum, "id": existing})
                    return dbc.Alert(f"Padrão para '{linhagem}' - Semana {semana} atualizado!", color="info")
                else:
                    q_insert = text("INSERT INTO metas_linhagem (linhagem, semana_idade, peso_medio_g, consumo_ave_dia_g, consumo_acum_g, mortalidade_acum_pct) VALUES (:lin, :sem, :peso, :c_dia, :c_acum, :m_acum)")
                    conn.execute(q_insert, {"lin": linhagem, "sem": semana, "peso": peso, "c_dia": c_dia, "c_acum": c_acum, "m_acum": m_acum})
                    return dbc.Alert("Novo padrão salvo com sucesso!", color="success")
        except Exception as e: return dbc.Alert(f"Erro ao salvar o padrão: {e}", color="danger")

    @app.callback(
        Output("metas-table-div", "children"),
        [Input("dropdown-linhagem-filter", "value"),
         Input("meta-submit-status", "children")]
    )
    def update_metas_table(selected_linhagem, status):
        query = "SELECT id, linhagem, semana_idade as 'Semana', peso_medio_g as 'Peso (g)', consumo_ave_dia_g as 'Consumo Dia (g)', consumo_acum_g as 'Consumo Acum (g)', mortalidade_acum_pct as 'Mort. Acum (%)' FROM metas_linhagem"
        params = {}
        if selected_linhagem:
            query += " WHERE linhagem = :lin"
            params = {"lin": selected_linhagem}
        query += " ORDER BY linhagem, semana_idade"
        
        engine = get_engine()
        df = pd.read_sql(text(query), engine, params=params)
        
        return dash_table.DataTable(
            id='metas-table',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_cell={'textAlign': 'left'},
            style_header={'fontWeight': 'bold'},
            page_size=10,
            row_deletable=True
        )
    
    @app.callback(
        Output("meta-submit-status", "children", allow_duplicate=True),
        Input("metas-table", "data_previous"),
        State("metas-table", "data"),
        prevent_initial_call=True
    )
    def delete_meta_row(previous, current):
        if previous is None or len(previous) <= len(current): raise PreventUpdate
        
        deleted_row = next(row for row in previous if row not in current)
        deleted_id = deleted_row.get('id')

        if not deleted_id: return dbc.Alert("ID da linha não encontrado.", color="danger")
            
        engine = get_engine()
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM metas_linhagem WHERE id = :id"), {"id": deleted_id})
            return dbc.Alert(f"Padrão ID {deleted_id} removido.", color="warning")
        except Exception as e: return dbc.Alert(f"Erro ao remover padrão: {e}", color="danger")

    # --- CALLBACKS DE PRODUÇÃO DE OVOS ---
    @app.callback(
        Output("btn-producao-submit", "disabled"),
        Input("dropdown-lote-producao", "value")
    )
    def toggle_producao_button(lote_id):
        return not lote_id

    @app.callback(
        Output("producao-submit-status", "children"),
        Input("btn-producao-submit", "n_clicks"),
        [State("dropdown-lote-producao", "value"),
         State("producao-data", "date"),
         State("producao-total-ovos", "value"),
         State("producao-ovos-quebrados", "value")],
        prevent_initial_call=True
    )
    def insert_producao_data(n, lote_id, data, total_ovos, ovos_quebrados):
        if not all([lote_id, data, total_ovos is not None]):
            return dbc.Alert("Lote, data e total de ovos são obrigatórios.", color="warning")

        engine = get_engine()
        try:
            with engine.begin() as conn:
                q = text("""
                    INSERT INTO producao_ovos (lote_id, data_producao, total_ovos, ovos_quebrados)
                    VALUES (:lote_id, :data, :total, :quebrados)
                """)
                params = {
                    "lote_id": lote_id,
                    "data": data,
                    "total": total_ovos,
                    "quebrados": ovos_quebrados
                }
                conn.execute(q, params)
            return dbc.Alert("Dados de produção inseridos com sucesso!", color="success")
        except Exception as e:
            return dbc.Alert(f"Erro ao inserir dados: {e}", color="danger")
        
    # (resto dos callbacks de produção...)

    @app.callback(
        Output("producao-table-div", "children"),
        [Input("dropdown-lote-producao", "value"),
         Input("producao-submit-status", "children")] # Atualiza a tabela após novo registro
    )
    def update_producao_table(lote_id, submit_status):
        if not lote_id:
            return "" # Não mostra nada se nenhum lote for selecionado

        engine = get_engine()
        # Query para buscar os últimos 7 registros do lote selecionado
        query = text("""
            SELECT
                DATE_FORMAT(data_producao, '%d/%m/%Y') as 'Data',
                total_ovos as 'Total de Ovos',
                ovos_quebrados as 'Ovos Quebrados'
            FROM producao_ovos
            WHERE lote_id = :lote_id
            ORDER BY data_producao DESC
            LIMIT 7
        """)
        df = pd.read_sql(query, engine, params={"lote_id": lote_id})

        if df.empty:
            return dbc.Alert("Nenhum dado de produção encontrado para este lote.", color="info")

        # Cria e retorna a DataTable
        return dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_cell={'textAlign': 'center', 'padding': '5px'},
            style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        )