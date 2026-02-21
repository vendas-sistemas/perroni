from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
import datetime
from django.contrib.auth.models import User
from .models import Obra, Etapa
from apps.funcionarios.models import ApontamentoFuncionario, FotoApontamento
from django.http import HttpResponse
import csv
from decimal import Decimal
from .forms import ObraForm
from .models import distribuir_datas_etapas
from .forms import (
    EtapaForm, Etapa1FundacaoForm, Etapa2EstruturaForm,
    Etapa3InstalacoesForm, Etapa4AcabamentosForm, Etapa5FinalizacaoForm
)
from .models import (
    Etapa1Fundacao, Etapa2Estrutura, Etapa3Instalacoes,
    Etapa4Acabamentos, Etapa5Finalizacao, EtapaHistorico
)
from django.shortcuts import Http404
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from apps.clientes.models import Cliente
import re


def _format_historico_valor(valor):
    if valor is None or valor == '':
        return '—'
    if isinstance(valor, bool):
        return 'Sim' if valor else 'Não'
    if isinstance(valor, datetime.date):
        return valor.strftime('%d/%m/%Y')
    return str(valor)


def _registrar_historico_etapa(etapa, usuario, origem, form):
    if not getattr(form, 'changed_data', None):
        return

    linhas = []
    for campo in form.changed_data:
        field_obj = form.fields.get(campo)
        label = field_obj.label if field_obj and field_obj.label else campo.replace('_', ' ').capitalize()
        valor_anterior = _format_historico_valor(form.initial.get(campo))
        valor_novo = _format_historico_valor(form.cleaned_data.get(campo))
        linhas.append(f"{label}: {valor_anterior} → {valor_novo}")

    if linhas:
        EtapaHistorico.objects.create(
            etapa=etapa,
            usuario=usuario if usuario and usuario.is_authenticated else None,
            origem=origem,
            descricao='\n'.join(linhas)
        )


def _resolver_usuario_historico(request, form=None):
    """Resolve o usuário para o histórico, priorizando usuário explicitamente informado no fluxo."""
    if form and getattr(form, 'cleaned_data', None):
        for chave in ('usuario', 'responsavel', 'fiscal', 'executor'):
            valor = form.cleaned_data.get(chave)
            if isinstance(valor, User):
                return valor

    if request.user and request.user.is_authenticated:
        return request.user

    return None


def _registrar_historico_inicial_etapa(etapa, usuario, origem='Criação da etapa'):
    EtapaHistorico.objects.create(
        etapa=etapa,
        usuario=usuario if usuario and usuario.is_authenticated else None,
        origem=origem,
        descricao=(
            f"Etapa criada com status inicial: {etapa.get_status_display()}\n"
            f"Percentual: {etapa.percentual_valor}%"
        )
    )


