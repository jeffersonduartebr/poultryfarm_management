from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import text
from db import get_engine
import dash_bootstrap_components as dbc
import dash
from dash import html, dcc

# Imports para geração de PDF
import base64
from weasyprint import HTML
from datetime import datetime

# Conexão compartilhada com o banco de dados
engine = get_engine()

def register_callbacks(app):
    """Registra todos os callbacks da aplicação."""

    # Importa os layouts para evitar dependência circular
    from layout import (insert_weekly_layout, view_layout, insert_daily_layout, 
                        bedding_layout, bait_layout, visits_layout, treat_layout, 
                        reports_layout)

    # =============================================================================
    # Callback Principal para Renderização de Abas
    # =============================================================================
    @app.callback(
        Output('tab-content', 'children'),
        Input('tabs', 'value')
    )
    def render_content(tab):
        layouts = {
            'tab-insert-weekly': insert_weekly_layout,
            'tab-view': view_layout,
            'tab-insert-daily': insert_daily_layout,
            'tab-bedding': bedding_layout,
            'tab-bait': bait_layout,
            'tab-visits': visits_layout,
            'tab-treat': treat_layout,
            'tab-reports': reports_layout
        }
        layout_function = layouts.get(tab)
        if layout_function:
            return layout_function()
        return html.Div()

    # =============================================================================
    # Callbacks da Aba "Visualizar Indicadores"
    # =============================================================================
    @app.callback(
        Output("graph-peso-medio", "figure"),
        Output("graph-mortalidade", "figure"),
        Output("graph-consumo", "figure"),
        Output("graph-mortalidade-acumulada", "figure"),
        Output("graph-consumo-comparativo", "figure"),
        Input("dropdown-aviario-indicadores", "value")
    )
    def atualizar_graficos(aviario):
        if not aviario:
            return go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()
        
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT * FROM producao_aves WHERE aviario = :av ORDER BY semana_idade"), conn, params={"av": aviario})
        
        if df.empty:
            return go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()

        fig_peso = px.line(df, x="semana_idade", y="peso_med", title="Peso Médio por Semana")
        fig_mort = px.bar(df, x="semana_idade", y="mort_total", title="Mortalidade Semanal")
        fig_cons = px.line(df, x="semana_idade", y="consumo_real", title="Consumo Real por Semana")
        df["mort_acum"] = df["mort_total"].cumsum()
        fig_mort_acum = px.line(df, x="semana_idade", y="mort_acum", title="Mortalidade Acumulada")
        
        fig_cons_comp = go.Figure()
        fig_cons_comp.add_trace(go.Scatter(x=df["semana_idade"], y=df["consumo_acum_real"], mode='lines+markers', name='Real'))
        fig_cons_comp.add_trace(go.Scatter(x=df["semana_idade"], y=pd.to_numeric(df["consumo_acum_padrao"], errors='coerce'), mode='lines+markers', name='Padrão'))
        fig_cons_comp.update_layout(title="Consumo Acumulado: Real vs Padrão")
        
        return fig_peso, fig_mort, fig_cons, fig_mort_acum, fig_cons_comp

    # =============================================================================
    # Callbacks da Aba "Inserir Dados Semanais"
    # =============================================================================
    @app.callback(
        Output("input-mort-total", "value"),
        Output("input-mort-acum", "value"),
        [Input(f"input-mort-dia-{i}", "value") for i in range(1, 8)],
        State("input-aviario", "value"),
        State("input-semana", "value")
    )
    def atualizar_mortalidade(*vals):
        dias = vals[:-2]
        aviario, semana_atual = vals[-2], vals[-1]
        total_corrente = sum(v or 0 for v in dias)
        
        if not aviario or not semana_atual:
            return total_corrente, total_corrente

        try:
            with engine.connect() as conn:
                query = text("SELECT COALESCE(SUM(mort_total), 0) FROM producao_aves WHERE aviario = :av AND semana_idade < :sem")
                historico = conn.execute(query, {"av": aviario, "sem": semana_atual}).scalar() or 0
            return total_corrente, historico + total_corrente
        except Exception:
            return total_corrente, total_corrente
            
    # =============================================================================
    # Callbacks para Inserção de Dados (um para cada aba de formulário)
    # =============================================================================
    @app.callback(
        Output("submit-status-weekly", "children"),
        Input("btn-submit-weekly", "n_clicks"),
        [State("input-aviario", "value"), State("input-n-aves", "value"), State("input-peso-medio", "value"),
         State("input-semana", "value"), State("input-aves-semana", "value"),
         *[State(f"input-mort-dia-{i}", "value") for i in range(1, 8)],
         State("input-mort-total", "value"), State("input-mort-acum", "value"),
         State("input-data-pesagem", "date"), State("input-peso-med", "value"),
         State("input-peso-min", "value"), State("input-peso-max", "value"),
         State("input-consumo-real", "value"), State("input-consumo-padrao", "value")]
    )
    def insert_weekly(n_clicks, *args):
        if not n_clicks: return ""
        try:
            (aviario, n_aves, peso_medio, semana, aves_semana, 
             d1, d2, d3, d4, d5, d6, d7, 
             mort_total, mort_acum, dt_pesagem, peso_med_sem, 
             peso_min, peso_max, consumo_real, consumo_padrao) = args

            with engine.begin() as conn:
                # Lógica para inserir no banco...
                pass # Adicionar a lógica de inserção aqui
            return dbc.Alert("Dados semanais inseridos!", color="success")
        except Exception as e:
            return dbc.Alert(f"Erro ao inserir: {e}", color="danger")

    @app.callback(
        Output("daily-submit-status", "children"),
        Input("btn-daily-submit", "n_clicks"),
        [State("daily-date", "date"), State("daily-aviario", "value"), State("daily-total-birds", "value"), State("daily-total-eggs", "value")]
    )
    def insert_daily(n_clicks, data, aviario, birds, eggs):
        if not n_clicks: return ""
        if not all([data, aviario, birds, eggs]): return dbc.Alert("Preencha todos os campos.", color="warning")
        
        pct = (eggs / birds * 100) if birds else 0
        try:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO producao_diaria (data, aviario, total_birds, total_eggs, pct_production) VALUES (:data, :aviario, :birds, :eggs, :pct)"), 
                             {"data": data, "aviario": aviario, "birds": birds, "eggs": eggs, "pct": pct})
            return dbc.Alert("Produção diária registrada!", color="success")
        except Exception as e:
            return dbc.Alert(f"Erro: {e}", color="danger")
    def insert_bedding(n, lot, imp, mat, rem, treat, dest, contact):
        if not n: return ""
        if not (lot and imp): return dbc.Alert("Preencha datas de alojamento e implantação.", color="danger")
        try:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO registro_camas (date_lot, date_implant, material, date_remove, treatment, destination, contact) VALUES (:lot, :imp, :mat, :rem, :treat, :dest, :contact)"),
                             {"lot": lot, "imp": imp, "mat": mat, "rem": rem, "treat": treat, "dest": dest, "contact": contact})
            return dbc.Alert("Registro de cama inserido com sucesso!", color="success")
        except Exception as e:
            return dbc.Alert(f"Erro: {e}", color="danger")

    @app.callback(
        Output("bait-submit-status", "children"),
        Input("btn-bait-submit", "n_clicks"),
        State("field-n_isca", "value"), State("field-produto", "value"),
        State("field-local", "value"), State("field-data-vistoria", "date"),
        State("field-consumida", "value"), State("field-intacta", "value"),
        State("field-mofada", "value"), State("field-responsavel", "value"),
        prevent_initial_call=True
    )
    def insert_bait(n_clicks, n_isca, produto, local, data_vistoria, consumida, intacta, mofada, responsavel):
        if n_clicks is None: return ""
        if not all([n_isca, produto, local, data_vistoria, responsavel]):
             return dbc.Alert("Preencha todos os campos obrigatórios da inspeção.", color="warning")
        try:
            qry = text("INSERT INTO iscas (n_isca, produto, local, data_vistoria, consumida, intacta, mofada, responsavel) VALUES (:n_isca, :produto, :local, :data_vistoria, :consumida, :intacta, :mofada, :responsavel)")
            with engine.begin() as conn:
                conn.execute(qry, {"n_isca": n_isca, "produto": produto, "local": local, "data_vistoria": data_vistoria, "consumida": consumida or 0, "intacta": intacta or 0, "mofada": mofada or 0, "responsavel": responsavel})
            return dbc.Alert("✅ Inspeção salva com sucesso.", color="success")
        except Exception as e:
            return dbc.Alert(f"❌ Erro ao salvar inspeção: {e}", color="danger")

    @app.callback(
        Output("visits-submit-status", "children"),
        Input("btn-visits-submit", "n_clicks"),
        State("visit-date", "date"), State("visit-objetivo", "value"),
        State("visit-contato", "value"), State("visit-placa", "value"),
        State("visit-assinatura", "value"),
        prevent_initial_call=True
    )
    def insert_visits(n_clicks, data, objetivo, contato, placa, assinatura):
        if n_clicks is None: return ""
        if not data: return dbc.Alert("⚠️ Data da visita é obrigatória.", color="warning")
        try:
            qry = text("INSERT INTO visitas (data, objetivo, contato, placa, assinatura) VALUES (:data, :objetivo, :contato, :placa, :assinatura)")
            with engine.begin() as conn:
                conn.execute(qry, {"data": data, "objetivo": objetivo, "contato": contato, "placa": placa, "assinatura": assinatura})
            return dbc.Alert("✅ Registro de visita salvo com sucesso.", color="success")
        except Exception as e:
            return dbc.Alert(f"❌ Erro ao salvar visita: {e}", color="danger")

    @app.callback(
        Output("treat-submit-status", "children"),
        Input("btn-treat-submit", "n_clicks"),
        State("treat-aviario", "value"), State("treat-medicacao", "value"),
        State("treat-inicio", "date"), State("treat-termino", "date"),
        State("treat-forma", "value"), State("treat-motivo", "value"),
        prevent_initial_call=True
    )
    def insert_treatments(n_clicks, aviario, medicacao, data_inicio, data_termino, forma_admin, motivacao):
        if n_clicks is None: return ""
        if not all([aviario, medicacao, data_inicio]):
            return dbc.Alert("⚠️ Aviário, Medicação e Data de início são obrigatórios.", color="warning")
        try:
            qry = text("INSERT INTO tratamentos (aviario, medicacao, data_inicio, data_termino, forma_admin, motivacao) VALUES (:aviario, :medicacao, :data_inicio, :data_termino, :forma_admin, :motivacao)")
            with engine.begin() as conn:
                conn.execute(qry, {"aviario": aviario, "medicacao": medicacao, "data_inicio": data_inicio, "data_termino": data_termino, "forma_admin": forma_admin, "motivacao": motivacao})
            return dbc.Alert("✅ Tratamento salvo com sucesso.", color="success")
        except Exception as e:
            return dbc.Alert(f"❌ Erro ao salvar tratamento: {e}", color="danger")

    @app.callback(
        Output("daily-pct", "value"),
        Input("daily-total-eggs", "value"),
        Input("daily-total-birds", "value"),
        prevent_initial_call=True
    )
    def calc_pct(eggs, birds):
        if not birds or birds == 0: return 0
        return round((eggs or 0) / birds * 100, 2)

