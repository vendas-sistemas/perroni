"""
Análises baseadas em RegistroProducao - Rankings por indicador específico.
Este módulo substitui/complementa o analytics.py oferecendo detalhamento por indicador.
"""

from collections import defaultdict
from decimal import Decimal

from django.db.models import Avg, Count, Sum, Q, Max, Min, Value, DecimalField
from django.db.models.functions import Coalesce

from apps.funcionarios.models import RegistroProducao, Funcionario, ApontamentoFuncionario


# Mapeamento de indicadores para etapas
INDICADORES_POR_ETAPA = {
    1: [  # Fundação
        {
            'indicador': 'alicerce_percentual',
            'nome': 'Levantar Alicerce (%)',
            'unidade': '%',
            'tipo': 'percentual'
        },
        {
            'indicador': 'parede_7fiadas',
            'nome': 'Parede até 7 Fiadas',
            'unidade': 'blocos',
            'tipo': 'quantitativo'
        },
    ],
    2: [  # Estrutura
        {
            'indicador': 'respaldo_conclusao',
            'nome': 'Respaldo - Conclusão',
            'unidade': '%',
            'tipo': 'percentual'
        },
        {
            'indicador': 'laje_conclusao',
            'nome': 'Laje - Conclusão',
            'unidade': '%',
            'tipo': 'percentual'
        },
        {
            'indicador': 'platibanda',
            'nome': 'Platibanda',
            'unidade': 'blocos',
            'tipo': 'quantitativo'
        },
        {
            'indicador': 'cobertura_conclusao',
            'nome': 'Cobertura - Conclusão',
            'unidade': '%',
            'tipo': 'percentual'
        },
    ],
    3: [  # Revestimentos e Instalações
        {
            'indicador': 'reboco_externo',
            'nome': 'Reboco Externo',
            'unidade': 'm²',
            'tipo': 'quantitativo'
        },
        {
            'indicador': 'reboco_interno',
            'nome': 'Reboco Interno',
            'unidade': 'm²',
            'tipo': 'quantitativo'
        },
    ],
}

ETAPA_NOMES = {
    1: 'Etapa 1 — Fundação',
    2: 'Etapa 2 — Estrutura',
    3: 'Etapa 3 — Revestimentos e Instalações',
    4: 'Etapa 4 — Acabamentos',
    5: 'Etapa 5 — Finalização',
}

# Mapeamento de indicadores para unidades
UNIDADES_INDICADORES = {
    'alicerce_percentual': '%',
    'parede_7fiadas': 'blocos',
    'respaldo_conclusao': '%',
    'laje_conclusao': '%',
    'platibanda': 'blocos',
    'cobertura_conclusao': '%',
    'reboco_externo': 'm²',
    'reboco_interno': 'm²',
}


