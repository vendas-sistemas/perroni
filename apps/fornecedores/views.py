from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FornecedorForm
from .models import Fornecedor


@login_required
def fornecedor_list(request):
    qs = Fornecedor.objects.filter(ativo=True)
    total_fornecedores = qs.count()

    busca = request.GET.get('q', '').strip()
    if busca:
        qs = qs.filter(
            models.Q(nome__icontains=busca)
            | models.Q(endereco__icontains=busca)
            | models.Q(telefone__icontains=busca)
        )

    total_resultado = qs.count()
    fornecedores_qs = qs.order_by('nome')

    total_com_endereco = Fornecedor.objects.filter(ativo=True).exclude(endereco__isnull=True).exclude(endereco='').count()
    total_com_telefone = Fornecedor.objects.filter(ativo=True).exclude(telefone__isnull=True).exclude(telefone='').count()

    per_page = int(request.GET.get('per_page', 15))
    if per_page not in (10, 15, 20):
        per_page = 15
    paginator = Paginator(fornecedores_qs, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))

    params = request.GET.copy()
    params.pop('page', None)

    context = {
        'fornecedores': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'querystring': params.urlencode(),
        'title': 'Fornecedores',
        'busca': busca,
        'per_page': per_page,
        'total_fornecedores': total_fornecedores,
        'total_resultado': total_resultado,
        'total_com_endereco': total_com_endereco,
        'total_com_telefone': total_com_telefone,
    }
    return render(request, 'fornecedores/fornecedor_list.html', context)


@login_required
def fornecedor_detail(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    return render(request, 'fornecedores/fornecedor_detail.html', {'fornecedor': fornecedor, 'title': fornecedor.nome})


@login_required
def fornecedor_create(request):
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save()
            messages.success(request, 'Fornecedor criado com sucesso.')
            return redirect('fornecedores:fornecedor_detail', pk=fornecedor.pk)
    else:
        form = FornecedorForm()

    return render(request, 'fornecedores/fornecedor_form.html', {'form': form, 'title': 'Novo Fornecedor'})


@login_required
def fornecedor_update(request, pk):
    fornecedor = get_object_or_404(Fornecedor, pk=pk)
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor atualizado.')
            return redirect('fornecedores:fornecedor_detail', pk=fornecedor.pk)
    else:
        form = FornecedorForm(instance=fornecedor)

    return render(request, 'fornecedores/fornecedor_form.html', {'form': form, 'fornecedor': fornecedor, 'title': 'Editar Fornecedor'})