# =============================================================================
    # Callbacks para Atualização de Tabelas de Histórico
    # =============================================================================
    @app.callback(
        Output("bait-history-table", "data"), Output("bait-history-table", "columns"),
        [Input("tabs", "value"), Input("btn-bait-submit", "n_clicks")]
    )
    def update_bait_table(tab, n_clicks):
        if tab != 'tab-bait': raise dash.exceptions.PreventUpdate
        df = pd.read_sql("SELECT n_isca as 'Nº Isca', produto as Produto, local as Local, data_vistoria as Data, consumida as Consumida, intacta as Intacta, mofada as Mofada, responsavel as Responsável FROM iscas ORDER BY id DESC LIMIT 5", engine)
        return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]

    @app.callback(
        Output("visits-history-table", "data"), Output("visits-history-table", "columns"),
        [Input("tabs", "value"), Input("btn-visits-submit", "n_clicks")]
    )
    def update_visits_table(tab, n_clicks):
        if tab != 'tab-visits': raise dash.exceptions.PreventUpdate
        df = pd.read_sql("SELECT data as Data, objetivo as Objetivo, contato as Contato, placa as Placa, assinatura as Assinatura FROM visitas ORDER BY id DESC LIMIT 5", engine)
        return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]

    @app.callback(
        Output("treatments-history-table", "data"), Output("treatments-history-table", "columns"),
        [Input("tabs", "value"), Input("btn-treat-submit", "n_clicks")]
    )
    def update_treatments_table(tab, n_clicks):
        if tab != 'tab-treat': raise dash.exceptions.PreventUpdate
        df = pd.read_sql("SELECT aviario as Aviário, medicacao as Medicação, data_inicio as Início, data_termino as Término, forma_admin as 'Forma Admin.', motivacao as Motivação FROM tratamentos ORDER BY id DESC LIMIT 5", engine)
        return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]

    # =============================================================================
    # Callback da Aba "Relatórios"
    # =============================================================================
    @app.callback(
        Output("download-pdf-report", "data"),
        Output("report-generation-status", "children"),
        Input("btn-generate-report", "n_clicks"),
        State("report-sections-checklist", "value")
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