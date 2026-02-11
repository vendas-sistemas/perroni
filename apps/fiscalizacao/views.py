from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import RegistroFiscalizacao

from django.contrib import messages
from .forms import RegistroFiscalizacaoForm
from django.db import IntegrityError
from django.core.paginator import Paginator
from django.db.models import Q


@login_required
def fiscalizacao_list(request):
    """Lista registros de fiscalização"""
    qs = RegistroFiscalizacao.objects.all().select_related('obra', 'fiscal', 'obra__cliente')

    # optional search by obra name or fiscal username
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(obra__nome__icontains=q) | Q(fiscal__username__icontains=q) | Q(fiscal__first_name__icontains=q) | Q(fiscal__last_name__icontains=q)
        )

    # Filtro por clima
    clima_filter = request.GET.get('clima', '')
    if clima_filter in ('sol', 'chuva', 'nublado'):
        qs = qs.filter(clima=clima_filter)

    # Filtro por ociosidade / retrabalho
    flag_filter = request.GET.get('flag', '')
    if flag_filter == 'ociosidade':
        qs = qs.filter(houve_ociosidade=True)
    elif flag_filter == 'retrabalho':
        qs = qs.filter(houve_retrabalho=True)

    qs = qs.order_by('-data_fiscalizacao', '-created_at')

    # Contadores
    all_qs = RegistroFiscalizacao.objects.all()
    total_fiscalizacoes = all_qs.count()
    total_ociosidade = all_qs.filter(houve_ociosidade=True).count()
    total_retrabalho = all_qs.filter(houve_retrabalho=True).count()
    total_resultado = qs.count()

    # pagination
    per_page_param = request.GET.get('per_page', '15')
    if per_page_param not in ('10', '15', '20'):
        per_page_param = '15'
    per_page = int(per_page_param)
    paginator = Paginator(qs, per_page)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    params = request.GET.copy()
    if 'page' in params:
        params.pop('page')
    querystring = params.urlencode()

    context = {
        'fiscalizacoes': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'querystring': querystring,
        'per_page': per_page,
        'title': 'Fiscalizações',
        'busca': q,
        'clima_filter': clima_filter,
        'flag_filter': flag_filter,
        'total_fiscalizacoes': total_fiscalizacoes,
        'total_ociosidade': total_ociosidade,
        'total_retrabalho': total_retrabalho,
        'total_resultado': total_resultado,
    }
    return render(request, 'fiscalizacao/fiscalizacao_list.html', context)


@login_required
def fiscalizacao_detail(request, pk):
    """Detalhes de uma fiscalização"""
    fiscalizacao = get_object_or_404(RegistroFiscalizacao, pk=pk)
    context = {
        'fiscalizacao': fiscalizacao,
        'title': f'Fiscalização - {fiscalizacao.obra.nome}'
    }
    return render(request, 'fiscalizacao/fiscalizacao_detail.html', context)


@login_required
def fiscalizacao_create(request):
    """Cria novo registro de fiscalização"""
    if request.method == 'POST':
        form = RegistroFiscalizacaoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # explicit list of files (form.save will also read from self.files)
                instance = form.save(commit=True, files=request.FILES.getlist('fotos'))
                messages.success(request, 'Fiscalização registrada com sucesso.')
                return redirect('fiscalizacao:fiscalizacao_detail', pk=instance.pk)
            except IntegrityError:
                form.add_error('data_fiscalizacao', 'Já existe um registro para esta obra e data.')
        else:
            messages.error(request, 'Corrija os erros no formulário.')
    else:
        # Pre-fill fiscal as current user when possible
        initial = {}
        if request.user.is_authenticated:
            initial['fiscal'] = request.user.pk
        form = RegistroFiscalizacaoForm(initial=initial)

    return render(request, 'fiscalizacao/fiscalizacao_form.html', {'form': form, 'title': 'Nova Fiscalização'})


@login_required
def fiscalizacao_update(request, pk):
    """Atualiza registro de fiscalização"""
    fiscalizacao = get_object_or_404(RegistroFiscalizacao, pk=pk)
    # Editing has been disabled for safety; redirect to detail view
    return redirect('fiscalizacao:fiscalizacao_detail', pk=pk)
