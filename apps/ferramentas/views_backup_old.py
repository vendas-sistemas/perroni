from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import Ferramenta, ConferenciaFerramenta, MovimentacaoFerramenta, ItemConferencia
from .forms import FerramentaForm, MovimentacaoForm, ConferenciaForm, ItemConferenciaForm
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.urls import reverse_lazy
from django.views import View
from django.forms import inlineformset_factory
from django.db import transaction
from django.shortcuts import render
from django.http import Http404
from django.utils import timezone
import random
from decimal import Decimal


@login_required
def ferramenta_list(request):
    """Lista ferramentas"""
    qs = Ferramenta.objects.filter(ativo=True)

    # Filters from GET
    codigo = request.GET.get('codigo')
    nome = request.GET.get('nome')
    categoria = request.GET.get('categoria')
    status_filter = request.GET.get('status')
    obra = request.GET.get('obra')
    busca = request.GET.get('q', '').strip()

    if busca:
        qs = qs.filter(
            models.Q(nome__icontains=busca) |
            models.Q(codigo__icontains=busca)
        )
    if codigo:
        qs = qs.filter(codigo__icontains=codigo)
    if nome:
        qs = qs.filter(nome__icontains=nome)
    if categoria:
        qs = qs.filter(categoria=categoria)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if obra:
        qs = qs.filter(obra_atual__nome__icontains=obra)

    # Ordering
    order = request.GET.get('order', 'nome')
    direction = request.GET.get('dir', 'asc')
    allowed = {
        'codigo': 'codigo',
        'nome': 'nome',
        'categoria': 'categoria',
        'status': 'status',
        'obra': 'obra_atual__nome'
    }
    order_field = allowed.get(order, 'nome')
    if direction == 'desc':
        order_field = f'-{order_field}'
    qs = qs.order_by(order_field)

    # Contadores
    all_active = Ferramenta.objects.filter(ativo=True)
    total_ferramentas = all_active.count()
    total_deposito = all_active.filter(status='deposito').count()
    total_em_obra = all_active.filter(status='em_obra').count()
    total_manutencao = all_active.filter(status='manutencao').count()
    total_resultado = qs.count()

    # Pagination
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    per_page_param = request.GET.get('per_page', '15')
    if per_page_param not in ('10', '15', '20'):
        per_page_param = '15'
    per_page = int(per_page_param)
    paginator = Paginator(qs, per_page)
    page = request.GET.get('page')
    try:
        ferramentas_page = paginator.page(page)
    except PageNotAnInteger:
        ferramentas_page = paginator.page(1)
    except EmptyPage:
        ferramentas_page = paginator.page(paginator.num_pages)

    # Build base querystring (keep filters but remove page/order/dir)
    params = request.GET.copy()
    for k in ('page', 'order', 'dir'):
        if k in params:
            params.pop(k)
    base_qs = params.urlencode()

    context = {
        'ferramentas': ferramentas_page,
        'title': 'Ferramentas',
        'base_qs': base_qs,
        'current_order': order,
        'current_dir': direction,
        'paginator': paginator,
        'per_page': per_page,
        'category_choices': [(k, v) for k, v in Ferramenta._meta.get_field('categoria').choices],
        'status_choices': [(k, v) for k, v in Ferramenta._meta.get_field('status').choices],
        'busca': busca,
        'status_filter': status_filter or '',
        'categoria_filter': categoria or '',
        'total_ferramentas': total_ferramentas,
        'total_deposito': total_deposito,
        'total_em_obra': total_em_obra,
        'total_manutencao': total_manutencao,
        'total_resultado': total_resultado,
    }
    return render(request, 'ferramentas/ferramenta_list.html', context)


