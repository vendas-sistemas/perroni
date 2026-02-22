from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404, redirect, render

from apps.configuracoes.forms import GroupManageForm, UserManageForm
from config.access_control import AREAS


def _is_admin_user(user):
    return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff))


admin_required = user_passes_test(_is_admin_user)


def _build_group_area_rows(form):
    rows = []
    for area in AREAS:
        key = area['key']
        rows.append(
            {
                'label': area['label'],
                'view': form[f'{key}_view'],
                'create': form[f'{key}_create'],
                'edit': form[f'{key}_edit'],
                'delete': form[f'{key}_delete'],
            }
        )
    return rows


@login_required
@admin_required
def configuracoes_home(request):
    return redirect('configuracoes:user_list')


@login_required
@admin_required
def group_list(request):
    grupos = Group.objects.order_by('name')
    return render(
        request,
        'configuracoes/group_list.html',
        {
            'title': 'Configurações - Grupos',
            'grupos': grupos,
        },
    )


@login_required
@admin_required
def group_create(request):
    if request.method == 'POST':
        form = GroupManageForm(request.POST)
        if form.is_valid():
            grupo = form.save()
            form.instance = grupo
            form.save_permissions()
            messages.success(request, 'Grupo criado com sucesso.')
            return redirect('configuracoes:group_list')
    else:
        form = GroupManageForm()

    return render(
        request,
        'configuracoes/group_form.html',
        {
            'title': 'Novo Grupo',
            'form': form,
            'area_rows': _build_group_area_rows(form),
            'grupo': None,
        },
    )


@login_required
@admin_required
def group_update(request, pk):
    grupo = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        form = GroupManageForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()
            form.save_permissions()
            messages.success(request, 'Grupo atualizado com sucesso.')
            return redirect('configuracoes:group_list')
    else:
        form = GroupManageForm(instance=grupo)

    return render(
        request,
        'configuracoes/group_form.html',
        {
            'title': f'Editar Grupo - {grupo.name}',
            'form': form,
            'area_rows': _build_group_area_rows(form),
            'grupo': grupo,
        },
    )


@login_required
@admin_required
def group_delete(request, pk):
    grupo = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        grupo.delete()
        messages.success(request, 'Grupo excluído com sucesso.')
        return redirect('configuracoes:group_list')
    return render(
        request,
        'configuracoes/group_delete_confirm.html',
        {'title': 'Excluir Grupo', 'grupo': grupo},
    )


@login_required
@admin_required
def user_list(request):
    usuarios = User.objects.prefetch_related('groups').order_by('username')
    for u in usuarios:
        if not hasattr(u, 'profile'):
            from apps.funcionarios.models import UserProfile
            UserProfile.objects.get_or_create(user=u)
    usuarios = usuarios.select_related('profile')
    return render(
        request,
        'configuracoes/user_list.html',
        {
            'title': 'Configurações - Usuários',
            'usuarios': usuarios,
        },
    )


@login_required
@admin_required
def user_create(request):
    if request.method == 'POST':
        form = UserManageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário criado com sucesso.')
            return redirect('configuracoes:user_list')
    else:
        form = UserManageForm()
    return render(
        request,
        'configuracoes/user_form.html',
        {'title': 'Novo Usuário', 'form': form, 'usuario_obj': None},
    )


@login_required
@admin_required
def user_update(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserManageForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário atualizado com sucesso.')
            return redirect('configuracoes:user_list')
    else:
        form = UserManageForm(instance=usuario)
    return render(
        request,
        'configuracoes/user_form.html',
        {'title': f'Editar Usuário - {usuario.username}', 'form': form, 'usuario_obj': usuario},
    )
