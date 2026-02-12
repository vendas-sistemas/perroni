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
from apps.obras.models import (
    Obra, Etapa,
    Etapa1Fundacao, Etapa2Estrutura, Etapa3Instalacoes,
    Etapa4Acabamentos, Etapa5Finalizacao,
)
from django.db import IntegrityError
from django.db.models import Sum, Count, Q, Avg, F
import datetime
from decimal import Decimal, InvalidOperation
from collections import defaultdict
import calendar


# ==================== ETAPA ITEMS HELPERS ====================

# Metadata for fields in each etapa detail model
ETAPA_FIELDS_META = {
    1: {
        'related_name': 'fundacao',
        'model_class': Etapa1Fundacao,
        'fields': [
            ('limpeza_terreno', 'boolean', 'Limpeza do Terreno'),
            ('instalacao_energia_agua', 'boolean', 'Instalação de Energia e Água'),
            ('marcacao_escavacao_dias', 'integer', 'Marcação e Escavação (dias)'),
            ('locacao_ferragem_dias', 'integer', 'Locação de Ferragem (dias)'),
            ('alicerce_percentual', 'decimal', 'Alicerce, Reboco e Impermeabilização (%)'),
            ('aterro_contrapiso_dias', 'integer', 'Aterro e Contrapiso (dias)'),
            ('parede_7fiadas_blocos', 'integer', 'Parede 7 Fiadas (blocos)'),
            ('fiadas_respaldo_dias', 'integer', '8 Fiadas até Respaldo (dias)'),
        ]
    },
    2: {
        'related_name': 'estrutura',
        'model_class': Etapa2Estrutura,
        'fields': [
            ('montagem_laje_dias', 'integer', 'Montagem da Laje (dias)'),
            ('platibanda_blocos', 'integer', 'Platibanda (blocos)'),
            ('cobertura_dias', 'integer', 'Cobertura Completa (dias)'),
        ]
    },
    3: {
        'related_name': 'instalacoes',
        'model_class': Etapa3Instalacoes,
        'fields': [
            ('reboco_externo_m2', 'decimal', 'Reboco Externo (m²)'),
            ('reboco_interno_m2', 'decimal', 'Reboco Interno (m²)'),
            ('instalacao_portais', 'boolean', 'Instalação de Portais'),
            ('agua_fria', 'boolean', 'Água Fria'),
            ('esgoto', 'boolean', 'Esgoto'),
            ('fluvial', 'boolean', 'Fluvial'),
        ]
    },
    4: {
        'related_name': 'acabamentos',
        'model_class': Etapa4Acabamentos,
        'fields': [
            ('portas_janelas', 'boolean', 'Portas e Janelas'),
            ('pintura_externa_1demao_dias', 'integer', 'Pintura Externa 1ª Demão (dias)'),
            ('pintura_interna_1demao_dias', 'integer', 'Pintura Interna 1ª Demão (dias)'),
            ('assentamento_piso_dias', 'integer', 'Assentamento de Piso (dias)'),
        ]
    },
    5: {
        'related_name': 'finalizacao',
        'model_class': Etapa5Finalizacao,
        'fields': [
            ('pintura_externa_2demao_dias', 'integer', 'Pintura Externa 2ª Demão (dias)'),
            ('pintura_interna_2demao_dias', 'integer', 'Pintura Interna 2ª Demão (dias)'),
            ('loucas_metais', 'boolean', 'Louças e Metais'),
            ('eletrica', 'boolean', 'Elétrica'),
        ]
    },
}


def _get_etapa_detail_obj(etapa, create=True):
    """Get (or optionally create) the detail model instance for an etapa."""
    meta = ETAPA_FIELDS_META.get(etapa.numero_etapa)
    if not meta:
        return None
    model_class = meta['model_class']
    related = meta['related_name']
    try:
        return getattr(etapa, related)
    except model_class.DoesNotExist:
        if create:
            return model_class.objects.create(etapa=etapa)
        return None


def _get_etapa_items(etapa):
    """Return a list of dicts with field metadata + current values for an etapa."""
    meta = ETAPA_FIELDS_META.get(etapa.numero_etapa)
    if not meta:
        return []
    detail_obj = _get_etapa_detail_obj(etapa, create=False)
    items = []
    for field_name, field_type, label in meta['fields']:
        current_value = None
        if detail_obj:
            current_value = getattr(detail_obj, field_name, None)
        if current_value is None:
            current_value = False if field_type == 'boolean' else 0
        items.append({
            'name': field_name,
            'type': field_type,
            'label': label,
            'value': str(current_value) if isinstance(current_value, Decimal) else current_value,
        })
    return items


