from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Funcionario, ApontamentoFuncionario, FechamentoSemanal
from .forms import FuncionarioForm, ApontamentoForm, FechamentoForm
from django.contrib import messages
from django.utils import timezone
import datetime


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
    # TODO: Implementar formulário de inativação
    return render(request, 'funcionarios/funcionario_inativar.html', {
        'funcionario': funcionario,
        'title': 'Inativar Funcionário'
    })


@login_required
def apontamento_list(request):
    """Lista apontamentos"""
    apontamentos = ApontamentoFuncionario.objects.all().select_related('funcionario', 'obra').order_by('-data')
    context = {
        'apontamentos': apontamentos,
        'title': 'Apontamentos'
    }
    return render(request, 'funcionarios/apontamento_list.html', context)


@login_required
def apontamento_create(request):
    """Cria apontamento diário"""
    if request.method == 'POST':
        form = ApontamentoForm(request.POST)
        if form.is_valid():
            ap = form.save(commit=False)
            # auto-fill valor_diaria if empty
            if not ap.valor_diaria:
                ap.valor_diaria = ap.funcionario.valor_diaria
            ap.save()
            messages.success(request, 'Apontamento salvo com sucesso.')
            return redirect('funcionarios:apontamento_list')
        else:
            messages.error(request, 'Corrija os erros no formulário.')
    else:
        form = ApontamentoForm()
    return render(request, 'funcionarios/apontamento_form.html', {'form': form, 'title': 'Novo Apontamento'})


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
            # determine data_fim as data_inicio + 6 dias
            f.data_fim = f.data_inicio + datetime.timedelta(days=6)
            f.status = 'aberto'
            f.save()
            f.calcular_totais()
            messages.success(request, 'Fechamento criado e totais calculados.')
            return redirect('funcionarios:fechamento_list')
        else:
            messages.error(request, 'Corrija os erros no formulário.')
    else:
        form = FechamentoForm()
    return render(request, 'funcionarios/fechamento_form.html', {'form': form, 'title': 'Novo Fechamento Semanal'})


@login_required
def fechamento_detail(request, pk):
    fechamento = get_object_or_404(FechamentoSemanal, pk=pk)
    # show apontamentos relacionados
    apontamentos = ApontamentoFuncionario.objects.filter(
        funcionario=fechamento.funcionario,
        data__gte=fechamento.data_inicio,
        data__lte=fechamento.data_fim
    ).select_related('obra')
    context = {
        'fechamento': fechamento,
        'apontamentos': apontamentos,
        'title': f'Fechamento - {fechamento.funcionario.nome_completo}'
    }
    return render(request, 'funcionarios/fechamento_detail.html', context)
