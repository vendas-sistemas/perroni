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
        'configuracoes': False,
    }

    if not user or not user.is_authenticated:
        return {'nav_perms': nav_perms}

    if user.is_superuser:
        for key in nav_perms:
            nav_perms[key] = True
        return {'nav_perms': nav_perms}

    try:
        from apps.configuracoes.models import GroupAreaPermission
    except Exception:
        nav_perms['admin'] = bool(user.is_staff)
        nav_perms['configuracoes'] = bool(user.is_staff)
        return {'nav_perms': nav_perms}

    area_map = {
        'obras': 'obras',
        'funcionarios': 'funcionarios',
        'ferramentas': 'ferramentas',
        'clientes': 'clientes',
        'analytics': 'analytics',
        'relatorios': 'relatorios',
    }
    for nav_key, area in area_map.items():
        nav_perms[nav_key] = GroupAreaPermission.objects.filter(
            group__user=user,
            area=area,
            can_view=True,
        ).exists()

    nav_perms['fiscalizacao'] = False
    nav_perms['admin'] = bool(user.is_staff)
    nav_perms['configuracoes'] = bool(user.is_staff or user.is_superuser)

    return {'nav_perms': nav_perms}