def _update_etapa_items_from_post(etapa, post_data):
    """Update etapa detail model fields from POST data (ADDITIVE logic) and recalculate obra progress.

    - boolean fields: OR logic (once marked True, stays True)
    - integer/decimal fields: posted value is ADDED to the current value
    """
    meta = ETAPA_FIELDS_META.get(etapa.numero_etapa)
    if not meta:
        return
    detail_obj = _get_etapa_detail_obj(etapa, create=True)
    if not detail_obj:
        return

    changed = False
    for field_name, field_type, _ in meta['fields']:
        key = f'item_{field_name}'
        if field_type == 'boolean':
            # Hidden "0" + checkbox "1" pattern — OR logic
            val = post_data.get(key, '0')
            new_val = val in ('1', 'on', 'true', 'True')
            current_val = getattr(detail_obj, field_name, False)
            final_val = current_val or new_val  # once True, stays True
            if current_val != final_val:
                setattr(detail_obj, field_name, final_val)
                changed = True
        elif field_type == 'integer':
            raw = post_data.get(key, '')
            if raw != '':
                try:
                    increment = int(raw)
                    if increment != 0:
                        current_val = getattr(detail_obj, field_name, 0) or 0
                        setattr(detail_obj, field_name, current_val + increment)
                        changed = True
                except (ValueError, TypeError):
                    pass
        elif field_type == 'decimal':
            raw = post_data.get(key, '')
            if raw != '':
                try:
                    increment = Decimal(raw)
                    if increment != Decimal('0'):
                        current_val = getattr(detail_obj, field_name, Decimal('0')) or Decimal('0')
                        setattr(detail_obj, field_name, current_val + increment)
                        changed = True
                except (ValueError, TypeError, InvalidOperation):
                    pass

    if changed:
        detail_obj.save()
        # Recalculate obra overall progress
        etapa.obra.calcular_percentual()


