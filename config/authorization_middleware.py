from django.http import HttpResponseForbidden

from config.access_control import resolve_area_from_request


class ModulePermissionMiddleware:
    """Enforce module/area permissions based on group settings."""

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

        area = resolve_area_from_request(app_name, view_name)
        if not self._has_area_permission(user, area, 'view'):
            return HttpResponseForbidden('Você não tem permissão para acessar este módulo.')

        required_action = self._required_action(request.method, view_name)
        if request.method not in self.SAFE_METHODS and not self._has_area_permission(user, area, required_action):
            return HttpResponseForbidden('Você não tem permissão para alterar dados neste módulo.')

        return self.get_response(request)

    @staticmethod
    def _has_area_permission(user, area: str, action: str) -> bool:
        if not area:
            return True
        if user.is_superuser:
            return True
        try:
            from apps.configuracoes.models import GroupAreaPermission
        except Exception:
            return False

        field_name = {
            'view': 'can_view',
            'create': 'can_create',
            'edit': 'can_edit',
            'delete': 'can_delete',
        }.get(action, 'can_view')

        return GroupAreaPermission.objects.filter(
            group__user=user,
            area=area,
            **{field_name: True},
        ).exists()

    @staticmethod
    def _required_action(method: str, view_name: str) -> str:
        if method in {'DELETE'}:
            return 'delete'

        lower = (view_name or '').lower()
        if any(token in lower for token in ('delete', 'excluir', 'remove')):
            return 'delete'
        if any(token in lower for token in ('create', 'criar', 'novo')):
            return 'create'
        if any(token in lower for token in ('update', 'edit', 'editar')):
            return 'edit'
        if method in {'POST', 'PUT', 'PATCH'}:
            return 'edit'
        return 'view'
