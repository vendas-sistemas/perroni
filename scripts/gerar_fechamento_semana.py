#!/usr/bin/env python
"""
Script para gerar fechamentos semanais de funcionários.
Uso: python gerar_fechamento_semana.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal
import argparse
import logging
from django.db import transaction

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import Funcionario, FechamentoSemanal, ApontamentoFuncionario


def obter_segunda_semana(data):
    """Retorna a segunda-feira da semana da data fornecida."""
    dias_atras = data.weekday()  # 0 = segunda, 6 = domingo
    return data - timedelta(days=dias_atras)


def obter_domingo_semana(data):
    """Retorna o domingo da semana da data fornecida."""
    segunda = obter_segunda_semana(data)
    return segunda + timedelta(days=6)


def gerar_fechamentos_semanais(quantidade, recalc=False):
    """Cria N fechamentos semanais com dados aleatórios.

    If `recalc` is True, existing fechamentos for the same period will be
    recalculated instead of skipped.
    """
    criados = 0
    erros = 0

    # Busca funcionários ativos
    funcionarios = list(Funcionario.objects.filter(ativo=True))

    if not funcionarios:
        logging.warning("Nenhum funcionário ativo encontrado. Criar funcionários primeiro.")
        sys.exit(1)

    logging.info("Gerando %d fechamentos semanais...", quantidade)

    for i in range(quantidade):
        try:
            funcionario = random.choice(funcionarios)

            # Data aleatória nos últimos 12 semanas
            data_aleatoria = datetime.now().date() - timedelta(weeks=random.randint(0, 12))
            segunda = obter_segunda_semana(data_aleatoria)
            domingo = obter_domingo_semana(data_aleatoria)

            # Use transaction for safety
            with transaction.atomic():
                existing = FechamentoSemanal.objects.filter(
                    funcionario=funcionario,
                    data_inicio=segunda,
                    data_fim=domingo
                ).first()

                if existing and not recalc:
                    logging.info("[%d/%d] Fechamento já existe para %s (%s a %s). Pulando...", i+1, quantidade, funcionario.nome_completo, segunda, domingo)
                    erros += 1
                    continue

                if existing and recalc:
                    fechamento = existing
                    logging.info("[%d/%d] Recalculando fechamento para %s (%s a %s)", i+1, quantidade, funcionario.nome_completo, segunda, domingo)
                else:
                    status = random.choice(['fechado', 'pago'])
                    data_pagamento = domingo + timedelta(days=random.randint(1, 7)) if status == 'pago' else None
                    fechamento = FechamentoSemanal.objects.create(
                        funcionario=funcionario,
                        data_inicio=segunda,
                        data_fim=domingo,
                        status=status,
                        data_pagamento=data_pagamento,
                    )

                # Recalculate totals using model method (which now pays one diária per day)
                fechamento.calcular_totais()

                criados += 0 if existing and not recalc else 1
                logging.info("  ✅ [%d/%d] %s - %s a %s (R$ %s)", i+1, quantidade, fechamento.funcionario.nome_completo, fechamento.data_inicio, fechamento.data_fim, fechamento.total_valor)

        except Exception as e:
            erros += 1
            logging.exception("[%d/%d] Erro ao criar/atualizar fechamento: %s", i+1, quantidade, e)

    logging.info("Resultado: %d criados/atualizados, %d erros", criados, erros)


def main():
    try:
        parser = argparse.ArgumentParser(description='Gerar fechamentos semanais (scripts utilitário)')
        parser.add_argument('quantidade', type=int, help='Quantos fechamentos gerar')
        parser.add_argument('--recalc', action='store_true', help='Recalcular fechamentos existentes em vez de pular')
        args = parser.parse_args()

        if args.quantidade <= 0:
            print('❌ A quantidade deve ser maior que 0.')
            sys.exit(1)

        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
        logging.info("Dica: Execute 'gerar_apontamento_diario.py' antes para ter dados para os fechamentos.")
        gerar_fechamentos_semanais(args.quantidade, recalc=args.recalc)
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Operação cancelada pelo usuário.")
        sys.exit(0)


if __name__ == '__main__':
    main()