@login_required
def obra_list(request):
    """Lista todas as obras"""
    qs = Obra.objects.filter(ativo=True)

    # filters
    q = request.GET.get('q')
    cliente = request.GET.get('cliente')
    cpf = request.GET.get('cpf')
    status_filter = request.GET.get('status', '')
    data_inicio_de = request.GET.get('data_inicio_de')
    data_inicio_ate = request.GET.get('data_inicio_ate')
    data_termino_de = request.GET.get('data_termino_de')
    data_termino_ate = request.GET.get('data_termino_ate')
    if q:
        qs = qs.filter(nome__icontains=q)
    if cliente:
        qs = qs.filter(cliente__nome__icontains=cliente)
    if cpf:
        digits = re.sub(r"\D", "", cpf or "")
        q_filters = Q()
        if digits:
            q_filters |= Q(cliente__cpf__icontains=digits)
            if len(digits) == 11:
                formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
                q_filters |= Q(cliente__cpf__icontains=formatted)
        q_filters |= Q(cliente__nome__icontains=cpf)
        qs = qs.filter(q_filters)
    if status_filter and status_filter in dict(Obra.STATUS_CHOICES):
        qs = qs.filter(status=status_filter)
    if data_inicio_de:
        qs = qs.filter(data_inicio__gte=data_inicio_de)
    if data_inicio_ate:
        qs = qs.filter(data_inicio__lte=data_inicio_ate)
    if data_termino_de:
        qs = qs.filter(data_previsao_termino__gte=data_termino_de)
    if data_termino_ate:
        qs = qs.filter(data_previsao_termino__lte=data_termino_ate)

    # Order by start date (newest first). Fall back to creation time for ties.
    qs = qs.order_by('-data_inicio', '-created_at')

    # Contadores (antes da paginação)
    all_active = Obra.objects.filter(ativo=True)
    total_obras = all_active.count()
    total_em_andamento = all_active.filter(status='em_andamento').count()
    total_planejamento = all_active.filter(status='planejamento').count()
    total_concluida = all_active.filter(status='concluida').count()
    total_pausada = all_active.filter(status='pausada').count()
    total_resultado = qs.count()

    # pagination
    per_page_param = request.GET.get('per_page', '15')
    if per_page_param not in ('10', '15', '20'):
        per_page_param = '15'
    per_page = int(per_page_param)
    paginator = Paginator(qs, per_page)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    # annotate obras with cliente info
    for obra in page_obj.object_list:
        if hasattr(obra, 'cliente') and obra.cliente is not None:
            obra.cliente_nome = getattr(obra.cliente, 'nome', str(obra.cliente))
            obra.cliente_cpf = getattr(obra.cliente, 'cpf', '') or ''
        else:
            obra.cliente_nome = ''
            obra.cliente_cpf = ''

    params = request.GET.copy()
    if 'page' in params:
        params.pop('page')
    querystring = params.urlencode()

    context = {
        'obras': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'querystring': querystring,
        'per_page': per_page,
        'title': 'Obras',
        'total_obras': total_obras,
        'total_em_andamento': total_em_andamento,
        'total_planejamento': total_planejamento,
        'total_concluida': total_concluida,
        'total_pausada': total_pausada,
        'total_resultado': total_resultado,
        'status_filter': status_filter,
        'filters': {
            'q': q or '',
            'cliente': cliente or '',
            'cpf': cpf or '',
            'status': status_filter or '',
            'data_inicio_de': data_inicio_de or '',
            'data_inicio_ate': data_inicio_ate or '',
            'data_termino_de': data_termino_de or '',
            'data_termino_ate': data_termino_ate or '',
        }
    }
    return render(request, 'obras/obra_list.html', context)



@login_required
def obra_detail(request, pk):
    """Detalhes de uma obra"""
    obra = get_object_or_404(Obra, pk=pk)

    # Optional: show apontamentos for a specific date when ?data=YYYY-MM-DD is provided
    data_str = request.GET.get('data')
    apontamentos_do_dia = None
    if data_str:
        try:
            data = datetime.date.fromisoformat(data_str)
            apontamentos_do_dia = ApontamentoFuncionario.objects.filter(
                obra=obra,
                data=data
            ).select_related('funcionario', 'etapa').order_by('funcionario__nome_completo')
        except ValueError:
            apontamentos_do_dia = None

    context = {
        'obra': obra,
        'title': f'Obra: {obra.nome}',
        'apontamentos_do_dia': apontamentos_do_dia,
        'apontamento_data': data_str or ''
    }
    return render(request, 'obras/obra_detail.html', context)


@login_required
def obra_create(request):
    """Cria uma nova obra e gera 5 etapas iniciais"""
    if request.method == 'POST':
        form = ObraForm(request.POST)
        if form.is_valid():
            obra = form.save()
            usuario_hist = _resolver_usuario_historico(request, form)
            # Criar 5 etapas básicas se não existirem
            try:
                for num, _label in Etapa.ETAPA_CHOICES:
                    # Verifica se etapa já existe
                    if not Etapa.objects.filter(obra=obra, numero_etapa=num).exists():
                        etapa = Etapa.objects.create(
                            obra=obra,
                            numero_etapa=num,
                            percentual_valor=Etapa.PERCENTUAIS_ETAPA.get(num)
                        )
                        _registrar_historico_inicial_etapa(
                            etapa,
                            usuario_hist,
                            origem='Criação automática da etapa'
                        )
                messages.success(request, 'Obra criada com sucesso. Etapas carregadas automaticamente.')
            except Exception as e:
                messages.warning(request, f'Obra criada, mas houve erro ao criar etapas: {str(e)}')
            return redirect('obras:obra_detail', pk=obra.pk)
        else:
            messages.error(request, 'Corrija os erros no formulário.')
    else:
        form = ObraForm()
    return render(request, 'obras/obra_form.html', {'form': form, 'title': 'Nova Obra'})


