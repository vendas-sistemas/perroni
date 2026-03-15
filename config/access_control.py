from __future__ import annotations

from typing import Dict, List


AREAS: List[Dict[str, str]] = [
    {'key': 'obras', 'label': 'Obras'},
    {'key': 'funcionarios', 'label': 'Funcionários'},
    {'key': 'funcionarios_apontamentos', 'label': 'Funcionários - Apontamentos'},
    {'key': 'funcionarios_fechamentos', 'label': 'Funcionários - Fechamentos'},
    {'key': 'ferramentas', 'label': 'Ferramentas'},
    {'key': 'analytics', 'label': 'Analytics'},
    {'key': 'relatorios', 'label': 'Relatórios'},
    {'key': 'clientes', 'label': 'Clientes'},
    {'key': 'fornecedores', 'label': 'Fornecedores'},
]

AREA_KEYS = [a['key'] for a in AREAS]
AREA_CHOICES = [(a['key'], a['label']) for a in AREAS]

ACTION_KEYS = ['view', 'create', 'edit', 'delete']


def resolve_area_from_request(app_name: str, view_name: str) -> str:
    if app_name == 'funcionarios':
        lower = (view_name or '').lower()
        if 'apontamento' in lower:
            return 'funcionarios_apontamentos'
        if 'fechamento' in lower:
            return 'funcionarios_fechamentos'
        return 'funcionarios'

    if app_name in {'obras', 'ferramentas', 'analytics', 'relatorios', 'clientes', 'fornecedores'}:
        return app_name

    return ''

