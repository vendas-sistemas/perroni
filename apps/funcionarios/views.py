from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Funcionario, ApontamentoFuncionario, FechamentoSemanal
from .forms import (
    FuncionarioForm, ApontamentoForm, FechamentoForm,
    ApontamentoDiarioCabecalhoForm, ApontamentoDiarioItemForm,
)
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode
from apps.obras.models import Obra, Etapa
from django.db import IntegrityError
from django.db.models import Sum, Count, Q, Avg, F
import datetime
from decimal import Decimal
from collections import defaultdict
import calendar


@login_required
def funcionario_list(request):
    """Lista funcionários"""
    funcionarios = Funcionario.objects.filter(ativo=True).order_by('nome_completo')
    context = {
        'funcionarios': funcionarios,
        'title': 'Funcionários'
    }
    return render(request, 'funcionarios/funcionario_list.html', context)


@login_required
def funcionario_detail(request, pk):
    """Detalhes de um funcionário"""
    funcionario = get_object_or_404(Funcionario, pk=pk)
    context = {
        'funcionario': funcionario,
        'title': funcionario.nome_completo
    }
    return render(request, 'funcionarios/funcionario_detail.html', context)


@login_required
def funcionario_create(request):
    """Cadastra novo funcionário"""
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            funcionario = form.save()
            messages.success(request, 'Funcionário criado com sucesso.')
            return redirect('funcionarios:funcionario_detail', pk=funcionario.pk)
        else:
            messages.error(request, 'Corrija os erros no formulário.')
    else:
        form = FuncionarioForm()
    return render(request, 'funcionarios/funcionario_form.html', {'form': form, 'title': 'Novo Funcionário'})


@login_required
def funcionario_update(request, pk):
    """Atualiza funcionário"""
    funcionario = get_object_or_404(Funcionario, pk=pk)
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES, instance=funcionario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funcionário atualizado com sucesso.')
            return redirect('funcionarios:funcionario_detail', pk=funcionario.pk)
        else:
            messages.error(request, 'Corrija os erros no formulário.')
    else:
        form = FuncionarioForm(instance=funcionario)
    return render(request, 'funcionarios/funcionario_form.html', {'form': form, 'funcionario': funcionario, 'title': 'Editar Funcionário'})


@login_required
def funcionario_inativar(request, pk):
    """Inativa um funcionário"""
    funcionario = get_object_or_404(Funcionario, pk=pk)
    return render(request, 'funcionarios/funcionario_inativar.html', {
        'funcionario': funcionario,
        'title': 'Inativar Funcionário'
    })


# ==================== APONTAMENTOS ====================

@login_required
def apontamento_list(request):
    """Lista apontamentos com filtros avançados"""
    qs = ApontamentoFuncionario.objects.all().select_related(
        'funcionario', 'obra', 'etapa'
    ).order_by('-data', '-created_at')

    # Filters from GET
    data = request.GET.get('data')
    funcionario_id = request.GET.get('funcionario')
    obra_id = request.GET.get('obra')
    etapa_id = request.GET.get('etapa')
    clima = request.GET.get('clima')
    ociosidade = request.GET.get('ociosidade')
    retrabalho = request.GET.get('retrabalho')

    if data:
        qs = qs.filter(data=data)
    if funcionario_id:
        qs = qs.filter(funcionario_id=funcionario_id)
    if obra_id:
        qs = qs.filter(obra_id=obra_id)
    if etapa_id:
        qs = qs.filter(etapa_id=etapa_id)
    if clima:
        qs = qs.filter(clima=clima)
    if ociosidade == '1':
        qs = qs.filter(houve_ociosidade=True)
    if retrabalho == '1':
        qs = qs.filter(houve_retrabalho=True)

    # Totals for current filter
    totais = qs.aggregate(
        total_horas=Sum('horas_trabalhadas'),
        total_valor=Sum('valor_diaria'),
        total_registros=Count('id'),
        total_ociosidade=Count('id', filter=Q(houve_ociosidade=True)),
        total_retrabalho=Count('id', filter=Q(houve_retrabalho=True)),
    )

    # Pagination
    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    params = request.GET.copy()
    if 'page' in params:
        params.pop('page')
    querystring = params.urlencode()

    context = {
        'apontamentos': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'querystring': querystring,
        'totais': totais,
        'funcionarios': Funcionario.objects.filter(ativo=True).order_by('nome_completo'),
        'obras': Obra.objects.filter(ativo=True).order_by('nome'),
        'title': 'Apontamentos'
    }
    return render(request, 'funcionarios/apontamento_list.html', context)


