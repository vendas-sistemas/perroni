"""
Script para gerar fechamentos semanais automáticos a partir dos
apontamentos diários existentes no sistema.

Agrupa apontamentos por funcionário e semana (segunda a sábado),
cria os FechamentoSemanal e calcula os totais via calcular_totais().

Uso:
    python scripts/gerar_fechamento_semanais.py
"""

import os
import sys
import random
from datetime import date, timedelta
from decimal import Decimal
from collections import defaultdict

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import django
django.setup()

from apps.funcionarios.models import Funcionario, ApontamentoFuncionario, FechamentoSemanal


# ============================================================
# Configurações
# ============================================================
OBSERVACOES_FECHAMENTO = [
    'Semana produtiva, sem intercorrências.',
    'Funcionário cumpriu todas as atividades previstas.',
    'Houve atraso por conta de material.',
    'Desempenho satisfatório.',
    'Necessário acompanhamento na próxima semana.',
    'Bom rendimento geral.',
    '',
    '',
    '',
]


def get_semana(data_ref):
    """
    Retorna (data_inicio, data_fim) da semana de trabalho.
    Semana: segunda (0) a sábado (5).
    """
    # weekday(): 0=seg, 1=ter, ..., 5=sab, 6=dom
    dia_semana = data_ref.weekday()
    if dia_semana == 6:  # domingo -> pertence à semana seguinte (segunda)
        inicio = data_ref + timedelta(days=1)
    else:
        inicio = data_ref - timedelta(days=dia_semana)
    fim = inicio + timedelta(days=5)  # sábado
    return inicio, fim


def gerar_fechamentos():
    """Gera fechamentos semanais a partir dos apontamentos existentes."""

    # Buscar todos os apontamentos
    apontamentos = ApontamentoFuncionario.objects.all().select_related('funcionario')
    total_apontamentos = apontamentos.count()

    if total_apontamentos == 0:
        print('ERRO: Nenhum apontamento encontrado. Execute gerar_apontamento_diario.py primeiro.')
        return

    print(f'Total de apontamentos no sistema: {total_apontamentos}')

    # Agrupar apontamentos por (funcionario_id, semana_inicio, semana_fim)
    semanas_funcionario = defaultdict(list)
    for apt in apontamentos:
        inicio, fim = get_semana(apt.data)
        chave = (apt.funcionario_id, inicio, fim)
        semanas_funcionario[chave].append(apt)

    print(f'Combinações funcionário/semana encontradas: {len(semanas_funcionario)}')

    # Buscar fechamentos já existentes
    existentes = set(
        FechamentoSemanal.objects.values_list('funcionario_id', 'data_inicio', 'data_fim')
    )
    print(f'Fechamentos já existentes: {len(existentes)}')

    criados = 0
    ignorados = 0
    status_opcoes = ['fechado', 'pago']
    status_pesos = [0.40, 0.60]  # 40% fechado, 60% pago

    for (func_id, data_inicio, data_fim), apts in semanas_funcionario.items():
        # Pular se já existe
        if (func_id, data_inicio, data_fim) in existentes:
            ignorados += 1
            continue

        # Determinar status com base na data
        hoje = date.today()
        if data_fim >= hoje:
            # Semana atual ou futura -> fechado
            status = 'fechado'
            data_pagamento = None
        else:
            # Semanas passadas -> sortear entre fechado e pago
            status = random.choices(status_opcoes, weights=status_pesos)[0]
            if status == 'pago':
                # Pagamento entre 1-5 dias após fim da semana
                data_pagamento = data_fim + timedelta(days=random.randint(1, 5))
            else:
                data_pagamento = None

        observacoes = random.choice(OBSERVACOES_FECHAMENTO)

        try:
            fechamento = FechamentoSemanal.objects.create(
                funcionario_id=func_id,
                data_inicio=data_inicio,
                data_fim=data_fim,
                status=status,
                data_pagamento=data_pagamento,
                observacoes=observacoes if observacoes else None,
            )
            # Calcular totais automaticamente a partir dos apontamentos
            fechamento.calcular_totais()
            criados += 1

            if criados % 20 == 0:
                print(f'  ... {criados} fechamentos criados')

        except Exception as e:
            print(f'  Erro ao criar fechamento (func={func_id}, {data_inicio}-{data_fim}): {e}')
            continue

    # ============================================================
    # Relatório
    # ============================================================
    print(f'\n{"="*55}')
    print(f'RESULTADO:')
    print(f'  Fechamentos criados: {criados}')
    print(f'  Já existentes (ignorados): {ignorados}')
    print(f'  Total de fechamentos no sistema: {FechamentoSemanal.objects.count()}')

    if criados > 0:
        from django.db.models import Sum, Avg, Count, Q

        stats = FechamentoSemanal.objects.aggregate(
            total=Count('id'),
            total_valor=Sum('total_valor'),
            media_horas=Avg('total_horas'),
            total_dias=Sum('total_dias'),
            abertos=Count('id', filter=Q(status='fechado')),
            fechados=Count('id', filter=Q(status='fechado')),
            pagos=Count('id', filter=Q(status='pago')),
        )

        funcs_envolvidos = FechamentoSemanal.objects.values('funcionario').distinct().count()
        semanas_distintas = FechamentoSemanal.objects.values('data_inicio').distinct().count()

        print(f'\nESTATÍSTICAS:')
        print(f'  Funcionários com fechamento: {funcs_envolvidos}')
        print(f'  Semanas distintas: {semanas_distintas}')
        print(f'  Total de dias apontados: {stats["total_dias"]}')
        print(f'  Média de horas/semana: {stats["media_horas"]:.1f}h')
        print(f'  Valor total a pagar: R$ {stats["total_valor"]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
        print(f'\n  Status:')
        print(f'    Fechados: {stats["fechados"]}')
        print(f'    Pagos:    {stats["pagos"]}')

    print(f'{"="*55}')


if __name__ == '__main__':
    gerar_fechamentos()
else:
    gerar_fechamentos()