@login_required
def funcionario_list(request):
    """Lista funcionários"""
    funcionarios = Funcionario.objects.filter(ativo=True).order_by('nome_completo')

    # Filtro por função
    funcao_filter = request.GET.get('funcao', '')
    if funcao_filter in ('pedreiro', 'servente'):
        funcionarios = funcionarios.filter(funcao=funcao_filter)

    # Busca por nome
    busca = request.GET.get('q', '').strip()
    if busca:
        funcionarios = funcionarios.filter(nome_completo__icontains=busca)

    # Contadores
    total_ativos = Funcionario.objects.filter(ativo=True).count()
    total_pedreiros = Funcionario.objects.filter(ativo=True, funcao='pedreiro').count()
    total_serventes = Funcionario.objects.filter(ativo=True, funcao='servente').count()
    total_resultado = funcionarios.count()

    # Paginação
    per_page = request.GET.get('per_page', '15')
    if per_page not in ('10', '15', '20'):
        per_page = '15'
    per_page = int(per_page)
    paginator = Paginator(funcionarios, per_page)
    page = request.GET.get('page')
    try:
        funcionarios_page = paginator.page(page)
    except PageNotAnInteger:
        funcionarios_page = paginator.page(1)
    except EmptyPage:
        funcionarios_page = paginator.page(paginator.num_pages)

    context = {
        'funcionarios': funcionarios_page,
        'page_obj': funcionarios_page,
        'title': 'Funcionários',
        'busca': busca,
        'funcao_filter': funcao_filter,
        'total_ativos': total_ativos,
        'total_pedreiros': total_pedreiros,
        'total_serventes': total_serventes,
        'total_resultado': total_resultado,
        'per_page': per_page,
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

    # Totals for current filter (one diária per unique funcionario+date)
    totais = qs.aggregate(
        total_horas=Sum('horas_trabalhadas'),
        total_valor=Sum('valor_diaria'),
        total_registros=Count('id'),
        total_diarias=Count('data', distinct=True),
        total_ociosidade=Count('data', filter=Q(houve_ociosidade=True), distinct=True),
        total_retrabalho=Count('data', filter=Q(houve_retrabalho=True), distinct=True),
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
            # Update existing entry instead of creating duplicate for same (funcionario, data, obra)
            existing = ApontamentoFuncionario.objects.filter(
                funcionario=ap.funcionario, data=ap.data, obra=ap.obra
            ).first()
            if existing:
                existing.etapa = ap.etapa
                existing.horas_trabalhadas = ap.horas_trabalhadas
                existing.clima = ap.clima
                existing.metragem_executada = ap.metragem_executada
                existing.valor_diaria = ap.valor_diaria
                existing.houve_ociosidade = ap.houve_ociosidade
                existing.observacao_ociosidade = ap.observacao_ociosidade
                existing.houve_retrabalho = ap.houve_retrabalho
                existing.motivo_retrabalho = ap.motivo_retrabalho
                existing.observacoes = ap.observacoes
                existing.save()
                ap = existing
                messages.info(request, f'Apontamento de {ap.funcionario.nome_completo} atualizado (já existia registro nesta data/obra).')
            else:
                ap.save()

            # ---- Auto-update obra: save etapa items from POST ----
            if ap.etapa and request.POST.get('items_etapa_id'):
                _update_etapa_items_from_post(ap.etapa, request.POST)
                messages.info(request, f'📊 Progresso da etapa "{ap.etapa}" atualizado automaticamente.')

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
    2. Sistema exibe etapas da obra com seus itens (progresso atual)
    3. Fiscal adiciona funcionários com etapa, horas, itens trabalhados
    4. Sistema atualiza automaticamente a obra com os dados informados
    """
    cab_form = ApontamentoDiarioCabecalhoForm(request.GET or None)
    obra = None
    data = None
    clima = None
    apontamentos_existentes = []
    item_form = None
    etapas = []
    etapas_overview = []

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

        # Build overview of all etapas with their items + current values
        for etapa in etapas:
            items = _get_etapa_items(etapa)
            etapas_overview.append({
                'etapa': etapa,
                'items': items,
            })

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
                    # Update existing entry instead of creating duplicate for same (funcionario, data, obra)
                    existing = ApontamentoFuncionario.objects.filter(
                        funcionario=ap.funcionario, data=data, obra=obra
                    ).first()
                    if existing:
                        existing.etapa = ap.etapa
                        existing.horas_trabalhadas = ap.horas_trabalhadas
                        existing.clima = ap.clima
                        existing.valor_diaria = ap.valor_diaria
                        existing.houve_ociosidade = ap.houve_ociosidade
                        existing.observacao_ociosidade = ap.observacao_ociosidade
                        existing.houve_retrabalho = ap.houve_retrabalho
                        existing.motivo_retrabalho = ap.motivo_retrabalho
                        existing.observacoes = ap.observacoes
                        existing.save()
                        ap = existing
                        messages.info(request, f'Apontamento de {ap.funcionario.nome_completo} atualizado (já existia registro nesta data/obra).')
                    else:
                        ap.save()

                    # ---- Auto-update obra: save etapa items from POST ----
                    items_etapa_id = request.POST.get('items_etapa_id')
                    if items_etapa_id and ap.etapa:
                        _update_etapa_items_from_post(ap.etapa, request.POST)
                        messages.info(request, f'📊 Progresso da etapa "{ap.etapa}" atualizado automaticamente.')

                    if ap.houve_retrabalho:
                        messages.warning(request, f'⚠️ RETRABALHO: {ap.funcionario.nome_completo} - {ap.motivo_retrabalho}')
                    if ap.houve_ociosidade:
                        messages.warning(request, f'⚠️ OCIOSIDADE: {ap.funcionario.nome_completo} - {ap.observacao_ociosidade}')
                    messages.success(request, f'{ap.funcionario.nome_completo} apontado com sucesso.')
                    return redirect(f'{request.path}?obra={obra.pk}&data={data.isoformat()}&clima={clima}')
                except IntegrityError:
                    messages.error(request, 'Funcionário já apontado nesta data em outra obra. Remova ou edite o apontamento existente se necessário.')
            else:
                messages.error(request, 'Corrija os erros abaixo.')
        elif request.method == 'POST' and request.POST.get('save_etapa_items'):
            # Save etapa items from the overview edit form (no funcionario add)
            items_etapa_id = request.POST.get('items_etapa_id')
            try:
                etapa_obj = Etapa.objects.get(pk=items_etapa_id, obra=obra)
                _update_etapa_items_from_post(etapa_obj, request.POST)
                messages.success(request, f'Progresso da etapa "{etapa_obj.get_numero_etapa_display()}" atualizado.')
            except Etapa.DoesNotExist:
                messages.error(request, 'Etapa inválida.')
            return redirect(f'{request.path}?obra={obra.pk}&data={data.isoformat()}&clima={clima}')
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
        'etapas_overview': etapas_overview,
        'apontamentos_existentes': apontamentos_existentes,
        'item_form': item_form,
        'title': 'Registro Diário'
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
    """Lista fechamentos agrupados por semana"""
    from django.db.models import Sum, Count, Q, Min, Max

    # Agrupar por semana (data_inicio, data_fim)
    semanas_qs = (
        FechamentoSemanal.objects
        .values('data_inicio', 'data_fim')
        .annotate(
            total_funcionarios=Count('id'),
            total_dias=Sum('total_dias'),
            total_valor=Sum('total_valor'),
            total_ociosidade=Sum('dias_ociosidade'),
            total_retrabalho=Sum('dias_retrabalho'),
            qtd_fechados=Count('id', filter=Q(status='fechado')),
            qtd_pagos=Count('id', filter=Q(status='pago')),
        )
        .order_by('-data_inicio')
    )

    semanas = list(semanas_qs)

    # Calcular status geral de cada semana
    for s in semanas:
        if s['qtd_pagos'] == s['total_funcionarios']:
            s['status_geral'] = 'pago'
        elif s['qtd_pagos'] > 0:
            s['status_geral'] = 'parcial'
        else:
            s['status_geral'] = 'fechado'

    context = {
        'semanas': semanas,
        'title': 'Fechamentos Semanais',
    }
    return render(request, 'funcionarios/fechamento_list.html', context)


@login_required
def set_theme(request):
    """Endpoint to persist user's theme preference (light/dark)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)
    theme = request.POST.get('theme')
    variant = request.POST.get('variant')
    if theme not in ('light', 'dark'):
        return JsonResponse({'status': 'error', 'message': 'Invalid theme'}, status=400)
    profile = getattr(request.user, 'profile', None)
    if not profile:
        from .models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.theme_preference = theme
    if variant in dict(getattr(profile, 'THEME_VARIANT_CHOICES', [])) or variant in ('default','soft','gray','blue'):
        profile.theme_variant = variant
    profile.save()
    return JsonResponse({'status': 'ok', 'theme': theme})


@login_required
def fechamento_semana_detail(request, data_inicio):
    """Detalhe de uma semana: lista todos os funcionários e seus fechamentos."""
    try:
        dt_inicio = datetime.date.fromisoformat(data_inicio)
    except ValueError:
        messages.error(request, 'Data inválida.')
        return redirect('funcionarios:fechamento_list')

    dt_fim = dt_inicio + datetime.timedelta(days=5)  # seg a sáb

    fechamentos = (
        FechamentoSemanal.objects
        .filter(data_inicio=dt_inicio)
        .select_related('funcionario')
        .order_by('funcionario__nome_completo')
    )

    if not fechamentos.exists():
        messages.warning(request, 'Nenhum fechamento encontrado para esta semana.')
        return redirect('funcionarios:fechamento_list')

    dt_fim_real = fechamentos.first().data_fim

    # Totais da semana
    from django.db.models import Sum, Count, Q
    totais = fechamentos.aggregate(
        total_funcionarios=Count('id'),
        total_dias=Sum('total_dias'),
        total_valor=Sum('total_valor'),
        total_ociosidade=Sum('dias_ociosidade'),
        total_retrabalho=Sum('dias_retrabalho'),
        qtd_fechados=Count('id', filter=Q(status='fechado')),
        qtd_pagos=Count('id', filter=Q(status='pago')),
    )

    # Filtro por status
    status_filter = request.GET.get('status')
    if status_filter in ('fechado', 'pago'):
        fechamentos = fechamentos.filter(status=status_filter)

    # Busca por nome
    busca = request.GET.get('q', '').strip()
    if busca:
        fechamentos = fechamentos.filter(funcionario__nome_completo__icontains=busca)

    # Filtro por dia específico ou intervalo de datas (filtra via apontamentos)
    dia_filter = request.GET.get('dia', '').strip()
    dia_inicio_filter = request.GET.get('dia_inicio', '').strip()
    dia_fim_filter = request.GET.get('dia_fim', '').strip()

    if dia_filter:
        # Dia específico: só mostra funcionários que trabalharam nesse dia
        try:
            dt_dia = datetime.date.fromisoformat(dia_filter)
            func_ids = ApontamentoFuncionario.objects.filter(
                data=dt_dia,
                data__gte=dt_inicio,
                data__lte=dt_fim_real,
            ).values_list('funcionario_id', flat=True)
            fechamentos = fechamentos.filter(funcionario_id__in=func_ids)
        except ValueError:
            pass
    elif dia_inicio_filter or dia_fim_filter:
        # Intervalo de datas dentro da semana
        try:
            dt_di = datetime.date.fromisoformat(dia_inicio_filter) if dia_inicio_filter else dt_inicio
            dt_df = datetime.date.fromisoformat(dia_fim_filter) if dia_fim_filter else dt_fim_real
            # Limitar ao intervalo da semana
            dt_di = max(dt_di, dt_inicio)
            dt_df = min(dt_df, dt_fim_real)
            func_ids = ApontamentoFuncionario.objects.filter(
                data__gte=dt_di,
                data__lte=dt_df,
            ).values_list('funcionario_id', flat=True)
            fechamentos = fechamentos.filter(funcionario_id__in=func_ids)
        except ValueError:
            pass

    # Gerar lista de dias da semana para os filtros rápidos
    dias_semana = []
    DIAS_NOMES = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    d = dt_inicio
    while d <= dt_fim_real:
        dias_semana.append({
            'data': d,
            'nome': DIAS_NOMES[d.weekday()],
            'iso': d.isoformat(),
        })
        d += datetime.timedelta(days=1)

    # Buscar apontamentos da semana para mostrar dia/obra por funcionário
    apontamentos_semana = (
        ApontamentoFuncionario.objects
        .filter(data__gte=dt_inicio, data__lte=dt_fim_real)
        .select_related('obra')
        .order_by('data')
    )
    # Agrupar por funcionário: lista de {data, obra_nome}
    apts_por_func = defaultdict(list)
    for apt in apontamentos_semana:
        apts_por_func[apt.funcionario_id].append({
            'data': apt.data,
            'obra': apt.obra.nome if apt.obra else '—',
        })

    # Converter fechamentos para lista para poder anotar
    fechamentos_list = list(fechamentos)
    for f in fechamentos_list:
        f.apontamentos_semana = apts_por_func.get(f.funcionario_id, [])

    context = {
        'fechamentos': fechamentos_list,
        'data_inicio': dt_inicio,
        'data_fim': dt_fim_real,
        'totais': totais,
        'status_filter': status_filter or '',
        'busca': busca,
        'dia_filter': dia_filter,
        'dia_inicio_filter': dia_inicio_filter,
        'dia_fim_filter': dia_fim_filter,
        'dias_semana': dias_semana,
        'title': f'Semana {dt_inicio.strftime("%d/%m/%Y")} a {dt_fim_real.strftime("%d/%m/%Y")}',
    }
    return render(request, 'funcionarios/fechamento_semana_detail.html', context)


@login_required
def fechamento_create(request):
    """Cria um fechamento semanal e calcula os totais"""
    if request.method == 'POST':
        form = FechamentoForm(request.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.data_fim = f.data_inicio + datetime.timedelta(days=5)
            f.status = 'fechado'
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

        # Verifica se já existe fechamento para esta semana
        fechamentos_existentes = FechamentoSemanal.objects.filter(data_inicio=data_inicio)
        if fechamentos_existentes.exists():
            qtd = fechamentos_existentes.count()
            messages.warning(
                request,
                f'Já existe(m) {qtd} fechamento(s) para a semana de '
                f'{data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}. '
                f'Não é possível gerar novos fechamentos para esta semana.'
            )
            return redirect('funcionarios:fechamento_list')

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
                    status='fechado'
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
            total_dias=Count('data', distinct=True),
        )
        funcionarios_etapa = aps.values(
            'funcionario__nome_completo', 'funcionario__funcao'
        ).annotate(
            dias=Count('data', distinct=True),
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

    # Stats for the month (one diária per unique date)
    stats = apontamentos_mes.aggregate(
        total_dias=Count('data', distinct=True),
        total_horas=Sum('horas_trabalhadas'),
        total_valor=Sum('valor_diaria'),
        dias_ociosidade=Count('data', filter=Q(houve_ociosidade=True), distinct=True),
        dias_retrabalho=Count('data', filter=Q(houve_retrabalho=True), distinct=True),
    )

    # Obras trabalhadas no mês
    obras_mes = apontamentos_mes.values('obra__nome').annotate(
        dias=Count('data', distinct=True),
        horas=Sum('horas_trabalhadas'),
    ).order_by('-dias')

    # Navigation
    prev_month = datetime.date(ano, mes, 1) - datetime.timedelta(days=1)
    next_month = datetime.date(ano, mes, 1) + datetime.timedelta(days=32)
    next_month = next_month.replace(day=1)

    MESES_PT = [
        '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
    ]

    context = {
        'funcionario': funcionario,
        'calendar_weeks': calendar_weeks,
        'stats': stats,
        'obras_mes': obras_mes,
        'ano': ano,
        'mes': mes,
        'mes_nome': MESES_PT[mes],
        'prev_month': f"{prev_month.year}-{prev_month.month:02d}",
        'next_month': f"{next_month.year}-{next_month.month:02d}",
        'current_month': f"{ano}-{mes:02d}",
        'title': f'Histórico - {funcionario.nome_completo}'
    }
    return render(request, 'funcionarios/funcionario_historico.html', context)


# ==================== APIs ====================

@login_required
def check_fechamento_api(request):
    """API JSON para verificar se já existe fechamento para uma semana."""
    data_inicio_str = request.GET.get('data_inicio', '')
    funcionario_id = request.GET.get('funcionario', '')

    if not data_inicio_str:
        return JsonResponse({'error': 'Parâmetro data_inicio obrigatório'}, status=400)

    try:
        di = datetime.date.fromisoformat(data_inicio_str)
    except ValueError:
        return JsonResponse({'error': 'data_inicio inválida'}, status=400)

    qs = FechamentoSemanal.objects.filter(data_inicio=di)
    if funcionario_id:
        qs_func = qs.filter(funcionario_id=funcionario_id)
        exists_func = qs_func.exists()
    else:
        exists_func = False

    exists_any = qs.exists()
    count = qs.count()

    funcionarios_list = list(
        qs.select_related('funcionario')
        .values_list('funcionario__nome_completo', flat=True)
        .order_by('funcionario__nome_completo')[:10]
    )

    di_fim = di + datetime.timedelta(days=6)
    return JsonResponse({
        'exists': exists_any,
        'exists_funcionario': exists_func,
        'count': count,
        'funcionarios': funcionarios_list,
        'semana': f'{di.strftime("%d/%m/%Y")} a {di_fim.strftime("%d/%m/%Y")}',
    })


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
    seen_dates = set()
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
        # Only count valor/horas once per unique date (one diária per day)
        if a.data not in seen_dates:
            total_valor += a.valor_diaria
            total_horas += a.horas_trabalhadas
            seen_dates.add(a.data)

    result = {
        'apontamentos': apontamentos,
        'totais': {
            'dias': len(seen_dates),
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


@login_required
def itens_etapa_api(request):
    """API para retornar os itens/campos de uma etapa específica com valores atuais."""
    etapa_id = request.GET.get('etapa_id')
    if not etapa_id:
        return JsonResponse({'items': []})
    try:
        etapa = Etapa.objects.get(pk=etapa_id)
    except Etapa.DoesNotExist:
        return JsonResponse({'items': []})

    items = _get_etapa_items(etapa)
    return JsonResponse({
        'items': items,
        'etapa_id': etapa.id,
        'etapa_numero': etapa.numero_etapa,
        'etapa_label': etapa.get_numero_etapa_display(),
    })


@login_required
def itens_obra_api(request):
    """API para retornar TODAS as etapas com seus itens para uma obra."""
    obra_id = request.GET.get('obra_id')
    if not obra_id:
        return JsonResponse({'etapas': []})

    etapas = Etapa.objects.filter(obra_id=obra_id).order_by('numero_etapa')
    result = []
    for etapa in etapas:
        items = _get_etapa_items(etapa)
        result.append({
            'id': etapa.id,
            'numero': etapa.numero_etapa,
            'label': etapa.get_numero_etapa_display(),
            'concluida': etapa.concluida,
            'items': items,
        })
    return JsonResponse({'etapas': result})