@login_required
def ferramenta_detail(request, pk):
    """Detalhes de uma ferramenta"""
    ferramenta = get_object_or_404(Ferramenta, pk=pk)
    movimentacoes_qs = ferramenta.movimentacoes.select_related('responsavel', 'obra_origem', 'obra_destino').all()
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(movimentacoes_qs, 10)
    page = request.GET.get('page')
    try:
        movimentacoes = paginator.page(page)
    except PageNotAnInteger:
        movimentacoes = paginator.page(1)
    except EmptyPage:
        movimentacoes = paginator.page(paginator.num_pages)
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
            # If codigo missing, generate a unique code
            codigo = form.cleaned_data.get('codigo')
            if not codigo:
                prefixes = ['FRR', 'TLS', 'SEG', 'MED', 'OTR']
                tentativa = 0
                codigo = None
                existing = set(Ferramenta.objects.values_list('codigo', flat=True))
                while tentativa < 20:
                    prefix = random.choice(prefixes)
                    numero = random.randint(10000, 99999)
                    candidate = f"{prefix}-{numero}"
                    if candidate not in existing:
                        codigo = candidate
                        break
                    tentativa += 1
                if not codigo:
                    # fallback to timestamp-based code
                    codigo = f"FERR-{int(timezone.now().timestamp())}"
                # inject into form instance
                form.instance.codigo = codigo

            ferramenta = form.save()
            MovimentacaoFerramenta.objects.create(
                ferramenta=ferramenta,
                tipo='entrada_deposito',
                origem='Cadastro inicial',
                destino='Depósito',
                responsavel=request.user,
                observacoes='Movimentação inicial criada automaticamente no cadastro da ferramenta.'
            )
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
    if request.method == 'POST':
        form = MovimentacaoForm(request.POST)
        if form.is_valid():
            mov = form.save(commit=False)
            mov.responsavel = request.user
            mov.save()
            messages.success(request, 'Movimentação registrada.')
            return redirect('ferramentas:ferramenta_detail', pk=mov.ferramenta.pk)
    else:
        # allow preselecting ferramenta via GET param ?f=<pk>
        f_pk = request.GET.get('f')
        if f_pk:
            form = MovimentacaoForm(initial={'ferramenta': f_pk})
        else:
            form = MovimentacaoForm()

    return render(request, 'ferramentas/movimentacao_form.html', {'form': form, 'title': 'Movimentar Ferramenta'})


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
def conferencia_detail(request, pk):
    conf = get_object_or_404(ConferenciaFerramenta, pk=pk)
    itens = conf.itens.select_related('ferramenta').all()
    context = {
        'conferencia': conf,
        'itens': itens,
        'title': f'Conferência - {conf.obra.nome}'
    }
    return render(request, 'ferramentas/conferencia_detail.html', context)


@login_required
def conferencia_create(request):
    """Cria conferência diária"""
    if request.method == 'POST':
        form = ConferenciaForm(request.POST)
        if form.is_valid():
            conf = form.save(commit=False)
            conf.fiscal = request.user
            conf.data_conferencia = timezone.localtime()
            conf.save()
            messages.success(request, 'Conferência criada.')
            return redirect('ferramentas:conferencia_list')
    else:
        form = ConferenciaForm()

    return render(request, 'ferramentas/conferencia_form.html', {'form': form, 'title': 'Nova Conferência'})


class ConferenciaCreateView(LoginRequiredMixin, generic.CreateView):
    model = ConferenciaFerramenta
    form_class = ConferenciaForm
    template_name = 'ferramentas/conferencia_form.html'
    success_url = reverse_lazy('ferramentas:conferencia_list')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.fiscal = self.request.user
        obj.data_conferencia = timezone.localtime()
        obj.save()
        messages.success(self.request, 'Conferência criada.')
        return super().form_valid(form)


class ItemConferenciaCreateView(LoginRequiredMixin, generic.CreateView):
    model = ItemConferencia
    form_class = ItemConferenciaForm
    template_name = 'ferramentas/itemconferencia_form.html'

    def get_initial(self):
        initial = super().get_initial()
        conferencia_pk = self.kwargs.get('conferencia_pk')
        if conferencia_pk:
            initial['conferencia'] = conferencia_pk
        return initial

    def form_valid(self, form):
        obj = form.save(commit=False)
        if not obj.conferencia_id:
            obj.conferencia = get_object_or_404(ConferenciaFerramenta, pk=self.kwargs.get('conferencia_pk'))
        obj.save()
        messages.success(self.request, 'Item adicionado à conferência.')
        return redirect('ferramentas:conferencia_list')


