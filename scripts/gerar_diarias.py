#!/usr/bin/env python
"""
Script para gerar apontamentos diários em um período customizável.
Uso: python gerar_diarias.py
Permite informar quantos meses/dias no passado gerar dados.
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import Funcionario, ApontamentoFuncionario
from apps.obras.models import Obra


CLIMAS = ['sol', 'chuva', 'nublado']
OBSERVACOES_OCIOSIDADE = [
    'Falta de material',
    'Espera por inspeção',
    'Problemas de segurança',
    'Chuva forte',
    'Falta de energia',
]
OBSERVACOES_RETRABALHO = [
    'Erro na execução anterior',
    'Mudança de especificação',
    'Corrosão ou dano',
    'Revisão de qualidade',
    'Problemas estruturais',
]


def gerar_diarias_periodo(quantidade, meses_atras):
    """Cria N apontamentos diários em um período específico."""
    criados = 0
    erros = 0
    
    # Busca dados necessários
    funcionarios = list(Funcionario.objects.filter(ativo=True))
    obras = list(Obra.objects.filter(ativo=True))
    
    if not funcionarios:
        print("⚠️  Nenhum funcionário ativo encontrado. Criar funcionários primeiro com 'gerar_funcionarios.py'")
        sys.exit(1)
    
    if not obras:
        print("⚠️  Nenhuma obra ativa encontrada. Criar obras primeiro com 'gerar_obras.py'")
        sys.exit(1)
    
    hoje = datetime.now().date()
    data_inicio_periodo = hoje - timedelta(days=meses_atras*30)  # aproximadamente meses
    
    print(f"\n{'='*60}")
    print(f"📋 Gerando {quantidade} apontamentos diários")
    print(f"   Período: {data_inicio_periodo} até {hoje}")
    print(f"{'='*60}\n")
    
    for i in range(quantidade):
        try:
            funcionario = random.choice(funcionarios)
            obra = random.choice(obras)
            
            # Data aleatória dentro do período
            dias_disponiveis = (hoje - data_inicio_periodo).days
            data = data_inicio_periodo + timedelta(days=random.randint(0, dias_disponiveis))
            
            # Tenta usar uma etapa da obra se houver
            etapa = None
            etapas = list(obra.etapas.all())
            if etapas:
                etapa = random.choice(etapas) if random.choice([True, False]) else None
            
            # Horas trabalhadas variadas
            horas = Decimal(str(random.choice([4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])))
            
            # Clima
            clima = random.choice(CLIMAS)
            
            # Ociosidade e retrabalho (com 25% de chance cada)
            houve_ociosidade = random.choice([True, False, False, False])
            obs_ociosidade = random.choice(OBSERVACOES_OCIOSIDADE) if houve_ociosidade else None
            
            houve_retrabalho = random.choice([True, False, False, False])
            motivo_retrabalho = random.choice(OBSERVACOES_RETRABALHO) if houve_retrabalho else None
            
            # Metragem executada variável
            if houve_ociosidade:
                metragem = Decimal(str(random.uniform(0.0, 10.0)))
            else:
                metragem = Decimal(str(random.uniform(5.0, 60.0)))
            metragem = metragem.quantize(Decimal('0.01'))
            
            # Valor da diária
            valor_diaria = funcionario.valor_diaria
            
            apontamento = ApontamentoFuncionario.objects.create(
                funcionario=funcionario,
                obra=obra,
                etapa=etapa,
                data=data,
                horas_trabalhadas=horas,
                clima=clima,
                houve_ociosidade=houve_ociosidade,
                observacao_ociosidade=obs_ociosidade,
                houve_retrabalho=houve_retrabalho,
                motivo_retrabalho=motivo_retrabalho,
                metragem_executada=metragem,
                valor_diaria=valor_diaria,
            )
            
            criados += 1
            if (i + 1) % 10 == 0:
                print(f"  ✅ [{i+1}/{quantidade}] {apontamento.funcionario.nome_completo} - {apontamento.obra.nome} ({apontamento.data})")
            
        except Exception as e:
            erros += 1
            print(f"  ❌ [{i+1}/{quantidade}] Erro ao criar apontamento: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Resultado: {criados} criados, {erros} erros")
    print(f"   Período coberto: {data_inicio_periodo} até {hoje}")
    print(f"{'='*60}\n")


def main():
    try:
        print("\n" + "="*60)
        print("📅 GERADOR DE APONTAMENTOS DIÁRIOS COM PERÍODO")
        print("="*60)
        
        quantidade = input("\nQuantos apontamentos diários deseja criar? ").strip()
        
        if not quantidade.isdigit():
            print("❌ Favor informar um número inteiro válido.")
            sys.exit(1)
        
        quantidade = int(quantidade)
        if quantidade <= 0:
            print("❌ A quantidade deve ser maior que 0.")
            sys.exit(1)
        
        print("\n📆 Opções de período:")
        print("  1 - Último mês (30 dias)")
        print("  2 - Últimos 3 meses (90 dias)")
        print("  3 - Últimos 6 meses (180 dias)")
        print("  4 - Último ano (365 dias)")
        print("  5 - Período customizado (informar dias)")
        
        opcao = input("\nEscolha uma opção (1-5): ").strip()
        
        meses_mapa = {
            '1': 1,      # 1 mês
            '2': 3,      # 3 meses
            '3': 6,      # 6 meses
            '4': 12,     # 12 meses
        }
        
        if opcao in meses_mapa:
            meses_atras = meses_mapa[opcao]
        elif opcao == '5':
            dias_customizado = input("Quantos dias no passado? ").strip()
            if not dias_customizado.isdigit():
                print("❌ Favor informar um número inteiro válido.")
                sys.exit(1)
            meses_atras = int(dias_customizado) // 30
        else:
            print("❌ Opção inválida.")
            sys.exit(1)
        
        gerar_diarias_periodo(quantidade, meses_atras)
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Operação cancelada pelo usuário.")
        sys.exit(0)


if __name__ == '__main__':
    main()