@login_required
def obra_update(request, pk):
    """Atualiza uma obra"""
    obra = get_object_or_404(Obra, pk=pk)
    if request.method == 'POST':
        form = ObraForm(request.POST, instance=obra)
        if form.is_valid():
            # Verifica se as datas foram alteradas
            datas_alteradas = (
                form.cleaned_data.get('data_inicio') != obra.data_inicio or
                form.cleaned_data.get('data_previsao_termino') != obra.data_previsao_termino
            )
            
            form.save()
            
            # Se as datas foram alteradas, redistribui para as etapas
            if datas_alteradas:
                try:
                    distribuir_datas_etapas(obra)
                    messages.success(request, 'Obra atualizada com sucesso. Datas das etapas recalculadas.')
                except Exception as e:
                    messages.warning(request, f'Obra atualizada, mas houve erro ao recalcular datas: {str(e)}')
            else:
                messages.success(request, 'Obra atualizada com sucesso.')
            return redirect('obras:obra_detail', pk=obra.pk)
        else:
            messages.error(request, 'Corrija os erros no formulário.')
    else:
        form = ObraForm(instance=obra)
    return render(request, 'obras/obra_form.html', {'form': form, 'obra': obra, 'title': 'Editar Obra'})


@login_required
@require_POST
def obra_delete(request, pk):
    """Soft-delete: move obra para excluídos (marca `deleted_at` e desativa `ativo`)."""
    obra = get_object_or_404(Obra, pk=pk)
    # soft-delete timestamp
    obra.delete()
    # manter compatibilidade com flag `ativo` usada nas views
    obra.ativo = False
    obra.save(update_fields=['ativo'])
    messages.success(request, 'Obra movida para Excluídos.')
    return redirect(request.META.get('HTTP_REFERER', 'obras:obra_list'))


@login_required
def obras_trash(request):
    """Lista itens excluídos (objetos deletados)."""
    trashed = Obra.all_objects.dead().order_by('-deleted_at')
    context = {'object_list': trashed, 'title': 'Excluídos - Obras'}
    return render(request, 'obras/obra_trash_list.html', context)


@login_required
@require_POST
def obra_restore(request, pk):
    obra = get_object_or_404(Obra.all_objects, pk=pk)
    obra.restore()
    obra.ativo = True
    obra.save(update_fields=['ativo'])
    messages.success(request, 'Obra restaurada.')
    return redirect(request.META.get('HTTP_REFERER', 'obras:excluidos'))


@login_required
@require_POST
def obra_hard_delete(request, pk):
    obra = get_object_or_404(Obra.all_objects, pk=pk)
    obra.hard_delete()
    messages.success(request, 'Obra excluída permanentemente.')
    return redirect(request.META.get('HTTP_REFERER', 'obras:excluidos'))


@login_required
def obra_etapas(request, pk):
    """Gerencia etapas de uma obra"""
    obra = get_object_or_404(Obra, pk=pk)
    etapas = obra.etapas.all()
    context = {
        'obra': obra,
        'etapas': etapas,
        'title': f'Etapas - {obra.nome}'
    }
    return render(request, 'obras/obra_etapas.html', context)


