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


def gerar_fechamentos_semanais(quantidade):
    """Cria N fechamentos semanais com dados aleatórios."""
    criados = 0
    erros = 0
    
    # Busca funcionários ativos
    funcionarios = list(Funcionario.objects.filter(ativo=True))
    
    if not funcionarios:
        print("⚠️  Nenhum funcionário ativo encontrado. Criar funcionários primeiro.")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"📅 Gerando {quantidade} fechamentos semanais...")
    print(f"{'='*60}\n")
    
    for i in range(quantidade):
        try:
            funcionario = random.choice(funcionarios)
            
            # Data aleatória nos últimos 12 semanas
            data_aleatoria = datetime.now().date() - timedelta(weeks=random.randint(0, 12))
            segunda = obter_segunda_semana(data_aleatoria)
            domingo = obter_domingo_semana(data_aleatoria)
            
            # Verifica se já existe fechamento para essa combinação
            if FechamentoSemanal.objects.filter(
                funcionario=funcionario,
                data_inicio=segunda,
                data_fim=domingo
            ).exists():
                print(f"  ⚠️  [{i+1}/{quantidade}] Fechamento já existe para {funcionario.nome_completo} ({segunda} a {domingo}). Pulando...")
                erros += 1
                continue
            
            # Status aleatório
            status = random.choice(['fechado', 'pago'])
            data_pagamento = domingo + timedelta(days=random.randint(1, 7)) if status == 'pago' else None
            
            # Cria fechamento (sem totais, será calculado depois)
            fechamento = FechamentoSemanal.objects.create(
                funcionario=funcionario,
                data_inicio=segunda,
                data_fim=domingo,
                status=status,
                data_pagamento=data_pagamento,
            )
            
            # Calcula totais baseado em apontamentos existentes da semana
            # Se não houver apontamentos, fica com 0
            fechamento.calcular_totais()
            
            criados += 1
            print(f"  ✅ [{i+1}/{quantidade}] {fechamento.funcionario.nome_completo} - {fechamento.data_inicio} a {fechamento.data_fim} (R$ {fechamento.total_valor})")
            
        except Exception as e:
            erros += 1
            print(f"  ❌ [{i+1}/{quantidade}] Erro ao criar fechamento: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Resultado: {criados} criados, {erros} erros")
    print(f"{'='*60}\n")


def main():
    try:
        quantidade = input("Quantos fechamentos semanais deseja criar? ").strip()
        
        if not quantidade.isdigit():
            print("❌ Favor informar um número inteiro válido.")
            sys.exit(1)
        
        quantidade = int(quantidade)
        if quantidade <= 0:
            print("❌ A quantidade deve ser maior que 0.")
            sys.exit(1)
        
        print("\n⚠️  Dica: Execute 'gerar_apontamento_diario.py' antes para ter dados para os fechamentos.")
        gerar_fechamentos_semanais(quantidade)
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Operação cancelada pelo usuário.")
        sys.exit(0)


if __name__ == '__main__':
    main()
