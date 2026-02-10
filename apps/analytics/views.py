from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .services import AnalyticsService
from apps.funcionarios.models import Funcionario
from apps.obras.models import Obra
from apps.clientes.models import Cliente
from django.db.models import Avg
from datetime import datetime
from dateutil.relativedelta import relativedelta


@login_required
def dashboard(request):
    """Dashboard principal com métricas gerais"""
    analytics = AnalyticsService()
    dados = analytics.dashboard_geral()

    # Build metrics expected by the template
    metrics = {
        'total_obras': dados.get('obras', {}).get('total', 0),
        'obras_em_andamento': dados.get('obras', {}).get('em_andamento', 0),
        'total_clientes': Cliente.objects.count(),
        'avg_percentual': float(Obra.objects.filter(ativo=True).aggregate(avg=Avg('percentual_concluido'))['avg'] or 0),
        'custo_mes': dados.get('financeiro', {}).get('custo_mes', 0),
        'horas_mes': dados.get('financeiro', {}).get('horas_mes', 0),
        'ociosidades_mes': dados.get('ocorrencias', {}).get('ociosidades_mes', 0),
        'retrabalhos_mes': dados.get('ocorrencias', {}).get('retrabalhos_mes', 0),
    }

    # Obras em andamento queryset (limit to 10)
    obras_em_andamento = Obra.objects.filter(status='em_andamento', ativo=True).order_by('-percentual_concluido')[:10]

    # Chart data: average percentual for the last 12 months by creation month
    labels = []
    values = []
    hoje = datetime.now().date()
    for i in range(11, -1, -1):
        mes = hoje - relativedelta(months=i)
        month_start = mes.replace(day=1)
        # get next month start
        next_month = month_start + relativedelta(months=1)
        avg = Obra.objects.filter(created_at__gte=month_start, created_at__lt=next_month, ativo=True).aggregate(avg=Avg('percentual_concluido'))['avg'] or 0
        labels.append(month_start.strftime('%b/%Y'))
        values.append(float(avg))

    context = {
        'metrics': metrics,
        'chart_labels': labels,
        'chart_values': values,
        'obras_em_andamento': obras_em_andamento,
        'title': 'Dashboard'
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
def rankings(request):
    """Rankings de pedreiros por etapa"""
    analytics = AnalyticsService()
    
    # Rankings para cada etapa
    rankings_etapas = {}
    for i in range(1, 6):
        rankings_etapas[i] = analytics.ranking_pedreiros_por_etapa(i)
    
    # Média de dias por etapa
    media_etapas = analytics.media_dias_por_etapa()
    
    context = {
        'rankings_etapas': rankings_etapas,
        'media_etapas': media_etapas,
        'title': 'Rankings e Análises'
    }
    return render(request, 'analytics/rankings.html', context)


@login_required
def pedreiro_rendimento(request, pk):
    """Análise de rendimento individual de um pedreiro"""
    pedreiro = get_object_or_404(Funcionario, pk=pk, funcao='pedreiro')
    analytics = AnalyticsService()
    
    rendimento = analytics.rendimento_individual_pedreiro(pk)
    historico = analytics.historico_funcionario_semanal(pk)
    
    context = {
        'pedreiro': pedreiro,
        'rendimento': rendimento,
        'historico': historico,
        'title': f'Rendimento - {pedreiro.nome_completo}'
    }
    return render(request, 'analytics/pedreiro_rendimento.html', context)


@login_required
def obra_custos(request, pk):
    """Análise de custos de uma obra"""
    obra = get_object_or_404(Obra, pk=pk)
    analytics = AnalyticsService()
    
    custos = analytics.custo_mao_obra_por_obra(pk)
    
    context = {
        'obra': obra,
        'custos': custos,
        'title': f'Custos - {obra.nome}'
    }
    return render(request, 'analytics/obra_custos.html', context)