@login_required
def obra_fotos(request, pk):
    """
    Galeria de fotos de uma obra, organizadas por etapa e dia.
    """
    from collections import defaultdict

    ETAPA_NOMES = {
        1: 'Etapa 1 — Fundação',
        2: 'Etapa 2 — Estrutura',
        3: 'Etapa 3 — Revestimentos e Instalações',
        4: 'Etapa 4 — Acabamentos',
        5: 'Etapa 5 — Finalização',
    }

    obra = get_object_or_404(Obra, pk=pk)

    fotos_qs = (
        FotoApontamento.objects
        .filter(obra=obra)
        .select_related('etapa', 'apontamento_lote', 'apontamento_individual')
        .order_by('etapa__numero_etapa', 'data_foto', '-data_upload')
    )

    # Agrupar: etapa_num → data_str → [fotos]
    por_etapa = defaultdict(lambda: defaultdict(list))
    sem_etapa = defaultdict(list)

    for foto in fotos_qs:
        data_str = foto.data_foto.strftime('%d/%m/%Y') if foto.data_foto else 'Sem data'
        if foto.etapa_id:
            num = foto.etapa.numero_etapa
            por_etapa[num][data_str].append(foto)
        else:
            sem_etapa[data_str].append(foto)

    # Montar lista ordenada para o template
    etapas_grupos = []
    for num in sorted(por_etapa.keys()):
        dias = [
            {'data': data, 'fotos': por_etapa[num][data]}
            for data in sorted(por_etapa[num].keys(), reverse=True)
        ]
        total = sum(len(d['fotos']) for d in dias)
        etapas_grupos.append({
            'numero': num,
            'nome': ETAPA_NOMES.get(num, f'Etapa {num}'),
            'dias': dias,
            'total': total,
        })

    sem_etapa_dias = [
        {'data': data, 'fotos': sem_etapa[data]}
        for data in sorted(sem_etapa.keys(), reverse=True)
    ]
    sem_etapa_total = sum(len(d['fotos']) for d in sem_etapa_dias)

    context = {
        'obra': obra,
        'etapas_grupos': etapas_grupos,
        'sem_etapa_dias': sem_etapa_dias,
        'sem_etapa_total': sem_etapa_total,
        'total_fotos': fotos_qs.count(),
        'title': f'Fotos da Obra — {obra.nome}',
    }
    return render(request, 'obras/obra_fotos.html', context)


@login_required
# Note: initialization of etapa detail records is now handled lazily
# when the user opens the corresponding etapa detail view. The
# explicit `obra_inicializar_detalhes` action/button was removed to
# simplify the workflow.


@login_required
def etapa_detail(request, pk):
    etapa = get_object_or_404(Etapa, pk=pk)
    detalhe = None
    try:
        if etapa.numero_etapa == 1:
            detalhe = etapa.fundacao
        elif etapa.numero_etapa == 2:
            detalhe = etapa.estrutura
        elif etapa.numero_etapa == 3:
            detalhe = etapa.instalacoes
        elif etapa.numero_etapa == 4:
            detalhe = etapa.acabamentos
        elif etapa.numero_etapa == 5:
            detalhe = etapa.finalizacao
    except Exception:
        detalhe = None

    context = {
        'etapa': etapa,
        'detalhe': detalhe,
        'historicos': etapa.historicos.select_related('usuario').all()[:100],
        'title': f'Etapa {etapa.numero_etapa} - {etapa.obra.nome}'
    }
    return render(request, 'obras/etapa_detail.html', context)


@login_required
def etapa_edit(request, pk):
    etapa = get_object_or_404(Etapa, pk=pk)
    if request.method == 'POST':
        form = EtapaForm(request.POST, instance=etapa)
        if form.is_valid():
            form.save()
            usuario_hist = _resolver_usuario_historico(request, form)
            _registrar_historico_etapa(etapa, usuario_hist, 'Informações gerais da etapa', form)
            messages.success(request, 'Etapa atualizada com sucesso.')
            return redirect(reverse('obras:etapa_detail', args=[etapa.pk]))
        else:
            messages.error(request, 'Corrija os erros no formulário.')
    else:
        form = EtapaForm(instance=etapa)
    return render(request, 'obras/etapa_form.html', {'form': form, 'etapa': etapa, 'title': f'Editar Etapa {etapa.numero_etapa} - {etapa.obra.nome}'})


@login_required
def etapa1_detail(request, pk):
    etapa = get_object_or_404(Etapa, pk=pk)
    try:
        detalhe = etapa.fundacao
    except Etapa1Fundacao.DoesNotExist:
        detalhe = Etapa1Fundacao.objects.create(etapa=etapa)
    # allow edit
    if request.method == 'POST':
        form = Etapa1FundacaoForm(request.POST, instance=detalhe)
        if form.is_valid():
            form.save()
            usuario_hist = _resolver_usuario_historico(request, form)
            _registrar_historico_etapa(etapa, usuario_hist, 'Detalhes da Etapa 1 - Fundação', form)
            messages.success(request, 'Detalhes da etapa 1 (Fundação) atualizados com sucesso.')
            return redirect(reverse('obras:etapa1_detail', args=[etapa.pk]))
    else:
        form = Etapa1FundacaoForm(instance=detalhe)
    return render(request, 'obras/etapa1_fundacao_detail.html', {'etapa': etapa, 'detalhe': detalhe, 'form': form, 'title': f'Fundação - {etapa.obra.nome}'})


