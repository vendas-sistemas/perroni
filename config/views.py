from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def home_redirect(request):
    user = request.user

    if user.is_superuser:
        return redirect('obras:obra_list')

    ordered_modules = [
        ('obras', 'obras:obra_list'),
        ('fiscalizacao', 'fiscalizacao:fiscalizacao_list'),
        ('funcionarios', 'funcionarios:funcionario_list'),
        ('ferramentas', 'ferramentas:ferramenta_list'),
        ('clientes', 'clientes:cliente_list'),
        ('analytics', 'analytics:dashboard'),
        ('relatorios', 'relatorios:dashboard'),
    ]

    for app_label, route_name in ordered_modules:
        if user.has_module_perms(app_label):
            return redirect(route_name)

    if user.is_staff:
        return redirect('/admin/')

    return redirect('login')
