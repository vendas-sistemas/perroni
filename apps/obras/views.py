from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Obra, Etapa
from .forms import ObraForm
from .forms import (
    EtapaForm, Etapa1FundacaoForm, Etapa2EstruturaForm,
    Etapa3InstalacoesForm, Etapa4AcabamentosForm, Etapa5FinalizacaoForm
)
from .models import (
    Etapa1Fundacao, Etapa2Estrutura, Etapa3Instalacoes,
    Etapa4Acabamentos, Etapa5Finalizacao
)
from django.shortcuts import Http404
from django.urls import reverse


@login_required
def obra_list(request):
    """Lista todas as obras"""
    obras = Obra.objects.filter(ativo=True).order_by('-created_at')
    context = {
        'obras': obras,
        'title': 'Obras'
    }
    return render(request, 'obras/obra_list.html', context)


@login_required
def obra_detail(request, pk):
    """Detalhes de uma obra"""
    obra = get_object_or_404(Obra, pk=pk)
    context = {
        'obra': obra,
        'title': f'Obra: {obra.nome}'
    }
    return render(request, 'obras/obra_detail.html', context)


@login_required
def obra_create(request):
    """Cria uma nova obra e gera 5 etapas iniciais"""
    if request.method == 'POST':
        form = ObraForm(request.POST)
        if form.is_valid():
            obra = form.save()
            # Criar 5 etapas básicas se não existirem
            for num, _label in Etapa.ETAPA_CHOICES:
                Etapa.objects.create(
                    obra=obra,
                    numero_etapa=num,
                    percentual_valor=Etapa.PERCENTUAIS_ETAPA.get(num)
                )
            messages.success(request, 'Obra criada com sucesso.')
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
            form.save()
            messages.success(request, 'Obra atualizada com sucesso.')
            return redirect('obras:obra_detail', pk=obra.pk)
        else:
            messages.error(request, 'Corrija os erros no formulário.')
    else:
        form = ObraForm(instance=obra)
    return render(request, 'obras/obra_form.html', {'form': form, 'obra': obra, 'title': 'Editar Obra'})


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
def obra_inicializar_detalhes(request, pk):
    """Cria os registros de detalhe (OneToOne) para cada etapa que estiver faltando."""
    obra = get_object_or_404(Obra, pk=pk)
    created = 0
    for etapa in obra.etapas.all():
        num = etapa.numero_etapa
        try:
            if num == 1:
                _ = etapa.fundacao
            elif num == 2:
                _ = etapa.estrutura
            elif num == 3:
                _ = etapa.instalacoes
            elif num == 4:
                _ = etapa.acabamentos
            elif num == 5:
                _ = etapa.finalizacao
        except Exception:
            # cria o detalhe correspondente
            if num == 1:
                Etapa1Fundacao.objects.create(etapa=etapa)
            elif num == 2:
                Etapa2Estrutura.objects.create(etapa=etapa)
            elif num == 3:
                Etapa3Instalacoes.objects.create(etapa=etapa)
            elif num == 4:
                Etapa4Acabamentos.objects.create(etapa=etapa)
            elif num == 5:
                Etapa5Finalizacao.objects.create(etapa=etapa)
            created += 1

    if created:
        messages.success(request, f'Inicializados {created} detalhes de etapa para a obra.')
    else:
        messages.info(request, 'Todos os detalhes das etapas já estão inicializados.')
    return redirect(reverse('obras:obra_etapas', args=[obra.pk]))


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
        raise Http404('Detalhe não encontrado')
    # allow edit
    if request.method == 'POST':
        form = Etapa1FundacaoForm(request.POST, instance=detalhe)
        if form.is_valid():
            form.save()
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
        raise Http404('Detalhe não encontrado')
    if request.method == 'POST':
        form = Etapa2EstruturaForm(request.POST, instance=detalhe)
        if form.is_valid():
            form.save()
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
        raise Http404('Detalhe não encontrado')
    if request.method == 'POST':
        form = Etapa3InstalacoesForm(request.POST, instance=detalhe)
        if form.is_valid():
            form.save()
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
        raise Http404('Detalhe não encontrado')
    if request.method == 'POST':
        form = Etapa4AcabamentosForm(request.POST, instance=detalhe)
        if form.is_valid():
            form.save()
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
        raise Http404('Detalhe não encontrado')
    if request.method == 'POST':
        form = Etapa5FinalizacaoForm(request.POST, instance=detalhe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Detalhes da etapa 5 (Finalização) atualizados com sucesso.')
            return redirect(reverse('obras:etapa5_detail', args=[etapa.pk]))
    else:
        form = Etapa5FinalizacaoForm(instance=detalhe)
    return render(request, 'obras/etapa5_finalizacao_detail.html', {'etapa': etapa, 'detalhe': detalhe, 'form': form, 'title': f'Finalização - {etapa.obra.nome}'})