@login_required
def etapa2_detail(request, pk):
    etapa = get_object_or_404(Etapa, pk=pk)
    try:
        detalhe = etapa.estrutura
    except Etapa2Estrutura.DoesNotExist:
        detalhe = Etapa2Estrutura.objects.create(etapa=etapa)
    if request.method == 'POST':
        form = Etapa2EstruturaForm(request.POST, instance=detalhe)
        if form.is_valid():
            form.save()
            usuario_hist = _resolver_usuario_historico(request, form)
            _registrar_historico_etapa(etapa, usuario_hist, 'Detalhes da Etapa 2 - Estrutura', form)
            messages.success(request, 'Detalhes da etapa 2 (Estrutura) atualizados com sucesso.')
            return redirect(reverse('obras:etapa2_detail', args=[etapa.pk]))
    else:
        form = Etapa2EstruturaForm(instance=detalhe)
    return render(request, 'obras/etapa2_estrutura_detail.html', {'etapa': etapa, 'detalhe': detalhe, 'form': form, 'title': f'Estrutura - {etapa.obra.nome}'})


@login_required
def etapa3_detail(request, pk):
    etapa = get_object_or_404(Etapa, pk=pk)
    try:
        detalhe = etapa.instalacoes
    except Etapa3Instalacoes.DoesNotExist:
        detalhe = Etapa3Instalacoes.objects.create(etapa=etapa)
    if request.method == 'POST':
        form = Etapa3InstalacoesForm(request.POST, instance=detalhe)
        if form.is_valid():
            form.save()
            usuario_hist = _resolver_usuario_historico(request, form)
            _registrar_historico_etapa(etapa, usuario_hist, 'Detalhes da Etapa 3 - Instalações', form)
            messages.success(request, 'Detalhes da etapa 3 (Instalações) atualizados com sucesso.')
            return redirect(reverse('obras:etapa3_detail', args=[etapa.pk]))
    else:
        form = Etapa3InstalacoesForm(instance=detalhe)
    return render(request, 'obras/etapa3_instalacoes_detail.html', {'etapa': etapa, 'detalhe': detalhe, 'form': form, 'title': f'Instalações - {etapa.obra.nome}'})


@login_required
def etapa4_detail(request, pk):
    etapa = get_object_or_404(Etapa, pk=pk)
    try:
        detalhe = etapa.acabamentos
    except Etapa4Acabamentos.DoesNotExist:
        detalhe = Etapa4Acabamentos.objects.create(etapa=etapa)
    if request.method == 'POST':
        form = Etapa4AcabamentosForm(request.POST, instance=detalhe)
        if form.is_valid():
            form.save()
            usuario_hist = _resolver_usuario_historico(request, form)
            _registrar_historico_etapa(etapa, usuario_hist, 'Detalhes da Etapa 4 - Acabamentos', form)
            messages.success(request, 'Detalhes da etapa 4 (Acabamentos) atualizados com sucesso.')
            return redirect(reverse('obras:etapa4_detail', args=[etapa.pk]))
    else:
        form = Etapa4AcabamentosForm(instance=detalhe)
    return render(request, 'obras/etapa4_acabamentos_detail.html', {'etapa': etapa, 'detalhe': detalhe, 'form': form, 'title': f'Acabamentos - {etapa.obra.nome}'})


@login_required
def etapa5_detail(request, pk):
    etapa = get_object_or_404(Etapa, pk=pk)
    try:
        detalhe = etapa.finalizacao
    except Etapa5Finalizacao.DoesNotExist:
        detalhe = Etapa5Finalizacao.objects.create(etapa=etapa)
    if request.method == 'POST':
        form = Etapa5FinalizacaoForm(request.POST, instance=detalhe)
        if form.is_valid():
            form.save()
            usuario_hist = _resolver_usuario_historico(request, form)
            _registrar_historico_etapa(etapa, usuario_hist, 'Detalhes da Etapa 5 - Finalização', form)
            messages.success(request, 'Detalhes da etapa 5 (Finalização) atualizados com sucesso.')
            return redirect(reverse('obras:etapa5_detail', args=[etapa.pk]))
    else:
        form = Etapa5FinalizacaoForm(instance=detalhe)
    return render(request, 'obras/etapa5_finalizacao_detail.html', {'etapa': etapa, 'detalhe': detalhe, 'form': form, 'title': f'Finalização - {etapa.obra.nome}'})


