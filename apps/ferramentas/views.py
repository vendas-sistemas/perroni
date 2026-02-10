from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Ferramenta, ConferenciaFerramenta
from .forms import FerramentaForm
from django.contrib import messages


@login_required
def ferramenta_list(request):
    """Lista ferramentas"""
    ferramentas = Ferramenta.objects.filter(ativo=True).order_by('nome')
    context = {
        'ferramentas': ferramentas,
        'title': 'Ferramentas'
    }
    return render(request, 'ferramentas/ferramenta_list.html', context)


@login_required
def ferramenta_detail(request, pk):
    """Detalhes de uma ferramenta"""
    ferramenta = get_object_or_404(Ferramenta, pk=pk)
    movimentacoes = ferramenta.movimentacoes.all()[:10]
    context = {
        'ferramenta': ferramenta,
        'movimentacoes': movimentacoes,
        'title': ferramenta.nome
    }
    return render(request, 'ferramentas/ferramenta_detail.html', context)


@login_required
def ferramenta_create(request):
    """Cadastra nova ferramenta"""
    if request.method == 'POST':
        form = FerramentaForm(request.POST, request.FILES)
        if form.is_valid():
            ferramenta = form.save()
            messages.success(request, 'Ferramenta criada com sucesso.')
            return redirect('ferramentas:ferramenta_detail', pk=ferramenta.pk)
    else:
        form = FerramentaForm()

    return render(request, 'ferramentas/ferramenta_form.html', {'form': form, 'title': 'Nova Ferramenta'})


@login_required
def ferramenta_update(request, pk):
    """Edita uma ferramenta existente"""
    ferramenta = get_object_or_404(Ferramenta, pk=pk)
    if request.method == 'POST':
        form = FerramentaForm(request.POST, request.FILES, instance=ferramenta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ferramenta atualizada.')
            return redirect('ferramentas:ferramenta_detail', pk=ferramenta.pk)
    else:
        form = FerramentaForm(instance=ferramenta)

    return render(request, 'ferramentas/ferramenta_form.html', {'form': form, 'ferramenta': ferramenta, 'title': 'Editar Ferramenta'})


@login_required
def movimentacao_create(request):
    """Registra movimentação de ferramenta"""
    # TODO: Implementar formulário
    return render(request, 'ferramentas/movimentacao_form.html', {'title': 'Movimentar Ferramenta'})


@login_required
def conferencia_list(request):
    """Lista conferências de ferramentas"""
    conferencias = ConferenciaFerramenta.objects.all().select_related('obra', 'fiscal')
    context = {
        'conferencias': conferencias,
        'title': 'Conferências'
    }
    return render(request, 'ferramentas/conferencia_list.html', context)


@login_required
def conferencia_create(request):
    """Cria conferência diária"""
    # TODO: Implementar formulário
    return render(request, 'ferramentas/conferencia_form.html', {'title': 'Nova Conferência'})