@login_required
def apontamento_create(request):
    """Cria apontamento individual"""
    if request.method == 'POST':
        form = ApontamentoForm(request.POST)
        if form.is_valid():
            ap = form.save(commit=False)
            if not ap.valor_diaria:
                ap.valor_diaria = ap.funcionario.valor_diaria
            ap.save()
            # Notificação de retrabalho/ociosidade
            if ap.houve_retrabalho:
                messages.warning(request, f'⚠️ RETRABALHO registrado para {ap.funcionario.nome_completo}.')
            if ap.houve_ociosidade:
                messages.warning(request, f'⚠️ OCIOSIDADE registrada para {ap.funcionario.nome_completo}.')
            messages.success(request, 'Apontamento salvo com sucesso.')
            return redirect('funcionarios:apontamento_list')
        else:
            messages.error(request, 'Corrija os erros no formulário.')
    else:
        form = ApontamentoForm()
    return render(request, 'funcionarios/apontamento_form.html', {'form': form, 'title': 'Novo Apontamento'})


@login_required
def apontamento_diario(request):
    """
    Fluxo principal de apontamento diário:
    1. Fiscal seleciona obra + data + clima
    2. Adiciona funcionários com etapa, horas, ociosidade, retrabalho
    """
    cab_form = ApontamentoDiarioCabecalhoForm(request.GET or None)
    obra = None
    data = None
    clima = None
    apontamentos_existentes = []
    item_form = None
    etapas = []

    # Step 1: Check if obra + data are set
    obra_id = request.GET.get('obra') or request.POST.get('obra')
    data_str = request.GET.get('data') or request.POST.get('data_apontamento')
    clima_sel = request.GET.get('clima') or request.POST.get('clima_apontamento')

    if obra_id and data_str:
        try:
            obra = Obra.objects.get(pk=obra_id)
            data = datetime.date.fromisoformat(data_str)
            clima = clima_sel or 'sol'
        except (Obra.DoesNotExist, ValueError):
            pass

    if obra and data:
        etapas = Etapa.objects.filter(obra=obra)
        apontamentos_existentes = ApontamentoFuncionario.objects.filter(
            obra=obra, data=data
        ).select_related('funcionario', 'etapa')

        # Already appointed funcionarios on this date (any obra)
        appointed_ids = ApontamentoFuncionario.objects.filter(
            data=data
        ).values_list('funcionario_id', flat=True)

        # Set initial values for cab_form
        cab_form = ApontamentoDiarioCabecalhoForm(initial={
            'obra': obra.pk, 'data': data, 'clima': clima
        })

        if request.method == 'POST' and 'add_funcionario' in request.POST:
            item_form = ApontamentoDiarioItemForm(request.POST, obra_id=obra.pk)
            if item_form.is_valid():
                ap = item_form.save(commit=False)
                ap.obra = obra
                ap.data = data
                ap.clima = clima
                if not ap.valor_diaria:
                    ap.valor_diaria = ap.funcionario.valor_diaria
                try:
                    ap.save()
                    if ap.houve_retrabalho:
                        messages.warning(request, f'⚠️ RETRABALHO: {ap.funcionario.nome_completo} - {ap.motivo_retrabalho}')
                    if ap.houve_ociosidade:
                        messages.warning(request, f'⚠️ OCIOSIDADE: {ap.funcionario.nome_completo} - {ap.observacao_ociosidade}')
                    messages.success(request, f'{ap.funcionario.nome_completo} apontado com sucesso.')
                    return redirect(f'{request.path}?obra={obra.pk}&data={data.isoformat()}&clima={clima}')
                except IntegrityError:
                    messages.error(request, 'Funcionário já apontado nesta data.')
            else:
                messages.error(request, 'Corrija os erros abaixo.')
        else:
            item_form = ApontamentoDiarioItemForm(obra_id=obra.pk, initial={
                'horas_trabalhadas': Decimal('8.0'),
            })

    context = {
        'cab_form': cab_form,
        'obra': obra,
        'data': data,
        'clima': clima,
        'etapas': etapas,
        'apontamentos_existentes': apontamentos_existentes,
        'item_form': item_form,
        'title': 'Apontamento Diário'
    }
    return render(request, 'funcionarios/apontamento_diario.html', context)


