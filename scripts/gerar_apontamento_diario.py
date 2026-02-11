"""
Script para gerar 100 apontamentos diários automáticos para testes.
Distribui apontamentos em diversas obras e funcionários,
com datas variadas nos últimos 30 dias.

Uso:
    python manage.py shell < scripts/gerar_apontamento_diario.py
    ou
    cd .. && python -c "import django; import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); django.setup(); exec(open('scripts/gerar_apontamento_diario.py').read())"
"""

import os
import sys
import random
from datetime import date, timedelta
from decimal import Decimal

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Adiciona o diretório raiz do projeto ao path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import django
django.setup()

from apps.funcionarios.models import Funcionario, ApontamentoFuncionario
from apps.obras.models import Obra, Etapa


# ============================================================
# Configurações
# ============================================================
TOTAL_APONTAMENTOS = 100
DIAS_PASSADOS = 30  # gerar datas nos últimos 30 dias

MOTIVOS_OCIOSIDADE = [
    'Aguardando material de construção',
    'Chuva forte impossibilitou trabalho externo',
    'Falta de energia elétrica no canteiro',
    'Equipamento quebrou, aguardando manutenção',
    'Aguardando liberação de engenharia',
    'Falta de água no canteiro',
    'Atraso na entrega de concreto',
]

MOTIVOS_RETRABALHO = [
    'Parede desalinhada, necessário refazer',
    'Erro na medição do piso',
    'Reboco com espessura incorreta',
    'Instalação hidráulica com vazamento',
    'Nível do contrapiso fora do padrão',
    'Fiação elétrica em bitola errada',
    'Acabamento de azulejo com defeito',
]

OBSERVACOES = [
    'Trabalho transcorreu normalmente.',
    'Funcionário demonstrou bom desempenho.',
    'Concluiu a atividade dentro do prazo.',
    'Necessário acompanhamento na próxima etapa.',
    'Bom andamento da obra hoje.',
    'Equipe trabalhou com eficiência.',
    'Material chegou no horário previsto.',
    'Houve atraso no início por conta do trânsito.',
    'Clima favorável, bom rendimento.',
    'Funcionário realizou hora extra.',
    '',  # sem observação
    '',
    '',
]

CLIMAS = ['sol', 'sol', 'sol', 'nublado', 'nublado', 'chuva']  # mais dias de sol

HORAS_POSSIVEIS = [
    Decimal('4.0'), Decimal('5.0'), Decimal('6.0'),
    Decimal('7.0'), Decimal('8.0'), Decimal('8.0'),
    Decimal('8.0'), Decimal('8.0'), Decimal('9.0'),
    Decimal('10.0'),
]