class MovimentacaoCreateView(LoginRequiredMixin, generic.CreateView):
    model = MovimentacaoFerramenta
    form_class = MovimentacaoForm
    template_name = 'ferramentas/movimentacao_form.html'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.responsavel = self.request.user
        obj.save()
        messages.success(self.request, 'Movimentação registrada.')
        return redirect('ferramentas:ferramenta_detail', pk=obj.ferramenta.pk)

    def get_initial(self):
        initial = super().get_initial()
        f_pk = self.request.GET.get('f')
        if f_pk:
            initial['ferramenta'] = f_pk
        return initial


class ConferenciaWithItemsCreateView(LoginRequiredMixin, View):
    """Create a Conferencia and multiple ItemConferencia at once using an inline formset."""
    template_name = 'ferramentas/conferencia_form_with_items.html'
    form_class = ConferenciaForm
    ItemFormSet = inlineformset_factory(
        parent_model=ConferenciaFerramenta,
        model=ItemConferencia,
        form=ItemConferenciaForm,
        extra=8,
        can_delete=True
    )

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        formset = self.ItemFormSet()
        return render(request, self.template_name, {'form': form, 'formset': formset, 'title': 'Nova Conferência (várias ferramentas)'} )

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        formset = self.ItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                conferencia = form.save(commit=False)
                conferencia.fiscal = request.user
                conferencia.data_conferencia = timezone.localtime()
                conferencia.save()
                items = formset.save(commit=False)
                for item in items:
                    item.conferencia = conferencia
                    item.save()
                for obj in formset.deleted_objects:
                    obj.delete()
            messages.success(request, 'Conferência e itens salvos com sucesso.')
            return redirect('ferramentas:conferencia_list')

        return render(request, self.template_name, {'form': form, 'formset': formset, 'title': 'Nova Conferência (várias ferramentas)'} )


class ConferenciaItemsManageView(LoginRequiredMixin, View):
    """Manage items for an existing Conferencia: show existing items and allow adding/removing many at once."""
    template_name = 'ferramentas/conferencia_form_with_items.html'
    form_class = ConferenciaForm
    ItemFormSet = inlineformset_factory(
        parent_model=ConferenciaFerramenta,
        model=ItemConferencia,
        form=ItemConferenciaForm,
        extra=3,
        can_delete=True
    )

    def get_object(self, pk):
        try:
            return ConferenciaFerramenta.objects.get(pk=pk)
        except ConferenciaFerramenta.DoesNotExist:
            raise Http404()

    def get(self, request, conferencia_pk, *args, **kwargs):
        conferencia = self.get_object(conferencia_pk)
        form = self.form_class(instance=conferencia)
        formset = self.ItemFormSet(instance=conferencia)
        return render(request, self.template_name, {'form': form, 'formset': formset, 'title': f'Conferência {conferencia.obra.nome} - Itens'})

    def post(self, request, conferencia_pk, *args, **kwargs):
        conferencia = self.get_object(conferencia_pk)
        form = self.form_class(request.POST, instance=conferencia)
        formset = self.ItemFormSet(request.POST, instance=conferencia)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                instances = formset.save(commit=False)
                for inst in instances:
                    inst.conferencia = conferencia
                    inst.save()
                # handle deletions
                for obj in formset.deleted_objects:
                    obj.delete()
            messages.success(request, 'Conferência e itens atualizados com sucesso.')
            return redirect('ferramentas:conferencia_detail', pk=conferencia.pk)

        return render(request, self.template_name, {'form': form, 'formset': formset, 'title': f'Conferência {conferencia.obra.nome} - Itens'})

    # end of ConferenciaItemsManageView
