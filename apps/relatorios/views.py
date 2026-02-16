import datetime

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse

from apps.relatorios.forms import FiltroRelatorioForm
from apps.relatorios.services.analytics import gerar_relatorio_completo, apontamentos_periodo
from apps.relatorios.services.exports import exportar_pdf, exportar_excel
from apps.funcionarios.models import ApontamentoFuncionario
from apps.obras.models import Etapa
from django.shortcuts import get_object_or_404
import csv


# ═══════════════════════════════════════════
#  Dashboard principal de relatórios
# ═══════════════════════════════════════════

@login_required
def relatorio_dashboard(request):
    """Tela principal dos relatórios com filtros e as 3 análises.
    Os dados vêm diretamente dos apontamentos diários (ApontamentoFuncionario).
    """
    form = FiltroRelatorioForm(request.GET or None)
    filtros = form.get_filtros() if form.is_valid() else {}
    filtros_informados = bool(filtros)

    if filtros_informados:
        dados = gerar_relatorio_completo(filtros)
        apontamentos = apontamentos_periodo(filtros)
    else:
        dados = {
            'ranking_etapa': [],
            'media_dias_etapa': [],
            'media_individual': [],
        }
        apontamentos = []

    context = {
        'form': form,
        'ranking_etapa': dados['ranking_etapa'],
        'media_dias_etapa': dados['media_dias_etapa'],
        'media_individual': dados['media_individual'],
        'apontamentos_periodo': apontamentos,
        'title': 'Relatórios de Produção',
        'filtros_aplicados': filtros,
        'filtros_informados': filtros_informados,
    }
    return render(request, 'relatorios/dashboard.html', context)


# ═══════════════════════════════════════════
#  Exportações
# ═══════════════════════════════════════════

@login_required
def exportar_relatorio_pdf(request):
    """Exporta o relatório completo em PDF."""
    form = FiltroRelatorioForm(request.GET or None)
    filtros = form.get_filtros() if form.is_valid() else {}

    buf = exportar_pdf(filtros)

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    response = HttpResponse(buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="relatorio_producao_{ts}.pdf"'
    return response


@login_required
def exportar_relatorio_excel(request):
    """Exporta o relatório completo em Excel."""
    form = FiltroRelatorioForm(request.GET or None)
    filtros = form.get_filtros() if form.is_valid() else {}

    buf = exportar_excel(filtros)

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    ct = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response = HttpResponse(buf.read(), content_type=ct)
    response['Content-Disposition'] = f'attachment; filename="relatorio_producao_{ts}.xlsx"'
    return response


@login_required
def relatorio_funcionario_diario(request):
    """Exporta todos os apontamentos de um funcionário em uma data (CSV).
    Não filtra por `metragem_executada`; retorna tudo do funcionário naquele dia.
    Espera parâmetros GET: `funcionario` (id) e `data` (YYYY-MM-DD).
    """
    funcionario_id = request.GET.get('funcionario')
    data_str = request.GET.get('data')
    if not funcionario_id or not data_str:
        return HttpResponse('Parâmetros "funcionario" e "data" são obrigatórios', status=400)

    try:
        data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse('Formato de data inválido. Use YYYY-MM-DD.', status=400)

    apontamentos = ApontamentoFuncionario.objects.filter(
        funcionario_id=funcionario_id,
        data=data
    ).order_by('id')

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    filename = f'relatorio_func_{funcionario_id}_{data_str}_{ts}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['id', 'funcionario_id', 'funcionario_nome', 'obra', 'etapa', 'data', 'horas_trabalhadas', 'metragem_executada', 'valor_diaria', 'observacoes'])
    for a in apontamentos:
        # etapa label if available
        etapa_label = ''
        try:
            if getattr(a, 'etapa', None):
                etapa_label = a.etapa.get_numero_etapa_display()
        except Exception:
            etapa_label = ''
        writer.writerow([
            a.pk,
            a.funcionario_id,
            getattr(a.funcionario, 'nome_completo', ''),
            getattr(a.obra, 'nome', '') if a.obra else '',
            etapa_label,
            a.data.isoformat(),
            a.horas_trabalhadas,
            a.metragem_executada,
            a.valor_diaria,
            a.observacoes or '',
        ])

    return response


@login_required
def etapas_por_obra(request):
    """Retorna etapas de uma obra em JSON para filtro dinâmico."""
    obra_id = request.GET.get('obra_id')
    if not obra_id:
        return JsonResponse({'etapas': []})

    try:
        obra_id = int(obra_id)
    except (TypeError, ValueError):
        return JsonResponse({'etapas': []})

    etapas = Etapa.objects.filter(obra_id=obra_id).order_by('numero_etapa')
    data = [
        {
            'id': e.id,
            'nome': e.get_numero_etapa_display(),
        }
        for e in etapas
    ]
    return JsonResponse({'etapas': data})