@login_required
def obra_allocations(request, pk):
    """Mostra alocações por pedreiro para cada etapa mensurável da obra."""
    obra = get_object_or_404(Obra, pk=pk)
    etapas = obra.etapas.all().order_by('numero_etapa')
    allocations = []
    for etapa in etapas:
        detalhe = None
        try:
            if etapa.numero_etapa == 1:
                detalhe = etapa.fundacao
            elif etapa.numero_etapa == 2:
                detalhe = etapa.estrutura
            elif etapa.numero_etapa == 3:
                detalhe = etapa.instalacoes
            elif etapa.numero_etapa == 4:
                detalhe = etapa.acabamentos
            elif etapa.numero_etapa == 5:
                detalhe = etapa.finalizacao
        except Exception:
            detalhe = None

        etapa_data = {'etapa': etapa, 'allocations': None}
        if detalhe and hasattr(detalhe, 'allocations_summary'):
            etapa_data['allocations'] = detalhe.allocations_summary()
        allocations.append(etapa_data)

    # human-friendly labels for measurable fields
    field_labels = {
        'reboco_externo_m2': 'Reboco Externo (m²)',
        'reboco_interno_m2': 'Reboco Interno (m²)'
    }

    # format period dates and ensure numeric strings formatted
    for item in allocations:
        allocs = item.get('allocations')
        if not allocs:
            continue
        new_allocs = {}
        for field, data in allocs.items():
            # format period
            period = data.get('period', {})
            start = period.get('start')
            end = period.get('end')
            def fmt(d):
                try:
                    return datetime.date.fromisoformat(d).strftime('%d/%m/%Y')
                except Exception:
                    return '—'
            data['period_formatted'] = {'start': fmt(start), 'end': fmt(end)}
            # ensure numbers have two decimals
            try:
                data['total'] = f"{Decimal(data.get('total') or '0'):.2f}"
            except Exception:
                pass
            try:
                data['per_worker'] = f"{Decimal(data.get('per_worker') or '0'):.2f}"
            except Exception:
                pass
            # map field key to user-friendly label
            label = field_labels.get(field, field)
            new_allocs[label] = data
        # replace allocations mapping with label-keyed mapping
        item['allocations'] = new_allocs

    context = {
        'obra': obra,
        'allocations': allocations,
        'field_labels': field_labels,
        'title': f'Alocações - {obra.nome}'
    }
    return render(request, 'obras/obra_allocations.html', context)


@login_required
def obra_allocations_csv(request, pk):
    """Export allocations CSV for an obra."""
    obra = get_object_or_404(Obra, pk=pk)
    etapas = obra.etapas.all().order_by('numero_etapa')

    # build rows
    rows = []
    for etapa in etapas:
        detalhe = None
        try:
            if etapa.numero_etapa == 1:
                detalhe = etapa.fundacao
            elif etapa.numero_etapa == 2:
                detalhe = etapa.estrutura
            elif etapa.numero_etapa == 3:
                detalhe = etapa.instalacoes
            elif etapa.numero_etapa == 4:
                detalhe = etapa.acabamentos
            elif etapa.numero_etapa == 5:
                detalhe = etapa.finalizacao
        except Exception:
            detalhe = None

        if detalhe and hasattr(detalhe, 'allocations_summary'):
            summary = detalhe.allocations_summary()
            for field, data in summary.items():
                total = data.get('total')
                workers = data.get('workers')
                per_worker = data.get('per_worker')
                # breakdown rows
                if data.get('breakdown'):
                    for b in data['breakdown']:
                        rows.append([
                            etapa.numero_etapa,
                            etapa.get_numero_etapa_display(),
                            field,
                            total,
                            workers,
                            per_worker,
                            b.get('funcionario_id'),
                            b.get('nome'),
                            b.get('value')
                        ])
                else:
                    rows.append([etapa.numero_etapa, etapa.get_numero_etapa_display(), field, total, workers, per_worker, '', '', ''])

    # Create CSV response
    filename = f"allocations_obra_{obra.pk}.csv"
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(['etapa_num', 'etapa_label', 'field', 'total', 'workers', 'per_worker', 'funcionario_id', 'funcionario_nome', 'value'])
    for r in rows:
        writer.writerow(r)
    return response