@login_required
def apontamento_delete(request, pk):
    """Remove um apontamento"""
    ap = get_object_or_404(ApontamentoFuncionario, pk=pk)
    obra_id = ap.obra_id
    data = ap.data
    if request.method == 'POST':
        ap.delete()
        messages.success(request, 'Apontamento removido.')
        # Redirect back to diario if referer suggests it
        next_url = request.POST.get('next', '')
        if next_url:
            return redirect(next_url)
    return redirect('funcionarios:apontamento_list')


# ==================== FECHAMENTOS ====================

@login_required
def fechamento_list(request):
    """Lista fechamentos semanais"""
    fechamentos = FechamentoSemanal.objects.all().select_related('funcionario')
    context = {
        'fechamentos': fechamentos,
        'title': 'Fechamentos Semanais'
    }
    return render(request, 'funcionarios/fechamento_list.html', context)


@login_required
def fechamento_create(request):
    """Cria um fechamento semanal e calcula os totais"""
    if request.method == 'POST':
        form = FechamentoForm(request.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.data_fim = f.data_inicio + datetime.timedelta(days=6)
            f.status = 'aberto'
            # Check duplicate
            existing = FechamentoSemanal.objects.filter(
                funcionario=f.funcionario,
                data_inicio=f.data_inicio,
                data_fim=f.data_fim
            ).first()
            if existing:
                messages.warning(request, 'Já existe um fechamento para esse funcionário e período.')
                return redirect('funcionarios:fechamento_detail', pk=existing.pk)
            try:
                f.save()
            except IntegrityError:
                messages.error(request, 'Erro ao salvar: já existe um fechamento para esse funcionário e período.')
                return redirect('funcionarios:fechamento_list')
            f.calcular_totais()
            messages.success(request, 'Fechamento criado e totais calculados.')
            return redirect('funcionarios:fechamento_detail', pk=f.pk)
        else:
            messages.error(request, 'Corrija os erros no formulário.')
    else:
        form = FechamentoForm()
    return render(request, 'funcionarios/fechamento_form.html', {'form': form, 'title': 'Novo Fechamento Semanal'})


@login_required
def fechamento_detail(request, pk):
    """Detalhes de um fechamento semanal"""
    fechamento = get_object_or_404(FechamentoSemanal, pk=pk)
    apontamentos = fechamento.get_apontamentos()
    obras_etapas = fechamento.get_obras_etapas()
    context = {
        'fechamento': fechamento,
        'apontamentos': apontamentos,
        'obras_etapas': obras_etapas,
        'title': f'Fechamento - {fechamento.funcionario.nome_completo}'
    }
    return render(request, 'funcionarios/fechamento_detail.html', context)


@login_required
def fechamento_auto(request):
    """Gera fechamentos semanais automaticamente para todos os funcionários ativos"""
    if request.method == 'POST':
        data_inicio_str = request.POST.get('data_inicio')
        if not data_inicio_str:
            messages.error(request, 'Informe a data de início da semana.')
            return redirect('funcionarios:fechamento_auto')

        try:
            data_inicio = datetime.date.fromisoformat(data_inicio_str)
        except ValueError:
            messages.error(request, 'Data inválida.')
            return redirect('funcionarios:fechamento_auto')

        data_fim = data_inicio + datetime.timedelta(days=6)
        funcionarios = Funcionario.objects.filter(ativo=True)
        criados = 0
        existentes = 0

        for func in funcionarios:
            # Check if has apontamentos in the week
            has_ap = ApontamentoFuncionario.objects.filter(
                funcionario=func,
                data__gte=data_inicio,
                data__lte=data_fim
            ).exists()
            if not has_ap:
                continue

            existing = FechamentoSemanal.objects.filter(
                funcionario=func, data_inicio=data_inicio, data_fim=data_fim
            ).first()
            if existing:
                existing.calcular_totais()
                existentes += 1
            else:
                f = FechamentoSemanal(
                    funcionario=func,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    status='aberto'
                )
                f.save()
                f.calcular_totais()
                criados += 1

        messages.success(request, f'Fechamento automático concluído: {criados} criados, {existentes} atualizados.')
        return redirect('funcionarios:fechamento_list')

    # GET: show form to select week
    context = {
        'title': 'Fechamento Semanal Automático',
        'today': datetime.date.today(),
    }
    return render(request, 'funcionarios/fechamento_auto.html', context)


# ==================== VISÕES ESPECIAIS ====================

@login_required
def obra_mao_de_obra(request, pk):
    """Visão de mão de obra por obra: custos por etapa + timeline"""
    obra = get_object_or_404(Obra, pk=pk)
    etapas = Etapa.objects.filter(obra=obra)

    # Custos por etapa
    custo_por_etapa = []
    for etapa in etapas:
        aps = ApontamentoFuncionario.objects.filter(obra=obra, etapa=etapa)
        total = aps.aggregate(
            total_valor=Sum('valor_diaria'),
            total_horas=Sum('horas_trabalhadas'),
            total_dias=Count('id'),
        )
        funcionarios_etapa = aps.values(
            'funcionario__nome_completo', 'funcionario__funcao'
        ).annotate(
            dias=Count('id'),
            horas=Sum('horas_trabalhadas'),
            valor=Sum('valor_diaria'),
        ).order_by('-dias')

        custo_por_etapa.append({
            'etapa': etapa,
            'total_valor': total['total_valor'] or Decimal('0.00'),
            'total_horas': total['total_horas'] or Decimal('0.0'),
            'total_dias': total['total_dias'] or 0,
            'funcionarios': funcionarios_etapa,
        })

    # Custo total
    custo_total = ApontamentoFuncionario.objects.filter(obra=obra).aggregate(
        total=Sum('valor_diaria')
    )['total'] or Decimal('0.00')

    # Timeline: últimos 30 dias
    hoje = datetime.date.today()
    data_inicio = hoje - datetime.timedelta(days=30)
    timeline_qs = ApontamentoFuncionario.objects.filter(
        obra=obra, data__gte=data_inicio
    ).select_related('funcionario', 'etapa').order_by('data')

    timeline = defaultdict(list)
    for ap in timeline_qs:
        timeline[ap.data].append(ap)

    # Sort timeline
    timeline_sorted = sorted(timeline.items(), key=lambda x: x[0], reverse=True)

    context = {
        'obra': obra,
        'etapas': etapas,
        'custo_por_etapa': custo_por_etapa,
        'custo_total': custo_total,
        'timeline': timeline_sorted,
        'title': f'Mão de Obra - {obra.nome}'
    }
    return render(request, 'funcionarios/obra_mao_de_obra.html', context)


@login_required
def funcionario_historico(request, pk):
    """Histórico semanal/mensal de um funcionário"""
    funcionario = get_object_or_404(Funcionario, pk=pk)

    # Month selector
    mes_str = request.GET.get('mes')
    if mes_str:
        try:
            ano, mes = map(int, mes_str.split('-'))
        except ValueError:
            hoje = datetime.date.today()
            ano, mes = hoje.year, hoje.month
    else:
        hoje = datetime.date.today()
        ano, mes = hoje.year, hoje.month

    # Build calendar data
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    month_days = cal.monthdayscalendar(ano, mes)

    apontamentos_mes = ApontamentoFuncionario.objects.filter(
        funcionario=funcionario,
        data__year=ano,
        data__month=mes
    ).select_related('obra', 'etapa')

    # Map by day
    ap_by_day = {}
    for ap in apontamentos_mes:
        ap_by_day[ap.data.day] = ap

    # Build calendar with data
    calendar_weeks = []
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                ap = ap_by_day.get(day)
                week_data.append({
                    'day': day,
                    'date': datetime.date(ano, mes, day),
                    'apontamento': ap,
                })
        calendar_weeks.append(week_data)

    # Stats for the month
    stats = apontamentos_mes.aggregate(
        total_dias=Count('id'),
        total_horas=Sum('horas_trabalhadas'),
        total_valor=Sum('valor_diaria'),
        dias_ociosidade=Count('id', filter=Q(houve_ociosidade=True)),
        dias_retrabalho=Count('id', filter=Q(houve_retrabalho=True)),
    )

    # Obras trabalhadas no mês
    obras_mes = apontamentos_mes.values('obra__nome').annotate(
        dias=Count('id'),
        horas=Sum('horas_trabalhadas'),
    ).order_by('-dias')

    # Navigation
    prev_month = datetime.date(ano, mes, 1) - datetime.timedelta(days=1)
    next_month = datetime.date(ano, mes, 1) + datetime.timedelta(days=32)
    next_month = next_month.replace(day=1)

    context = {
        'funcionario': funcionario,
        'calendar_weeks': calendar_weeks,
        'stats': stats,
        'obras_mes': obras_mes,
        'ano': ano,
        'mes': mes,
        'mes_nome': calendar.month_name[mes] if hasattr(calendar.month_name, '__getitem__') else '',
        'prev_month': f"{prev_month.year}-{prev_month.month:02d}",
        'next_month': f"{next_month.year}-{next_month.month:02d}",
        'current_month': f"{ano}-{mes:02d}",
        'title': f'Histórico - {funcionario.nome_completo}'
    }
    return render(request, 'funcionarios/funcionario_historico.html', context)


# ==================== APIs ====================

@login_required
def apontamentos_api(request):
    """API JSON para retornar apontamentos de um funcionário em um intervalo de datas."""
    funcionario_id = request.GET.get('funcionario')
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')

    if not funcionario_id or not data_inicio:
        return JsonResponse({'error': 'Parâmetros insuficientes'}, status=400)

    try:
        di = datetime.date.fromisoformat(data_inicio)
    except Exception:
        return JsonResponse({'error': 'data_inicio inválida'}, status=400)

    if data_fim:
        try:
            df = datetime.date.fromisoformat(data_fim)
        except Exception:
            return JsonResponse({'error': 'data_fim inválida'}, status=400)
    else:
        df = di + datetime.timedelta(days=6)

    qs = ApontamentoFuncionario.objects.filter(
        funcionario_id=funcionario_id,
        data__gte=di,
        data__lte=df
    ).select_related('obra', 'etapa').order_by('data')

    apontamentos = []
    total_valor = Decimal('0.00')
    total_horas = Decimal('0.0')
    for a in qs:
        apontamentos.append({
            'id': a.id,
            'obra': a.obra.nome if a.obra else None,
            'etapa': str(a.etapa) if a.etapa else None,
            'data': a.data.isoformat(),
            'horas_trabalhadas': str(a.horas_trabalhadas),
            'clima': a.clima,
            'houve_ociosidade': a.houve_ociosidade,
            'houve_retrabalho': a.houve_retrabalho,
            'valor_diaria': str(a.valor_diaria),
            'created_at': a.created_at.isoformat(),
        })
        total_valor += a.valor_diaria
        total_horas += a.horas_trabalhadas

    result = {
        'apontamentos': apontamentos,
        'totais': {
            'dias': qs.count(),
            'horas': str(total_horas),
            'valor': f"{total_valor:.2f}"
        }
    }
    return JsonResponse(result)


@login_required
def etapas_por_obra_api(request):
    """API para retornar etapas de uma obra (para preencher select dinamicamente)"""
    obra_id = request.GET.get('obra_id')
    if not obra_id:
        return JsonResponse({'etapas': []})

    etapas = Etapa.objects.filter(obra_id=obra_id).order_by('numero_etapa')
    data = [{'id': e.id, 'label': e.get_numero_etapa_display()} for e in etapas]
    return JsonResponse({'etapas': data})
