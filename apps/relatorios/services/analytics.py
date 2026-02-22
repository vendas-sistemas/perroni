"""
Camada de serviço para análises de produção diária.
Lê diretamente do ApontamentoFuncionario (apontamentos diários).
Todas as queries utilizam ORM com annotate / aggregate / Avg / Count.
"""

from collections import defaultdict

from django.db.models import Avg, Count, Q

from apps.funcionarios.models import ApontamentoFuncionario


ETAPA_NOMES = {
    1: 'Etapa 1 — Fundação',
    2: 'Etapa 2 — Estrutura',
    3: 'Etapa 3 — Revestimentos e Instalações',
    4: 'Etapa 4 — Acabamentos',
    5: 'Etapa 5 — Finalização',
}


def _base_qs(filtros: dict | None = None):
    """Retorna queryset base de apontamentos de pedreiros com filtros opcionais."""
    qs = (
        ApontamentoFuncionario.objects
        .filter(funcionario__funcao='pedreiro')
        .select_related('funcionario', 'obra', 'etapa')
    )
    if not filtros:
        return qs

    if filtros.get('obra_id'):
        qs = qs.filter(obra_id=filtros['obra_id'])
    if filtros.get('etapa_id'):
        qs = qs.filter(etapa_id=filtros['etapa_id'])
    if filtros.get('funcionario_id'):
        qs = qs.filter(funcionario_id=filtros['funcionario_id'])
    if filtros.get('data_inicio'):
        qs = qs.filter(data__gte=filtros['data_inicio'])
    if filtros.get('data_fim'):
        qs = qs.filter(data__lte=filtros['data_fim'])
    if filtros.get('clima'):
        qs = qs.filter(clima=filtros['clima'])

    return qs


# ─────────────────────────────────────────────
# 1) Ranking 3 melhores / 3 piores por etapa
# ─────────────────────────────────────────────

def ranking_por_etapa(filtros: dict | None = None):
    """
    Para cada etapa retorna os 3 melhores e 3 piores pedreiros
    com base na média de metragem executada por dia.
    Ignora registros com metragem_executada = 0.
    """
    qs = _base_qs(filtros).filter(
        etapa__isnull=False,
        metragem_executada__gt=0,
    )

    stats = (
        qs
        .values(
            'etapa_id',
            'etapa__numero_etapa',
            'funcionario_id',
            'funcionario__nome_completo',
        )
        .annotate(
            media_metragem=Avg('metragem_executada'),
            total_dias=Count('id'),
        )
        .order_by('etapa_id', '-media_metragem')
    )

    por_etapa = defaultdict(list)
    etapa_labels = {}

    for row in stats:
        eid = row['etapa_id']
        num = row['etapa__numero_etapa']
        por_etapa[eid].append({
            'funcionario_id': row['funcionario_id'],
            'nome': row['funcionario__nome_completo'],
            'media_metragem': round(float(row['media_metragem']), 2),
            'total_dias': row['total_dias'],
        })
        if eid not in etapa_labels:
            etapa_labels[eid] = ETAPA_NOMES.get(num, f'Etapa {num}')

    resultado = []
    for eid, items in por_etapa.items():
        sorted_items = sorted(items, key=lambda x: x['media_metragem'], reverse=True)
        resultado.append({
            'etapa_id': eid,
            'etapa_nome': etapa_labels.get(eid, ''),
            'melhores': sorted_items[:3],
            'piores': sorted_items[-3:] if len(sorted_items) > 3 else sorted_items[::-1][:3],
        })

    resultado.sort(key=lambda x: x['etapa_nome'])
    return resultado


# ─────────────────────────────────────────────
# 2) Média de dias para execução de cada etapa
# ─────────────────────────────────────────────

def media_dias_por_etapa(filtros: dict | None = None):
    """
    Calcula, para cada etapa, quantos dias distintos foram trabalhados por
    cada obra e depois faz a média.
    Exclui etapas concluídas e obras concluídas do cálculo.
    """
    qs = _base_qs(filtros).filter(
        etapa__isnull=False,
        # Excluir etapas concluídas
        etapa__concluida=False,
        # Excluir obras concluídas
        obra__status__in=['planejamento', 'em_andamento'],
    )

    dias_por_obra = (
        qs
        .values('etapa_id', 'etapa__numero_etapa', 'obra_id')
        .annotate(dias=Count('data', distinct=True))
    )

    etapa_dias = defaultdict(list)

    for row in dias_por_obra:
        num = row['etapa__numero_etapa']
        nome = ETAPA_NOMES.get(num, f'Etapa {num}')
        etapa_dias[nome].append(row['dias'])

    resultado = []
    for nome, lista in sorted(etapa_dias.items()):
        media = sum(lista) / len(lista) if lista else 0
        resultado.append({
            'etapa_nome': nome,
            'media_dias': round(media, 1),
            'total_obras': len(lista),
        })

    return resultado


# ─────────────────────────────────────────────
# 3) Média de rendimento individual (pedreiro)
# ─────────────────────────────────────────────

def media_rendimento_individual(filtros: dict | None = None):
    """
    Média de metragem executada por dia de cada pedreiro.
    Ignora registros com metragem_executada = 0.
    """
    qs = _base_qs(filtros).filter(metragem_executada__gt=0)

    resultado = (
        qs
        .values('funcionario_id', 'funcionario__nome_completo')
        .annotate(
            media_metragem=Avg('metragem_executada'),
            total_dias=Count('id'),
            total_ociosidade=Count('id', filter=Q(houve_ociosidade=True)),
            total_retrabalho=Count('id', filter=Q(houve_retrabalho=True)),
        )
        .order_by('-media_metragem')
    )

    return [
        {
            'funcionario_id': r['funcionario_id'],
            'nome': r['funcionario__nome_completo'],
            'media_metragem': round(float(r['media_metragem']), 2),
            'total_dias': r['total_dias'],
            'total_ociosidade': r['total_ociosidade'],
            'total_retrabalho': r['total_retrabalho'],
        }
        for r in resultado
    ]


# ─────────────────────────────────────────────
# Função utilitária: gera todos os dados de uma vez
# ─────────────────────────────────────────────

def gerar_relatorio_completo(filtros: dict | None = None):
    """Retorna dict com todas as análises."""
    return {
        'ranking_etapa': ranking_por_etapa(filtros),
        'media_dias_etapa': media_dias_por_etapa(filtros),
        'media_individual': media_rendimento_individual(filtros),
    }


def apontamentos_periodo(filtros: dict | None = None, limite: int = 300):
    """Lista apontamentos detalhados do período com textos digitados."""
    qs = ApontamentoFuncionario.objects.select_related('funcionario', 'obra', 'etapa')

    if filtros:
        if filtros.get('obra_id'):
            qs = qs.filter(obra_id=filtros['obra_id'])
        if filtros.get('etapa_id'):
            qs = qs.filter(etapa_id=filtros['etapa_id'])
        if filtros.get('funcionario_id'):
            qs = qs.filter(funcionario_id=filtros['funcionario_id'])
        if filtros.get('data_inicio'):
            qs = qs.filter(data__gte=filtros['data_inicio'])
        if filtros.get('data_fim'):
            qs = qs.filter(data__lte=filtros['data_fim'])
        if filtros.get('clima'):
            qs = qs.filter(clima=filtros['clima'])

    return qs.order_by('-data', '-id')[:limite]
