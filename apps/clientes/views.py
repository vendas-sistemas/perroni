from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import Cliente
from .forms import ClienteForm
from django.core.paginator import Paginator


@login_required
def cliente_list(request):
    qs = Cliente.objects.filter(ativo=True)
    total_clientes = qs.count()

    # search
    busca = request.GET.get('q', '').strip()
    if busca:
        qs = qs.filter(
            models.Q(nome__icontains=busca)
            | models.Q(cpf__icontains=busca)
            | models.Q(telefone__icontains=busca)
            | models.Q(email__icontains=busca)
        )

    total_resultado = qs.count()
    clientes_qs = qs.order_by('nome')

    # counters
    total_com_email = Cliente.objects.filter(ativo=True).exclude(email__isnull=True).exclude(email='').count()
    total_com_telefone = Cliente.objects.filter(ativo=True).exclude(telefone__isnull=True).exclude(telefone='').count()

    # pagination
    per_page = int(request.GET.get('per_page', 15))
    if per_page not in (10, 15, 20):
        per_page = 15
    paginator = Paginator(clientes_qs, per_page)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    # build querystring without page
    params = request.GET.copy()
    if 'page' in params:
        params.pop('page')
    querystring = params.urlencode()

    context = {
        'clientes': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'querystring': querystring,
        'title': 'Clientes',
        'busca': busca,
        'per_page': per_page,
        'total_clientes': total_clientes,
        'total_resultado': total_resultado,
        'total_com_email': total_com_email,
        'total_com_telefone': total_com_telefone,
    }
    return render(request, 'clientes/cliente_list.html', context)


@login_required
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'clientes/cliente_detail.html', {'cliente': cliente, 'title': cliente.nome})


@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, 'Cliente criado com sucesso.')
            return redirect('clientes:cliente_detail', pk=cliente.pk)
    else:
        form = ClienteForm()

    return render(request, 'clientes/cliente_form.html', {'form': form, 'title': 'Novo Cliente'})


@login_required
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado.')
            return redirect('clientes:cliente_detail', pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'clientes/cliente_form.html', {'form': form, 'cliente': cliente, 'title': 'Editar Cliente'})
