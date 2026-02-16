def navigation_permissions(request):
    user = getattr(request, 'user', None)

    nav_perms = {
        'obras': False,
        'fiscalizacao': False,
        'funcionarios': False,
        'ferramentas': False,
        'clientes': False,
        'analytics': False,
        'relatorios': False,
        'admin': False,
    }

    if not user or not user.is_authenticated:
        return {'nav_perms': nav_perms}

    if user.is_superuser:
        for key in nav_perms:
            nav_perms[key] = True
        return {'nav_perms': nav_perms}

    nav_perms['obras'] = user.has_module_perms('obras')
    nav_perms['fiscalizacao'] = user.has_module_perms('fiscalizacao')
    nav_perms['funcionarios'] = user.has_module_perms('funcionarios')
    nav_perms['ferramentas'] = user.has_module_perms('ferramentas')
    nav_perms['clientes'] = user.has_module_perms('clientes')
    nav_perms['analytics'] = user.has_module_perms('analytics')
    nav_perms['relatorios'] = user.has_module_perms('relatorios')
    nav_perms['admin'] = bool(user.is_staff)

    return {'nav_perms': nav_perms}
