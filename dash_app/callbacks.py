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
import base64
from weasyprint import HTML
from datetime import datetime, timedelta

engine = get_engine()

def register_callbacks(app):
    from layout import (view_layout, lotes_layout, insert_weekly_layout, 
                        financeiro_layout, treat_layout, metas_layout, reports_layout,
                        get_distinct_linhagens) # Importar a função auxiliar

    # Callback principal para renderizar o conteúdo das abas
    @app.callback(Output('tab-content', 'children'), Input('tabs', 'value'))
    def render_content(tab):
        layouts = {
            'tab-view': view_layout, 'tab-lotes': lotes_layout,
            'tab-insert-weekly': insert_weekly_layout, 'tab-financeiro': financeiro_layout,
            'tab-treat': treat_layout, 'tab-metas': metas_layout, 'tab-reports': reports_layout
        }
        return layouts.get(tab, lambda: html.H3("Página não encontrada"))()

    # ================== Callbacks de Gestão de Lotes ==================
    # (Callbacks de lotes permanecem os mesmos)
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
        df = pd.read_sql("SELECT id, identificador_lote as 'Lote', linhagem as 'Linhagem', aviario_alocado as 'Aviário', data_alojamento as 'Data', aves_alojadas as 'Aves', status as 'Status' FROM lotes ORDER BY data_alojamento DESC", engine)
        return dash_table.DataTable(id='lotes-table', columns=[{"name": i, "id": i, "deletable": False} for i in df.columns], data=df.to_dict('records'), row_selectable="single", selected_rows=[])

    # ================== Callbacks de Visualização (GRÁFICOS) - ATUALIZADO ==================
    @app.callback(
        [Output("graph-peso-medio", "figure"), Output("graph-mortalidade-acumulada", "figure"),
         Output("graph-consumo-comparativo", "figure"), Output("graph-conversao-alimentar", "figure")],
        Input("dropdown-lote-indicadores", "value")
    )
    def update_indicadores_graphs(lote_id):
        if not lote_id:
            return go.Figure(), go.Figure(), go.Figure(), go.Figure()

        with engine.connect() as conn:
            df_prod = pd.read_sql(text("SELECT * FROM producao_aves WHERE lote_id = :id ORDER BY semana_idade"), conn, params={"id": lote_id})
            lote_info = conn.execute(text("SELECT linhagem, aves_alojadas FROM lotes WHERE id = :id"), {"id": lote_id}).mappings().first()
            
            # Busca as metas para a linhagem do lote selecionado
            df_metas = pd.DataFrame()
            if lote_info and lote_info['linhagem']:
                df_metas = pd.read_sql(text("SELECT * FROM metas_linhagem WHERE linhagem = :lin ORDER BY semana_idade"), conn, params={"lin": lote_info['linhagem']})

        if df_prod.empty:
            return go.Figure(), go.Figure(), go.Figure(), go.Figure()

        # Gráfico de Peso com Meta
        fig_peso = go.Figure()
        fig_peso.add_trace(go.Scatter(x=df_prod['semana_idade'], y=df_prod['peso_medio'], name='Peso Real', mode='lines+markers'))
        if not df_metas.empty:
            fig_peso.add_trace(go.Scatter(x=df_metas['semana_idade'], y=df_metas['peso_medio_g'], name='Padrão', mode='lines', line=dict(dash='dash', color='red')))
        fig_peso.update_layout(title_text="Peso Médio (g) vs. Padrão", template='plotly_white', legend_title_text='Legenda')

        # Gráfico de Mortalidade com Meta
        df_prod['mort_acum'] = df_prod['mort_total'].cumsum()
        df_prod['mort_acum_pct'] = (df_prod['mort_acum'] / lote_info['aves_alojadas']) * 100
        fig_mort = go.Figure()
        fig_mort.add_trace(go.Scatter(x=df_prod['semana_idade'], y=df_prod['mort_acum_pct'], name='Mortalidade Real', mode='lines+markers'))
        if not df_metas.empty:
            fig_mort.add_trace(go.Scatter(x=df_metas['semana_idade'], y=df_metas['mortalidade_acum_pct'], name='Padrão', mode='lines', line=dict(dash='dash', color='red')))
        fig_mort.update_layout(title_text="Mortalidade Acumulada (%) vs. Padrão", yaxis_title="%", template='plotly_white', legend_title_text='Legenda')

        # Gráfico de Consumo com Meta
        df_prod['consumo_acum_real'] = (df_prod['consumo_real_ave_dia'] * 7).cumsum()
        fig_cons = go.Figure()
        fig_cons.add_trace(go.Scatter(x=df_prod['semana_idade'], y=df_prod['consumo_acum_real'], name='Consumo Acum. Real', mode='lines+markers'))
        if not df_metas.empty:
            fig_cons.add_trace(go.Scatter(x=df_metas['semana_idade'], y=df_metas['consumo_acum_g'], name='Padrão', mode='lines', line=dict(dash='dash', color='red')))
        fig_cons.update_layout(title_text="Consumo Acumulado por Ave (g) vs. Padrão", template='plotly_white', legend_title_text='Legenda')
        
        # Gráfico de Conversão Alimentar (sem meta, pois é um indicador calculado)
        df_prod['ganho_de_peso'] = df_prod['peso_medio'].diff().fillna(df_prod['peso_medio'])
        df_prod['consumo_semanal'] = df_prod['consumo_real_ave_dia'] * 7
        # Evitar divisão por zero ou ganho de peso negativo
        df_prod.loc[df_prod['ganho_de_peso'] <= 0, 'conv_alimentar'] = pd.NA
        df_prod.loc[df_prod['ganho_de_peso'] > 0, 'conv_alimentar'] = df_prod['consumo_semanal'] / df_prod['ganho_de_peso']
        fig_ca = px.line(df_prod.dropna(subset=['conv_alimentar']), x='semana_idade', y='conv_alimentar', title="Conversão Alimentar Semanal", template='plotly_white', markers=True)
        
        return fig_peso, fig_mort, fig_cons, fig_ca

    # ================== NOVOS CALLBACKS PARA METAS ==================
    @app.callback(
        Output("dropdown-linhagem-filter", "options"),
        Input("meta-submit-status", "children"), # Atualiza quando uma nova meta é salva
        Input("tabs", "value") # Atualiza quando a aba é aberta
    )
    def update_linhagem_filter_options(status, tab):
        if tab == 'tab-metas':
            return get_distinct_linhagens()
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
        if not all([linhagem, semana]):
            return dbc.Alert("Linhagem e Semana são campos obrigatórios.", color="warning")
        
        try:
            with engine.begin() as conn:
                # Checa se já existe um registro para essa linhagem e semana para evitar duplicatas
                q_check = text("SELECT id FROM metas_linhagem WHERE linhagem = :lin AND semana_idade = :sem")
                existing = conn.execute(q_check, {"lin": linhagem, "sem": semana}).scalar()
                
                if existing:
                    # Atualiza o registro existente
                    q_update = text("""
                        UPDATE metas_linhagem SET peso_medio_g = :peso, consumo_ave_dia_g = :c_dia,
                        consumo_acum_g = :c_acum, mortalidade_acum_pct = :m_acum
                        WHERE id = :id
                    """)
                    conn.execute(q_update, {"peso": peso, "c_dia": c_dia, "c_acum": c_acum, "m_acum": m_acum, "id": existing})
                    return dbc.Alert(f"Padrão para '{linhagem}' - Semana {semana} atualizado!", color="info")
                else:
                    # Insere um novo registro
                    q_insert = text("""
                        INSERT INTO metas_linhagem (linhagem, semana_idade, peso_medio_g, consumo_ave_dia_g, consumo_acum_g, mortalidade_acum_pct)
                        VALUES (:lin, :sem, :peso, :c_dia, :c_acum, :m_acum)
                    """)
                    conn.execute(q_insert, {"lin": linhagem, "sem": semana, "peso": peso, "c_dia": c_dia, "c_acum": c_acum, "m_acum": m_acum})
                    return dbc.Alert("Novo padrão salvo com sucesso!", color="success")
        except Exception as e:
            return dbc.Alert(f"Erro ao salvar o padrão: {e}", color="danger")

    @app.callback(
        Output("metas-table-div", "children"),
        [Input("dropdown-linhagem-filter", "value"),
         Input("meta-submit-status", "children")] # Atualiza a tabela após salvar/deletar
    )
    def update_metas_table(selected_linhagem, status):
        query = "SELECT id, linhagem, semana_idade as 'Semana', peso_medio_g as 'Peso (g)', consumo_ave_dia_g as 'Consumo Dia (g)', consumo_acum_g as 'Consumo Acum (g)', mortalidade_acum_pct as 'Mort. Acum (%)' FROM metas_linhagem"
        params = {}
        if selected_linhagem:
            query += " WHERE linhagem = :lin"
            params = {"lin": selected_linhagem}
        query += " ORDER BY linhagem, semana_idade"
        
        df = pd.read_sql(text(query), engine, params=params)
        
        return dash_table.DataTable(
            id='metas-table',
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_cell={'textAlign': 'left'},
            style_header={'fontWeight': 'bold'},
            page_size=10,
            row_deletable=True # Permite a deleção de linhas
        )
    
    @app.callback(
        Output("meta-submit-status", "children", allow_duplicate=True),
        Input("metas-table", "data_previous"),
        State("metas-table", "data"),
        prevent_initial_call=True
    )
    def delete_meta_row(previous, current):
        if previous is None or len(previous) <= len(current):
            raise PreventUpdate
        
        # Encontra a linha que foi removida
        deleted_row = next(row for row in previous if row not in current)
        deleted_id = deleted_row.get('id')

        if not deleted_id:
            return dbc.Alert("ID da linha não encontrado. Não foi possível deletar.", color="danger")
            
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM metas_linhagem WHERE id = :id"), {"id": deleted_id})
            return dbc.Alert(f"Padrão ID {deleted_id} removido com sucesso.", color="warning")
        except Exception as e:
            return dbc.Alert(f"Erro ao remover padrão: {e}", color="danger")

    # Demais callbacks (financeiro, tratamentos, etc.) permanecem aqui...


    # ================== Callbacks Financeiros ==================
    @app.callback(
        [Output("btn-custo-submit", "disabled"), Output("btn-receita-submit", "disabled")],
        Input("dropdown-lote-financeiro", "value")
    )
    def toggle_finance_buttons(lote_id):
        return (not lote_id, not lote_id)
    
    # ... (Callbacks de inserção de custo/receita e atualização do resumo)

    # ================== Callbacks de Tratamentos =================
    @app.callback(Output("btn-treat-submit", "disabled"), Input("dropdown-lote-treat", "value"))
    def toggle_treat_button(lote_id):
        return not lote_id
    
    # ... (Callbacks de inserção de tratamento e atualização da tabela de histórico)

    # ================== Callback de Alertas ==================
    @app.callback(
        [Output("alert-toast", "is_open"), Output("alert-toast-content", "children")],
        Input("interval-alerts", "n_intervals")
    )
    def check_alerts(n):
        alerts = []
        with engine.connect() as conn:
            q_carencia = text("SELECT l.identificador_lote, t.medicacao, t.data_termino, t.periodo_carencia_dias FROM tratamentos t JOIN lotes l ON t.lote_id = l.id WHERE l.status = 'Ativo' AND t.data_termino IS NOT NULL AND t.periodo_carencia_dias > 0")
            tratamentos = conn.execute(q_carencia).mappings().fetchall()
            for t in tratamentos:
                data_liberacao = t['data_termino'] + timedelta(days=t['periodo_carencia_dias'])
                if datetime.now().date() < data_liberacao:
                    alerts.append(f"Lote '{t['identificador_lote']}' em carência por '{t['medicacao']}' até {data_liberacao.strftime('%d/%m/%Y')}.")
        if alerts: return True, html.Ul([html.Li(a) for a in alerts])
        return False, ""

    # ================== Callback de Relatórios ==================
    @app.callback(Output("btn-generate-report", "disabled"), Input("dropdown-lote-report", "value"))
    def toggle_report_button(lote_id):
        return not lote_id
        
    @app.callback(
        [Output("download-pdf-report", "data"), Output("report-generation-status", "children")],
        Input("btn-generate-report", "n_clicks"),
        State("dropdown-lote-report", "value"),
        prevent_initial_call=True
    )
    def generate_pdf_report(n_clicks, selected_sections):
        if not n_clicks or not selected_sections:
            raise dash.exceptions.PreventUpdate
        
        full_html = ""

        # --- Seção de Indicadores da Criação (para TODOS os aviários) ---
        if 'tab-view' in selected_sections:
            try:
                # 1. Buscar todos os aviários distintos do banco de dados
                with engine.connect() as conn:
                    aviarios_df = pd.read_sql("SELECT DISTINCT aviario FROM producao_aves WHERE aviario IS NOT NULL ORDER BY aviario", conn)
                    all_aviarios = aviarios_df['aviario'].tolist()

                if not all_aviarios:
                    full_html += "<h1>Indicadores da Criação</h1><p>Nenhum aviário com dados encontrado.</p>"
                else:
                    # 2. Loop sobre cada aviário
                    for aviario in all_aviarios:
                        full_html += f"<h1>Indicadores da Criação: {aviario}</h1>"
                        
                        # 3. Gerar os gráficos para o aviário atual
                        figs = atualizar_graficos(aviario)
                        titles = ["Peso Médio", "Mortalidade Semanal", "Consumo Real", "Mortalidade Acumulada", "Consumo Acumulado"]
                        
                        has_data = False
                        for fig, title in zip(figs, titles):
                            if fig.data: # Verifica se a figura tem dados para exibir
                                has_data = True
                                img_bytes = fig.to_image(format="png", width=700, height=350)
                                encoded = base64.b64encode(img_bytes).decode()
                                full_html += f"<h3>{title}</h3><img src='data:image/png;base64,{encoded}'>"
                        
                        if not has_data:
                            full_html += "<p>Não há dados suficientes para gerar gráficos para este aviário.</p>"

            except Exception as e:
                full_html += f"<h1>Indicadores da Criação</h1><p>Ocorreu um erro ao gerar os gráficos: {e}</p>"

        # --- Seções de Tabelas de Histórico ---
        if 'tab-bait' in selected_sections:
            full_html += "<h1>Histórico de Inspeção de Iscas</h1>"
            df = pd.read_sql("SELECT * FROM iscas ORDER BY id DESC LIMIT 20", engine)
            full_html += df.to_html(index=False, border=1, classes="table")

        if 'tab-visits' in selected_sections:
            full_html += "<h1>Histórico de Visitas</h1>"
            df = pd.read_sql("SELECT * FROM visitas ORDER BY id DESC LIMIT 20", engine)
            full_html += df.to_html(index=False, border=1, classes="table")

        if 'tab-treat' in selected_sections:
            full_html += "<h1>Histórico de Tratamentos</h1>"
            df = pd.read_sql("SELECT * FROM tratamentos ORDER BY id DESC LIMIT 20", engine)
            full_html += df.to_html(index=False, border=1, classes="table")
            
        # Monta o HTML e CSS para o PDF final
        final_html = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{ size: portrait; margin: 1.5cm; }} 
                    body {{ font-family: Arial, sans-serif; font-size: 12pt; }}
                    h1 {{ 
                        font-size: 20pt;
                        color: #2c3e50;
                        border-bottom: 2px solid #3498db; 
                        padding-bottom: 5px; 
                        margin-top: 25px;
                        page-break-before: always; 
                    }}
                    h3 {{ font-size: 14pt; color: #34495e; margin-top: 20px; }}
                    img {{ max-width: 100%; height: auto; border: 1px solid #ddd; margin-top: 10px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 15px; font-size: 9pt; page-break-inside: auto; }}
                    tr {{ page-break-inside: avoid; page-break-after: auto; }}
                    th, td {{ border: 1px solid #ccc; padding: 5px; text-align: left; }}
                    th {{ background-color: #ecf0f1; }}
                    .table {{ width: 100%; }}
                    .title-page {{ text-align:center; page-break-after: always; }}
                    .title-page h1 {{ border-bottom: none; page-break-before: auto; }}
                </style>
            </head>
            <body>
                <div class="title-page">
                    <h1>Relatório Geral de Criação de Aves</h1>
                    <p>Gerado em: {datetime.now(datetime.now().astimezone().tzinfo).strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                {full_html}
            </body>
        </html>
        """
        
        pdf_bytes = HTML(string=final_html).write_pdf()
        return dcc.send_bytes(pdf_bytes, "relatorio_geral_aves.pdf"), dbc.Alert("Relatório gerado com sucesso!", color="success", duration=3000)