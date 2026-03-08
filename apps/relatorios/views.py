import csv
import datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from apps.funcionarios.models import ApontamentoFuncionario
from apps.obras.models import Etapa
from apps.relatorios.forms import FiltroRelatorioForm
from apps.relatorios.services.analytics import gerar_relatorio_completo, apontamentos_periodo
from apps.relatorios.services.analytics_indicadores import gerar_relatorio_completo_indicadores
from apps.relatorios.services.exports import exportar_pdf, exportar_excel


def _build_pagination_context(request, page_obj, param_name):
    query_params = request.GET.copy()
    query_params.pop(param_name, None)

    def _url(page_number):
        p = query_params.copy()
        p[param_name] = page_number
        return f'?{p.urlencode()}'

    return {
        'page_obj': page_obj,
        'pages': list(page_obj.paginator.page_range),
        'first_url': _url(1),
        'last_url': _url(page_obj.paginator.num_pages),
        'prev_url': _url(page_obj.previous_page_number()) if page_obj.has_previous() else None,
        'next_url': _url(page_obj.next_page_number()) if page_obj.has_next() else None,
    }


@login_required
def relatorio_dashboard(request):
    """Tela principal dos relatórios com filtros e análises."""
    form = FiltroRelatorioForm(request.GET or None)
    filtros = form.get_filtros() if form.is_valid() else {}
    filtros_informados = bool(filtros)

    dados = gerar_relatorio_completo_indicadores(filtros if filtros_informados else None)
    apontamentos = apontamentos_periodo(filtros if filtros_informados else None)

    media_individual_lista = dados['media_individual']
    paginator_media = Paginator(media_individual_lista, 10)
    media_page_obj = paginator_media.get_page(request.GET.get('page_media', 1))
    media_pag = _build_pagination_context(request, media_page_obj, 'page_media')

    paginator_apontamentos = Paginator(apontamentos, 10)
    apontamentos_page_obj = paginator_apontamentos.get_page(request.GET.get('page_apontamentos', 1))
    apontamentos_pag = _build_pagination_context(request, apontamentos_page_obj, 'page_apontamentos')

    export_params = request.GET.copy()
    export_params.pop('page_media', None)
    export_params.pop('page_apontamentos', None)
    export_querystring = export_params.urlencode()

    context = {
        'form': form,
        'ranking_por_etapas': dados['ranking_por_etapas'],
        'media_dias_etapa': dados['media_dias_etapa'],
        'media_individual': media_page_obj,
        'media_individual_total': len(media_individual_lista),
        'media_pag': media_pag,
        'rankings_indicadores': dados.get('rankings_indicadores', {}),
        'apontamentos_periodo': apontamentos_page_obj,
        'apontamentos_total': len(apontamentos),
        'apontamentos_pag': apontamentos_pag,
        'title': 'Relatórios de Produção - Por Indicador',
        'filtros_aplicados': filtros,
        'filtros_informados': filtros_informados,
        'export_querystring': export_querystring,
    }
    return render(request, 'relatorios/dashboard.html', context)


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
    """Exporta todos os apontamentos de um funcionário em uma data (CSV)."""
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
        data=data,
    ).exclude(
        funcionario__funcao='fiscal'
    ).order_by('id')

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    filename = f'relatorio_func_{funcionario_id}_{data_str}_{ts}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'id',
        'funcionario_id',
        'funcionario_nome',
        'obra',
        'etapa',
        'data',
        'horas_trabalhadas',
        'metragem_executada',
        'valor_diaria',
        'observacoes',
    ])
    for a in apontamentos:
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
    data = [{'id': e.id, 'nome': e.get_numero_etapa_display()} for e in etapas]
    return JsonResponse({'etapas': data})

