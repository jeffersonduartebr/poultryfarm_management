from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
                    producao_layout, get_distinct_linhagens, agua_layout)


def register_callbacks(app):
    @app.callback(Output('tab-content', 'children'), Input('tabs', 'value'))
    def render_content(tab):
        layouts = {
            'tab-view': view_layout, 'tab-lotes': lotes_layout,
            'tab-insert-weekly': insert_weekly_layout,
            'tab-producao': producao_layout,  
            'tab-financeiro': financeiro_layout,
            'tab-treat': treat_layout, 
            'tab-metas': metas_layout, 
            'tab-reports': reports_layout,
            'tab-agua': agua_layout
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
            # Removemos a consulta da ultima_semana
        aves_atuais = aves_alojadas - mort_acumulada
        # Retornamos None para o valor da semana, para que o usuário preencha.
        return {'display': 'block'}, aves_atuais, None

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
        


    @app.callback(
        Output("producao-table-div", "children"),
        Input("dropdown-lote-producao", "value")
    )
    def update_producao_table(lote_id):
        if not lote_id:
            return ""

        engine = get_engine()
        query = text("""
            SELECT
                DATE_FORMAT(data_producao, '%d/%m/%Y') as 'Data',
                total_ovos as 'Total de Ovos',
                ovos_quebrados as 'Ovos Quebrados'
            FROM producao_ovos
            WHERE lote_id = :lote_id
            AND MONTH(data_producao) = MONTH(CURDATE())
            AND YEAR(data_producao) = YEAR(CURDATE())
            ORDER BY data_producao DESC
        """)
        df = pd.read_sql(query, engine, params={"lote_id": lote_id})

        if df.empty:
            return dbc.Alert("Nenhum dado de produção encontrado para este mês.", color="info")

        return dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_cell={'textAlign': 'center', 'padding': '5px'},
            style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        )

    @app.callback(
        Output("producao-resumo-mensal", "children"),
        Input("dropdown-lote-producao", "value")
    )
    def update_resumo_mensal(lote_id):
        if not lote_id:
            return ""

        engine = get_engine()

        query = text("""
            SELECT 
                DATE_FORMAT(data_producao, '%m') as mes_num,
                DATE_FORMAT(data_producao, '%Y') as ano,
                MONTHNAME(data_producao) as mes_nome,
                SUM(total_ovos) as total_ovos,
                SUM(ovos_quebrados) as total_quebrados
            FROM producao_ovos
            WHERE lote_id = :lote_id
            AND data_producao < DATE_FORMAT(CURDATE(), '%Y-%m-01')  -- Exclui mês atual
            AND data_producao >= DATE_SUB(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 3 MONTH)
            GROUP BY mes_nome, ano
            ORDER BY ano DESC, mes_num DESC
            LIMIT 3
        """)
        df = pd.read_sql(query, engine, params={"lote_id": lote_id})

        if df.empty:
            return dbc.Alert("Sem dados dos meses anteriores.", color="info")

        # Formatar mês: "Janeiro/2025"
        df['Mês'] = df.apply(lambda row: f"{row['mes_nome'].capitalize()}/{row['ano']}", axis=1)
        df = df[['Mês', 'total_ovos', 'total_quebrados']]
        df.columns = ['Mês', 'Total de Ovos', 'Ovos Quebrados']

        return dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_cell={'textAlign': 'center', 'padding': '5px'},
            style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
        )

    # ==========================================================
    # === SEÇÃO: QUALIDADE DA ÁGUA (pH e Alcalinidade)       ===
    # ==========================================================

    # Habilita o botão quando houver lote + pH + data
    @app.callback(
        Output("btn-agua-submit", "disabled"),
        [
            Input("dropdown-lote-agua", "value"),
            Input("agua-ph", "value"),
            Input("agua-data", "date")
        ],
    )
    def toggle_agua_button(lote_id, ph, data):
        return not (lote_id and ph is not None and data)

    # Insere (ou atualiza) o registro diário (UNIQUE por lote+data)
    @app.callback(
        Output("agua-submit-status", "children"),
        Input("btn-agua-submit", "n_clicks"),
        [
            State("dropdown-lote-agua", "value"),
            State("agua-data", "date"),
            State("agua-ph", "value"),
            State("agua-alc", "value")
        ],
        prevent_initial_call=True
    )
    def insert_agua(n_clicks, lote_id, data_medicao, ph, alc_ppm):
        if not (lote_id and data_medicao and ph is not None):
            return dbc.Alert("Lote, data e pH são obrigatórios.", color="warning")

        alc_ppm = alc_ppm or 0
        engine = get_engine()
        try:
            with engine.begin() as conn:
                # MySQL UPSERT via UNIQUE (lote_id, data_medicao)
                q = text("""
                    INSERT INTO qualidade_agua (lote_id, data_medicao, ph, alcalinidade_ppm)
                    VALUES (:l, :d, :ph, :alc)
                    ON DUPLICATE KEY UPDATE ph = VALUES(ph), alcalinidade_ppm = VALUES(alcalinidade_ppm)
                """)
                conn.execute(q, {"l": lote_id, "d": data_medicao, "ph": ph, "alc": alc_ppm})

            return dbc.Alert("Registro salvo/atualizado com sucesso!", color="success")
        except Exception as e:
            return dbc.Alert(f"Erro ao salvar registro: {e}", color="danger")

    # Atualiza gráfico e histórico (últimos 30 dias) ao selecionar lote ou após salvar
    @app.callback(
        [Output("agua-graph", "figure"), Output("agua-table-div", "children")],
        [Input("dropdown-lote-agua", "value"), Input("agua-submit-status", "children")]
    )
    def update_agua_view(lote_id, submit_msg):
        if not lote_id:
            return go.Figure(), ""

        engine = get_engine()
        # últimos 30 dias
        query = text("""
            SELECT data_medicao, ph, alcalinidade_ppm
            FROM qualidade_agua
            WHERE lote_id = :l
              AND data_medicao >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            ORDER BY data_medicao
        """)
        df = pd.read_sql(query, engine, params={"l": lote_id})

        # Gráfico com 2 eixos (pH e Alcalinidade)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        if not df.empty:
            df["data_medicao"] = pd.to_datetime(df["data_medicao"])
            fig.add_trace(
                go.Scatter(x=df["data_medicao"], y=df["ph"], mode="lines+markers", name="pH"),
                secondary_y=False
            )
            fig.add_trace(
                go.Bar(x=df["data_medicao"], y=df["alcalinidade_ppm"], name="Alcalinidade (ppm)", opacity=0.5),
                secondary_y=True
            )
            fig.update_yaxes(title_text="pH", secondary_y=False, range=[0, 14])
            fig.update_yaxes(title_text="Alcalinidade (ppm)", secondary_y=True)
            fig.update_layout(
                title="pH (linha) e Alcalinidade (barras) — últimos 30 dias",
                template="plotly_white",
                legend_title_text="Séries",
                barmode="overlay"
            )
        else:
            fig.update_layout(title="Sem dados de qualidade da água nos últimos 30 dias", template="plotly_white")

        # Tabela
        if df.empty:
            table = dbc.Alert("Sem registros nos últimos 30 dias.", color="info")
        else:
            dft = df.copy()
            dft["Data"] = dft["data_medicao"].dt.strftime("%d/%m/%Y")
            dft = dft[["Data", "ph", "alcalinidade_ppm"]]
            dft.columns = ["Data", "pH", "Alcalinidade (ppm)"]
            table = dash_table.DataTable(
                columns=[{"name": c, "id": c} for c in dft.columns],
                data=dft.to_dict("records"),
                style_cell={"textAlign": "center", "padding": "6px"},
                style_header={"fontWeight": "bold", "backgroundColor": "whitesmoke"},
                page_size=15
            )

        return fig, table


    # ==========================================================
    # === SEÇÃO: RELATÓRIOS (ATIVAÇÃO DO BOTÃO + GERAR PDF) ===
    # ==========================================================

    # Habilita o botão quando um lote for escolhido
    @app.callback(
        Output("btn-generate-report", "disabled"),
        Input("dropdown-lote-report", "value")
    )
    def toggle_report_button(lote_id):
        return not bool(lote_id)

    # Gera PDF completo (produção, mortalidade, financeiro, QR, rodapé)
    @app.callback(
        Output("download-pdf-report", "data"),
        Input("btn-generate-report", "n_clicks"),
        State("dropdown-lote-report", "value"),
        prevent_initial_call=True
    )
    def gerar_pdf_completo(n_clicks, lote_id):
        if not lote_id:
            raise PreventUpdate

        try:
            # ---------------------------------------
            # (0) Período do relatório: últimos 180d
            # ---------------------------------------
            hoje = datetime.now().date()
            inicio_periodo = hoje - timedelta(days=180)

            # ---------------------------
            # (1) BUSCAS NO BANCO (180d)
            # ---------------------------
            engine = get_engine()
            with engine.connect() as conn:
                # Info do lote
                lote_info = conn.execute(text("""
                    SELECT identificador_lote, linhagem, data_alojamento, aves_alojadas 
                    FROM lotes WHERE id = :id
                """), {"id": lote_id}).mappings().first()

                # Produção de ovos (últimos 180 dias)
                df_prod_ovos = pd.read_sql(
                    text("""
                        SELECT data_producao, total_ovos, ovos_quebrados
                        FROM producao_ovos
                        WHERE lote_id = :id
                          AND data_producao >= :inicio
                        ORDER BY data_producao DESC
                    """),
                    conn, params={"id": lote_id, "inicio": inicio_periodo}
                )

                # Mortalidade / desempenho semanal (filtra pela data de pesagem)
                df_sem = pd.read_sql(
                    text("""
                        SELECT semana_idade, aves_na_semana, 
                               mort_d1, mort_d2, mort_d3, mort_d4, mort_d5, mort_d6, mort_d7, mort_total,
                               data_pesagem, peso_medio, consumo_real_ave_dia
                        FROM producao_aves
                        WHERE lote_id = :id
                          AND data_pesagem >= :inicio
                        ORDER BY semana_idade
                    """),
                    conn, params={"id": lote_id, "inicio": inicio_periodo}
                )

                # Tratamentos (qualquer início ou término no período)
                df_trat = pd.read_sql(
                    text("""
                        SELECT data_inicio, data_termino, medicacao, forma_admin, 
                               periodo_carencia_dias, motivacao
                        FROM tratamentos
                        WHERE lote_id = :id
                          AND (data_inicio >= :inicio OR data_termino >= :inicio)
                        ORDER BY data_inicio DESC
                    """),
                    conn, params={"id": lote_id, "inicio": inicio_periodo}
                )

                # 💧 Qualidade da Água (últimos 180 dias)
                df_agua = pd.read_sql(
                    text("""
                        SELECT data_medicao, ph, alcalinidade_ppm
                        FROM qualidade_agua
                        WHERE lote_id = :id
                          AND data_medicao >= :inicio
                        ORDER BY data_medicao DESC
                    """),
                    conn, params={"id": lote_id, "inicio": inicio_periodo}
                )

                # Financeiro (custos e receitas no período, + agregados)
                df_custos = pd.read_sql(
                    text("""
                        SELECT data, tipo_custo AS tipo, descricao, valor
                        FROM custos_lote
                        WHERE lote_id = :id
                          AND data >= :inicio
                        ORDER BY data DESC
                    """),
                    conn, params={"id": lote_id, "inicio": inicio_periodo}
                )
                df_receitas = pd.read_sql(
                    text("""
                        SELECT data, tipo_receita AS tipo, descricao, valor
                        FROM receitas_lote
                        WHERE lote_id = :id
                          AND data >= :inicio
                        ORDER BY data DESC
                    """),
                    conn, params={"id": lote_id, "inicio": inicio_periodo}
                )
                total_custos = conn.execute(text(
                    "SELECT COALESCE(SUM(valor),0) FROM custos_lote WHERE lote_id = :id AND data >= :inicio"
                ), {"id": lote_id, "inicio": inicio_periodo}).scalar() or 0.0
                total_receitas = conn.execute(text(
                    "SELECT COALESCE(SUM(valor),0) FROM receitas_lote WHERE lote_id = :id AND data >= :inicio"
                ), {"id": lote_id, "inicio": inicio_periodo}).scalar() or 0.0

            saldo = float(total_receitas) - float(total_custos)

            # ---------------------------
            # (2) QR CODE (com rota pública)
            # ---------------------------
            base_url = "http://nancy.ifrn.edu.br/"
            lote_url = f"{base_url.rstrip('/')}/public/lote/{lote_id}"  # ✅ ROTA PÚBLICA
            qr_img_b64 = ""
            try:
                import qrcode
                from io import BytesIO
                qr = qrcode.QRCode(version=1, box_size=6, border=2)
                qr.add_data(lote_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buf = BytesIO()
                img.save(buf, format="PNG")
                qr_img_b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
            except Exception:
                qr_img_b64 = ""  # fallback: mostraremos a URL em texto

            # ---------------------------
            # (3) FUNÇÕES AUXILIARES
            # ---------------------------
            def fmt_date(dt):
                if pd.isna(dt): return ""
                if isinstance(dt, str): return dt
                return pd.to_datetime(dt).strftime("%d/%m/%Y")

            def truncate_text(texto, maxlen=120):
                if texto is None: return ""
                s = str(texto).strip()
                return s if len(s) <= maxlen else s[:maxlen - 3] + "..."

            # ---------------------------
            # (4) TABELAS HTML
            # ---------------------------
            # Produção de ovos
            prod_html_rows = ""
            if not df_prod_ovos.empty:
                for _, r in df_prod_ovos.sort_values("data_producao").iterrows():
                    prod_html_rows += f"""
                    <tr>
                        <td>{fmt_date(r['data_producao'])}</td>
                        <td style="text-align:right">{int(r['total_ovos'] or 0)}</td>
                        <td style="text-align:right">{int(r['ovos_quebrados'] or 0)}</td>
                    </tr>"""
            else:
                prod_html_rows = '<tr><td colspan="3" style="text-align:center">Sem registros</td></tr>'

            prod_table_html = f"""
            <table>
                <thead><tr><th>Data</th><th>Total de Ovos</th><th>Ovos Quebrados</th></tr></thead>
                <tbody>{prod_html_rows}</tbody>
            </table>
            """

            # Mortalidade / desempenho
            sem_html_rows = ""
            if not df_sem.empty:
                for _, r in df_sem.iterrows():
                    sem_html_rows += f"""
                    <tr>
                        <td style="text-align:right">{int(r['semana_idade'] or 0)}</td>
                        <td style="text-align:right">{int(r['aves_na_semana'] or 0)}</td>
                        <td style="text-align:right">{int(r['mort_total'] or 0)}</td>
                        <td>{fmt_date(r['data_pesagem'])}</td>
                        <td style="text-align:right">{(r['peso_medio'] or 0):.2f}</td>
                        <td style="text-align:right">{(r['consumo_real_ave_dia'] or 0):.2f}</td>
                    </tr>"""
            else:
                sem_html_rows = '<tr><td colspan="6" style="text-align:center">Sem registros</td></tr>'

            sem_table_html = f"""
            <table>
                <thead>
                    <tr>
                        <th>Semana</th><th>Aves</th><th>Mort. (sem)</th>
                        <th>Data Pesagem</th><th>Peso Médio (g)</th><th>Consumo (g/ave/dia)</th>
                    </tr>
                </thead>
                <tbody>{sem_html_rows}</tbody>
            </table>
            """

            # Tratamentos
            trat_html_rows = ""
            if not df_trat.empty:
                for _, r in df_trat.iterrows():
                    trat_html_rows += f"""
                    <tr>
                        <td>{fmt_date(r['data_inicio'])}</td>
                        <td>{fmt_date(r['data_termino'])}</td>
                        <td>{r['medicacao'] or ''}</td>
                        <td>{r['forma_admin'] or ''}</td>
                        <td style="text-align:right">{int(r['periodo_carencia_dias'] or 0)}</td>
                        <td>{truncate_text(r['motivacao'])}</td>
                    </tr>"""
            else:
                trat_html_rows = '<tr><td colspan="6" style="text-align:center">Sem registros de tratamento</td></tr>'

            trat_table_html = f"""
            <table>
                <thead>
                    <tr>
                        <th>Início</th>
                        <th>Término</th>
                        <th>Medicação</th>
                        <th>Forma de Administração</th>
                        <th>Carência (dias)</th>
                        <th>Motivação</th>
                    </tr>
                </thead>
                <tbody>{trat_html_rows}</tbody>
            </table>
            """

            # 💧 Qualidade da Água — tabela
            agua_html_rows = ""
            if not df_agua.empty:
                for _, r in df_agua.iterrows():
                    ph_val = 0.0 if pd.isna(r['ph']) else float(r['ph'])
                    alc_val = 0 if pd.isna(r['alcalinidade_ppm']) else int(r['alcalinidade_ppm'])
                    agua_html_rows += f"""
                    <tr>
                        <td>{fmt_date(r['data_medicao'])}</td>
                        <td style="text-align:right">{ph_val:.2f}</td>
                        <td style="text-align:right">{alc_val}</td>
                    </tr>
                    """
            else:
                agua_html_rows = '<tr><td colspan="3" style="text-align:center">Sem registros de qualidade da água nos últimos 180 dias.</td></tr>'

            agua_table_html = f"""
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>pH</th>
                        <th>Alcalinidade (ppm)</th>
                    </tr>
                </thead>
                <tbody>{agua_html_rows}</tbody>
            </table>
            """

            # Financeiro – custos e receitas
            def table_from(df, headers):
                if df.empty:
                    return f'<table><thead><tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr></thead><tbody><tr><td colspan="{len(headers)}" style="text-align:center">Sem registros</td></tr></tbody></table>'
                rows = ""
                for _, r in df.iterrows():
                    rows += f"""
                    <tr>
                        <td>{fmt_date(r['data'])}</td>
                        <td>{r['tipo'] or ''}</td>
                        <td>{truncate_text(r['descricao'])}</td>
                        <td style="text-align:right">R$ {float(r['valor'] or 0):,.2f}</td>
                    </tr>"""
                return f"""
                <table>
                    <thead><tr>{"".join(f"<th>{h}</th>" for h in headers)}</tr></thead>
                    <tbody>{rows}</tbody>
                </table>
                """

            custos_table_html = table_from(df_custos, ["Data", "Tipo", "Descrição", "Valor"])
            receitas_table_html = table_from(df_receitas, ["Data", "Tipo", "Descrição", "Valor"])

            resumo_fin_html = f"""
            <table>
                <thead><tr><th>Total de Custos</th><th>Total de Receitas</th><th>Saldo</th></tr></thead>
                <tbody>
                    <tr>
                        <td style="text-align:right;color:#b00020">R$ {float(total_custos):,.2f}</td>
                        <td style="text-align:right;color:#006400">R$ {float(total_receitas):,.2f}</td>
                        <td style="text-align:right;font-weight:bold">{'R$ ' + format(float(saldo), ',.2f')}</td>
                    </tr>
                </tbody>
            </table>
            """

            # ---------------------------
            # (5) HTML FINAL DO PDF
            # ---------------------------
            proprietaria = "Rosilene Duarte de Lima"
            cpf = "566.408.974-15"
            responsavel_tecnico = "Ernesto Guevara"
            agora_str = datetime.now().strftime("%d/%m/%Y %H:%M")

            # QR (ou URL em destaque)
            qr_block = f'<img src="{qr_img_b64}" style="width:160px;height:160px" />' if qr_img_b64 else f"""
                <div style="border:1px dashed #888; padding:10px; font-size:12px">
                    Acesse o painel do lote:<br><b>{lote_url}</b>
                </div>
            """

            html_content = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    @page {{
                        size: A4;                 /* RETRATO */
                        margin: 12mm;
                        @bottom-right {{
                            content: "Página " counter(page) " de " counter(pages) " — Gerado automaticamente pelo Sistema de Gestão Avícola - IFRN | {agora_str} | Últimos 180 dias";
                            font-size: 10px;
                            color: #666;
                        }}
                    }}
                    body {{ font-family: Arial, sans-serif; font-size: 12px; color: #111; }}
                    h1 {{ text-align: center; margin: 0 0 6px 0; }}
                    h2 {{ margin: 16px 0 6px 0; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 6px 0 12px 0; }}
                    th, td {{ border: 1px solid #333; padding: 6px; text-align: left; }}
                    thead th {{ background: #efefef; }}
                    .header {{
                        border-bottom: 2px solid #333; padding-bottom: 6px; margin-bottom: 10px;
                        display: flex; justify-content: space-between; align-items: flex-start;
                    }}
                    .owner-box {{ border: 1px solid #555; padding: 8px; margin: 8px 0; background: #f8f8f8; }}
                    .id-box {{
                        border: 1px solid #333; padding: 8px; margin: 6px 0;
                        display: grid; grid-template-columns: 1fr 1fr; gap: 4px;
                    }}
                    .qr {{ border: 1px solid #aaa; padding: 8px; display: inline-block; margin-top: 4px; }}
                    .period-note {{ font-size: 11px; color: #666; margin-top: 4px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div>
                        <h1>Relatório do Lote {lote_info['identificador_lote']}</h1>
                        <div style="font-size:12px;color:#333;">Painel: {lote_url}</div>
                        <div class="period-note">
                            Período incluído neste relatório: últimos 180 dias (a partir de {inicio_periodo.strftime("%d/%m/%Y")})
                        </div>
                    </div>
                    <div class="qr">{qr_block}</div>
                </div>

                <div class="owner-box">
                    <b>Proprietária:</b> {proprietaria} &nbsp; | &nbsp; <b>CPF:</b> {cpf}<br>
                    <b>Responsável Técnico:</b> {responsavel_tecnico}
                </div>

                <div class="id-box">
                    <div><b>Linhagem:</b> {lote_info['linhagem'] or ''}</div>
                    <div><b>Data de Alojamento:</b> {lote_info['data_alojamento']}</div>
                    <div><b>Aves Alojadas:</b> {lote_info['aves_alojadas']}</div>
                    <div><b>ID Interno:</b> {lote_id}</div>
                </div>

                <h2>Produção de Ovos (últimos 180 dias)</h2>
                {prod_table_html}

                <h2>Mortalidade & Desempenho Semanal</h2>
                {sem_table_html}

                <h2>🩺 Tratamentos Aplicados ao Lote</h2>
                {trat_table_html}

                <h2>💧 Qualidade da Água (últimos 180 dias)</h2>
                {agua_table_html}

                <h2>Financeiro — Custos</h2>
                {custos_table_html}

                <h2>Financeiro — Receitas</h2>
                {receitas_table_html}

                <h2>Resumo Financeiro</h2>
                {resumo_fin_html}
            </body>
            </html>
            """

            # ---------------------------
            # (6) GERA E ENVIA O PDF
            # ---------------------------
            pdf_path = f"/tmp/relatorio_lote_{lote_id}.pdf"
            HTML(string=html_content).write_pdf(pdf_path)
            return dcc.send_file(pdf_path)

        except Exception as e:
            print(f"[Relatórios] ERRO ao gerar PDF: {e}")
            return dash.no_update