def gerar_apontamentos():
    """Gera 100 apontamentos diários distribuídos em obras e funcionários."""

    funcionarios = list(Funcionario.objects.filter(ativo=True))
    obras = list(Obra.objects.filter(ativo=True, status='em_andamento'))

    if not funcionarios:
        print('ERRO: Nenhum funcionário ativo encontrado. Execute generate_test_data_realistic.py primeiro.')
        return
    if not obras:
        # Tentar com qualquer obra ativa
        obras = list(Obra.objects.filter(ativo=True))
        if not obras:
            print('ERRO: Nenhuma obra ativa encontrada. Execute generate_test_data_realistic.py primeiro.')
            return
        print(f'Aviso: Nenhuma obra "em_andamento". Usando {len(obras)} obras ativas de qualquer status.')

    print(f'Funcionários disponíveis: {len(funcionarios)}')
    print(f'Obras disponíveis: {len(obras)}')

    # Pré-carregar etapas por obra
    etapas_por_obra = {}
    for obra in obras:
        etapas = list(Etapa.objects.filter(obra=obra))
        etapas_por_obra[obra.id] = etapas

    # Gerar datas úteis (seg-sáb) nos últimos N dias
    hoje = date.today()
    datas_uteis = []
    for i in range(DIAS_PASSADOS):
        d = hoje - timedelta(days=i)
        if d.weekday() < 6:  # 0=seg ... 5=sab (exclui domingo)
            datas_uteis.append(d)

    print(f'Datas úteis disponíveis: {len(datas_uteis)}')

    # Verificar apontamentos já existentes para evitar unique_together
    existentes = set(
        ApontamentoFuncionario.objects.values_list('funcionario_id', 'data')
    )
    print(f'Apontamentos já existentes: {len(existentes)}')

    criados = 0
    tentativas = 0
    max_tentativas = TOTAL_APONTAMENTOS * 5  # evitar loop infinito

    while criados < TOTAL_APONTAMENTOS and tentativas < max_tentativas:
        tentativas += 1

        # Escolher funcionário e data aleatórios
        func = random.choice(funcionarios)
        data_apt = random.choice(datas_uteis)

        # Verificar unique_together
        if (func.id, data_apt) in existentes:
            continue

        # Escolher obra e etapa
        obra = random.choice(obras)
        etapas = etapas_por_obra.get(obra.id, [])
        etapa = random.choice(etapas) if etapas else None

        # Definir dados do apontamento
        horas = random.choice(HORAS_POSSIVEIS)
        clima = random.choice(CLIMAS)

        # 15% de chance de ociosidade
        houve_ociosidade = random.random() < 0.15
        obs_ociosidade = random.choice(MOTIVOS_OCIOSIDADE) if houve_ociosidade else ''

        # Se choveu, reduzir horas e aumentar chance de ociosidade
        if clima == 'chuva':
            horas = min(horas, Decimal('6.0'))
            if random.random() < 0.4:
                houve_ociosidade = True
                obs_ociosidade = 'Chuva forte impossibilitou trabalho externo'

        # 10% de chance de retrabalho
        houve_retrabalho = random.random() < 0.10
        motivo_retrabalho = random.choice(MOTIVOS_RETRABALHO) if houve_retrabalho else ''

        observacoes = random.choice(OBSERVACOES)

        try:
            apontamento = ApontamentoFuncionario.objects.create(
                funcionario=func,
                obra=obra,
                etapa=etapa,
                data=data_apt,
                horas_trabalhadas=horas,
                clima=clima,
                houve_ociosidade=houve_ociosidade,
                observacao_ociosidade=obs_ociosidade if houve_ociosidade else None,
                houve_retrabalho=houve_retrabalho,
                motivo_retrabalho=motivo_retrabalho if houve_retrabalho else None,
                valor_diaria=func.valor_diaria,
                observacoes=observacoes if observacoes else None,
            )
            existentes.add((func.id, data_apt))
            criados += 1

            if criados % 20 == 0:
                print(f'  ... {criados}/{TOTAL_APONTAMENTOS} apontamentos criados')

        except Exception as e:
            print(f'  Erro ao criar apontamento: {e}')
            continue

    print(f'\n{"="*50}')
    print(f'RESULTADO:')
    print(f'  Apontamentos criados: {criados}')
    print(f'  Tentativas realizadas: {tentativas}')
    print(f'  Total de apontamentos no sistema: {ApontamentoFuncionario.objects.count()}')

    # Estatísticas
    if criados > 0:
        from django.db.models import Count, Avg, Q as DjangoQ
        stats = ApontamentoFuncionario.objects.aggregate(
            total=Count('id'),
            media_horas=Avg('horas_trabalhadas'),
            total_ociosidade=Count('id', filter=DjangoQ(houve_ociosidade=True)),
            total_retrabalho=Count('id', filter=DjangoQ(houve_retrabalho=True)),
        )

        obras_usadas = ApontamentoFuncionario.objects.values('obra').distinct().count()
        funcs_usados = ApontamentoFuncionario.objects.values('funcionario').distinct().count()
        datas_usadas = ApontamentoFuncionario.objects.values('data').distinct().count()

        print(f'\nESTATÍSTICAS:')
        print(f'  Obras envolvidas: {obras_usadas}')
        print(f'  Funcionários envolvidos: {funcs_usados}')
        print(f'  Datas distintas: {datas_usadas}')
        print(f'  Média de horas: {stats["media_horas"]:.1f}h')
        print(f'  Com ociosidade: {stats["total_ociosidade"]}')
        print(f'  Com retrabalho: {stats["total_retrabalho"]}')

    print(f'{"="*50}')


if __name__ == '__main__':
    gerar_apontamentos()
else:
    # Quando executado via shell < script
    gerar_apontamentos()
