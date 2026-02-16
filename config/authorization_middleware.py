from django.http import HttpResponseForbidden


class ModulePermissionMiddleware:
    """Enforce app-level permissions for project modules.

    - Safe methods (GET/HEAD/OPTIONS): user must have any permission in the app.
    - Unsafe methods (POST/PUT/PATCH/DELETE): user must also have any write
      permission (add/change/delete) in the app.
    """

    PROTECTED_APPS = {
        'obras',
        'fiscalizacao',
        'funcionarios',
        'ferramentas',
        'clientes',
        'analytics',
        'relatorios',
    }

    SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'}

    ALLOWED_VIEW_NAMES = {
        'funcionarios:set_theme',
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)

        if not user or not user.is_authenticated or user.is_superuser:
            return self.get_response(request)

        resolver_match = getattr(request, 'resolver_match', None)
        if resolver_match is None:
            return self.get_response(request)

        app_name = resolver_match.app_name
        if app_name not in self.PROTECTED_APPS:
            return self.get_response(request)

        view_name = resolver_match.view_name
        if view_name in self.ALLOWED_VIEW_NAMES:
            return self.get_response(request)

        if not user.has_module_perms(app_name):
            return HttpResponseForbidden('Você não tem permissão para acessar este módulo.')

        if request.method not in self.SAFE_METHODS and not self._has_write_permission(user, app_name):
            return HttpResponseForbidden('Você não tem permissão para alterar dados neste módulo.')

        return self.get_response(request)

    @staticmethod
    def _has_write_permission(user, app_name: str) -> bool:
        for perm in user.get_all_permissions():
            if not perm.startswith(f'{app_name}.'):
                continue
            codename = perm.split('.', 1)[1]
            if codename.startswith(('add_', 'change_', 'delete_')):
                return True
        return False