def _base_qs(filtros: dict | None = None):
    """Retorna queryset base de RegistroProducao com filtros opcionais."""
    qs = (
        RegistroProducao.objects
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

    return qs


def ranking_por_indicador(indicador, filtros=None, top=3, bottom=3):
    """
    Retorna ranking dos melhores e piores pedreiros para um indicador específico.
    Calcula: média de quantidade produzida por dia trabalhado.
    
    CORREÇÃO CRÍTICA: Calcula média corretamente em Python!
    
    Args:
        indicador: string do indicador (ex: 'alicerce_percentual', 'parede_7fiadas')
        filtros: dict com filtros opcionais
        top: quantidade de melhores
        bottom: quantidade de piores
    
    Returns:
        dict com 'melhores' e 'piores', cada um com lista de pedreiros ordenados
    """
    qs = _base_qs(filtros).filter(
        indicador=indicador,
        quantidade__gt=0  # Ignora registros zerados
    )
    
    # Agrupar por funcionário (SEM calcular média no Django)
    stats = (
        qs
        .values('funcionario_id', 'funcionario__nome_completo')
        .annotate(
            total_valor=Sum('quantidade'),
            total_dias=Count('data', distinct=True),
        )
        .order_by()
    )
    
    # ===== CALCULAR MÉDIA CORRETAMENTE EM PYTHON =====
    resultado_lista = []
    for row in stats:
        total_valor = float(row['total_valor'] or 0)
        total_dias = int(row['total_dias'] or 0)
        
        # Calcular média: Total ÷ Dias
        if total_dias > 0:
            media_producao = total_valor / total_dias
        else:
            media_producao = 0
        
        resultado_lista.append({
            'funcionario_id': row['funcionario_id'],
            'nome': row['funcionario__nome_completo'],
            'media_producao': round(media_producao, 2),  # ← MÉDIA CORRETA!
            'total_dias': total_dias,
        })
    
    # Ordenar por média (maior primeiro)
    resultado_lista = sorted(resultado_lista, key=lambda x: x['media_producao'], reverse=True)
    
    # Obter nome e unidade do indicador
    nome_indicador = dict(RegistroProducao.INDICADOR_CHOICES).get(indicador, indicador)
    unidade = UNIDADES_INDICADORES.get(indicador, '')
    
    return {
        'indicador': indicador,
        'nome': nome_indicador,
        'unidade': unidade,
        'ranking': resultado_lista,  # Lista completa ordenada
        'melhores': resultado_lista[:top],
        'piores': resultado_lista[-bottom:] if len(resultado_lista) > top else resultado_lista[::-1][:bottom],
    }


def ranking_geral_por_etapas(filtros=None, top=3, bottom=3):
    """
    Retorna rankings de TODOS os indicadores organizados por etapa.
    
    Returns:
        Lista de etapas, cada uma com seus indicadores e seus rankings
    """
    resultado = []
    
    for num_etapa, indicadores_info in sorted(INDICADORES_POR_ETAPA.items()):
        etapa_data = {
            'numero': num_etapa,
            'nome': ETAPA_NOMES.get(num_etapa, f'Etapa {num_etapa}'),
            'indicadores': []
        }
        
        for info_indicador in indicadores_info:
            indicador_codigo = info_indicador['indicador']
            ranking = ranking_por_indicador(indicador_codigo, filtros, top, bottom)
            
            # Só adiciona se tiver dados
            if ranking['melhores'] or ranking['piores']:
                etapa_data['indicadores'].append({
                    'codigo': indicador_codigo,
                    'nome': info_indicador['nome'],
                    'unidade': info_indicador['unidade'],
                    'tipo': info_indicador['tipo'],
                    'melhores': ranking['melhores'],
                    'piores': ranking['piores'],
                })
        
        # Só adiciona etapa se tiver dados
        if etapa_data['indicadores']:
            resultado.append(etapa_data)
    
    return resultado


def media_rendimento_por_pedreiro(filtros=None):
    """
    Retorna média geral de rendimento de cada pedreiro considerando TODOS os indicadores.
    Mostra também dias trabalhados, dias com ociosidade, dias com retrabalho.
    
    CORREÇÃO CRÍTICA: Calcula média corretamente em Python!
    """
    # Buscar dados de RegistroProducao
    qs_producao = _base_qs(filtros).filter(quantidade__gt=0)
    
    # Agregar por funcionário (SEM calcular média no Django)
    stats_producao = (
        qs_producao
        .values('funcionario_id', 'funcionario__nome_completo')
        .annotate(
            # Soma total de produção (de todos os indicadores)
            total_producao=Sum('quantidade'),
            # Dias únicos trabalhados
            total_dias=Count('data', distinct=True),
        )
        .order_by()
    )
    
    # Buscar dados de ociosidade/retrabalho do ApontamentoFuncionario
    qs_apontamentos = (
        ApontamentoFuncionario.objects
        .filter(funcionario__funcao='pedreiro')
    )
    
    if filtros:
        if filtros.get('obra_id'):
            qs_apontamentos = qs_apontamentos.filter(obra_id=filtros['obra_id'])
        if filtros.get('funcionario_id'):
            qs_apontamentos = qs_apontamentos.filter(funcionario_id=filtros['funcionario_id'])
        if filtros.get('data_inicio'):
            qs_apontamentos = qs_apontamentos.filter(data__gte=filtros['data_inicio'])
        if filtros.get('data_fim'):
            qs_apontamentos = qs_apontamentos.filter(data__lte=filtros['data_fim'])
    
    stats_apontamentos = (
        qs_apontamentos
        .values('funcionario_id')
        .annotate(
            total_ociosidade=Count('id', filter=Q(houve_ociosidade=True)),
            total_retrabalho=Count('id', filter=Q(houve_retrabalho=True)),
            total_horas=Coalesce(Sum('horas_trabalhadas'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2)),
            total_valor=Coalesce(Sum('valor_diaria'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2)),
            total_metragem=Coalesce(Sum('metragem_executada'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2)),
        )
    )
    
    # Combinar dados
    apontamentos_dict = {
        r['funcionario_id']: r for r in stats_apontamentos
    }

    # Agregar produção por (funcionario_id, indicador) para médias por indicador
    INDICADORES_COLS = [
        'parede_7fiadas',
        'alicerce_percentual',
        'platibanda',
        'reboco_externo',
        'reboco_interno',
    ]
    por_indicador_qs = (
        qs_producao
        .filter(indicador__in=INDICADORES_COLS)
        .values('funcionario_id', 'indicador')
        .annotate(
            total_ind=Sum('quantidade'),
            dias_ind=Count('data', distinct=True),
        )
    )
    # Montar dicionário {func_id: {indicador: media}}
    indicador_dict = defaultdict(dict)
    for row_ind in por_indicador_qs:
        fid = row_ind['funcionario_id']
        ind = row_ind['indicador']
        total_i = float(row_ind['total_ind'] or 0)
        dias_i = int(row_ind['dias_ind'] or 0)
        indicador_dict[fid][ind] = round(total_i / dias_i, 2) if dias_i > 0 else 0

    resultado = []
    for row in stats_producao:
        func_id = row['funcionario_id']
        apt = apontamentos_dict.get(func_id, {})
        ind_data = indicador_dict.get(func_id, {})

        # ===== CALCULAR MÉDIA CORRETAMENTE EM PYTHON =====
        total_producao = float(row['total_producao'] or 0)
        total_dias = int(row['total_dias'] or 0)

        if total_dias > 0:
            media_producao = total_producao / total_dias
        else:
            media_producao = 0

        resultado.append({
            'funcionario_id': func_id,
            'nome': row['funcionario__nome_completo'],
            'media_producao': round(media_producao, 2),
            'total_dias': total_dias,
            'total_ociosidade': apt.get('total_ociosidade', 0),
            'total_retrabalho': apt.get('total_retrabalho', 0),
            'total_horas': float(apt.get('total_horas', 0) or 0),
            'total_valor': float(apt.get('total_valor', 0) or 0),
            'total_metragem': float(apt.get('total_metragem', 0) or 0),
            # Médias por indicador específico
            'media_7fiadas': ind_data.get('parede_7fiadas', '-'),
            'media_alicerce': ind_data.get('alicerce_percentual', '-'),
            'media_platibanda': ind_data.get('platibanda', '-'),
            'media_reboco_ext': ind_data.get('reboco_externo', '-'),
            'media_reboco_int': ind_data.get('reboco_interno', '-'),
        })

    # Ordenar por média de produção
    resultado.sort(key=lambda x: x['media_producao'], reverse=True)

    return resultado


def detalhamento_pedreiro(funcionario_id, filtros=None):
    """
    Retorna detalhamento completo de um pedreiro específico.
    Mostra performance em cada indicador + resumo geral.
    
    CORREÇÃO CRÍTICA: Calcula média corretamente em Python!
    """
    try:
        funcionario = Funcionario.objects.get(id=funcionario_id, funcao='pedreiro')
    except Funcionario.DoesNotExist:
        return None
    
    # Adicionar filtro de funcionário
    filtros_pedreiro = filtros.copy() if filtros else {}
    filtros_pedreiro['funcionario_id'] = funcionario_id
    
    # Buscar dados por indicador
    qs = _base_qs(filtros_pedreiro).filter(quantidade__gt=0)
    
    # Agrupar por indicador (SEM calcular média no Django)
    stats_por_indicador = (
        qs
        .values('indicador')
        .annotate(
            total_producao=Sum('quantidade'),
            total_dias=Count('data', distinct=True),
            primeira_data=Min('data'),
            ultima_data=Max('data'),
        )
    )
    
    indicadores_detalhados = []
    for row in stats_por_indicador:
        indicador_codigo = row['indicador']
        indicador_nome = dict(RegistroProducao.INDICADOR_CHOICES).get(
            indicador_codigo, 
            indicador_codigo
        )
        
        # ===== CALCULAR MÉDIA CORRETAMENTE EM PYTHON =====
        total_producao = float(row['total_producao'] or 0)
        total_dias = int(row['total_dias'] or 0)
        
        if total_dias > 0:
            media_producao = total_producao / total_dias
        else:
            media_producao = 0
        
        indicadores_detalhados.append({
            'codigo': indicador_codigo,
            'nome': indicador_nome,
            'media_producao': round(media_producao, 2),  # ← MÉDIA CORRETA!
            'total_producao': round(total_producao, 2),
            'total_dias': total_dias,
            'primeira_data': row['primeira_data'],
            'ultima_data': row['ultima_data'],
        })
    
    # Buscar dados gerais de apontamentos
    qs_apt = ApontamentoFuncionario.objects.filter(funcionario_id=funcionario_id)
    
    if filtros:
        if filtros.get('obra_id'):
            qs_apt = qs_apt.filter(obra_id=filtros['obra_id'])
        if filtros.get('data_inicio'):
            qs_apt = qs_apt.filter(data__gte=filtros['data_inicio'])
        if filtros.get('data_fim'):
            qs_apt = qs_apt.filter(data__lte=filtros['data_fim'])
    
    resumo_geral = qs_apt.aggregate(
        total_dias=Count('id'),
        total_horas=Sum('horas_trabalhadas'),
        total_ociosidade=Count('id', filter=Q(houve_ociosidade=True)),
        total_retrabalho=Count('id', filter=Q(houve_retrabalho=True)),
        obras_distintas=Count('obra', distinct=True),
    )
    
    return {
        'funcionario': {
            'id': funcionario.id,
            'nome': funcionario.nome_completo,
            'funcao': funcionario.get_funcao_display(),
        },
        'resumo_geral': {
            'total_dias': resumo_geral['total_dias'] or 0,
            'total_horas': float(resumo_geral['total_horas'] or 0),
            'total_ociosidade': resumo_geral['total_ociosidade'] or 0,
            'total_retrabalho': resumo_geral['total_retrabalho'] or 0,
            'obras_distintas': resumo_geral['obras_distintas'] or 0,
        },
        'indicadores': indicadores_detalhados,
    }


def media_dias_por_etapa(filtros=None):
    """
    Calcula média de dias para execução de cada etapa.
    Usa dados de ApontamentoFuncionario (mantido do sistema original).
    Exclui etapas concluídas e obras concluídas do cálculo.
    """
    from apps.funcionarios.models import ApontamentoFuncionario
    
    qs = (
        ApontamentoFuncionario.objects
        .filter(
            funcionario__funcao='pedreiro',
            etapa__isnull=False,
            # Excluir etapas concluídas
            etapa__concluida=False,
            # Excluir obras concluídas
            obra__status__in=['planejamento', 'em_andamento'],
        )
        .select_related('funcionario', 'obra', 'etapa')
    )
    
    if filtros:
        if filtros.get('obra_id'):
            qs = qs.filter(obra_id=filtros['obra_id'])
        if filtros.get('etapa_id'):
            qs = qs.filter(etapa_id=filtros['etapa_id'])
        if filtros.get('data_inicio'):
            qs = qs.filter(data__gte=filtros['data_inicio'])
        if filtros.get('data_fim'):
            qs = qs.filter(data__lte=filtros['data_fim'])
    
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


def gerar_relatorio_completo_indicadores(filtros=None):
    """
    Retorna dict com TODAS as análises baseadas em indicadores.
    Substitui o gerar_relatorio_completo() do analytics.py
    """
    # Lista dos 8 indicadores principais
    indicadores = [
        'alicerce_percentual',
        'parede_7fiadas',
        'respaldo_conclusao',
        'laje_conclusao',
        'platibanda',
        'cobertura_conclusao',
        'reboco_externo',
        'reboco_interno',
    ]
    
    # Gerar ranking para cada indicador
    rankings_indicadores = {}
    for indicador in indicadores:
        ranking = ranking_por_indicador(indicador, filtros, top=10, bottom=0)
        if ranking:  # Só incluir se houver dados
            rankings_indicadores[indicador] = ranking
    
    return {
        'ranking_por_etapas': ranking_geral_por_etapas(filtros, top=3, bottom=3),
        'media_dias_etapa': media_dias_por_etapa(filtros),
        'media_individual': media_rendimento_por_pedreiro(filtros),
        'rankings_indicadores': rankings_indicadores,  # NOVO: rankings separados por indicador
    }
