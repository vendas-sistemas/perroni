from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cliente
from .forms import ClienteForm
from django.core.paginator import Paginator


@login_required
def cliente_list(request):
    qs = Cliente.objects.filter(ativo=True)

    # filters
    nome = request.GET.get('nome')
    cpf = request.GET.get('cpf')
    telefone = request.GET.get('telefone')
    email = request.GET.get('email')

    if nome:
        qs = qs.filter(nome__icontains=nome)
    if cpf:
        qs = qs.filter(cpf__icontains=cpf)
    if telefone:
        qs = qs.filter(telefone__icontains=telefone)
    if email:
        qs = qs.filter(email__icontains=email)

    clientes_qs = qs.order_by('nome')

    # pagination
    per_page = 25
    paginator = Paginator(clientes_qs, per_page)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    # build querystring without page to preserve filters when paginating
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
        'filters': {
            'nome': nome or '',
            'cpf': cpf or '',
            'telefone': telefone or '',
            'email': email or '',
        }
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
