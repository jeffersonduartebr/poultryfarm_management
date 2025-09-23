# dashboard/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Lotes, ProducaoOvos
from .forms import ProducaoOvosForm
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
import plotly.io as pio

@login_required
def dashboard_view(request):
    # Lógica para a aba "Visão Geral" pode ser adicionada aqui
    context = {'page': 'dashboard'}
    return render(request, 'dashboard/base.html', context)

@login_required
def producao_view(request):
    lotes = Lotes.objects.filter(status='Ativo')
    selected_lote_id = request.GET.get('lote_id')
    producao_recente = None

    if selected_lote_id:
        producao_recente = ProducaoOvos.objects.filter(
            lote_id=selected_lote_id
        ).order_by('-data_producao')[:7]

    if request.method == 'POST':
        form = ProducaoOvosForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f"{request.path}?lote_id={form.cleaned_data['lote'].id}")
    else:
        form = ProducaoOvosForm()

    context = {
        'page': 'producao',
        'lotes': lotes,
        'form': form,
        'producao_recente': producao_recente,
        'selected_lote_id': selected_lote_id
    }
    return render(request, 'dashboard/producao.html', context)
    
    
@login_required
def visao_geral_view(request, lote_id):
    # 1. Busque os dados do banco com o ORM do Django
    dados = ProducaoAves.objects.filter(lote_id=lote_id).order_by('semana_idade')
    
    # 2. Crie o gráfico com Plotly
    fig = px.line(
        x=[d.semana_idade for d in dados],
        y=[d.peso_medio for d in dados],
        title="Evolução do Peso Médio"
    )

    # 3. Converta o gráfico para HTML
    grafico_html = pio.to_html(fig, full_html=False)

    context = {
        'grafico_html': grafico_html,
    }
    return render(request, 'dashboard/visao_geral.html', context)    