import datetime

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from apps.relatorios.forms import FiltroRelatorioForm
from apps.relatorios.services.analytics import gerar_relatorio_completo
from apps.relatorios.services.exports import exportar_pdf, exportar_excel


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

    dados = gerar_relatorio_completo(filtros)

    context = {
        'form': form,
        'ranking_etapa': dados['ranking_etapa'],
        'media_dias_etapa': dados['media_dias_etapa'],
        'media_individual': dados['media_individual'],
        'title': 'Relatórios de Produção',
        'filtros_aplicados': filtros,
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
