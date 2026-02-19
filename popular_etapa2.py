#!/usr/bin/env python
"""Script para popular dados da Etapa 2"""
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao, Funcionario
from apps.obras.models import Obra, Etapa

print("=" * 70)
print("CRIANDO DADOS DE TESTE PARA ETAPA 2")
print("=" * 70)

# Buscar pedreiros
pedreiros = Funcionario.objects.filter(funcao='pedreiro', ativo=True)[:3]
print(f"\nPedreiros encontrados: {len(pedreiros)}")
for p in pedreiros:
    print(f"  - {p.nome_completo} (ID: {p.id})")

# Buscar uma obra
obra = Obra.objects.first()
if not obra:
    print("\n❌ Nenhuma obra encontrada!")
    sys.exit(1)

print(f"\nObra: {obra.nome}")

# Buscar ou criar etapa 2
etapa = Etapa.objects.filter(obra=obra, numero_etapa=2).first()
if not etapa:
    print("\n⚠️ Etapa 2 não encontrada, criando...")
    etapa = Etapa.objects.create(
        obra=obra,
        numero_etapa=2,
        nome="Estrutura",
        data_inicio=date.today() - timedelta(days=30),
        data_termino=date.today()
    )

print(f"\nEtapa: {etapa}")

# Criar registros de produção para Etapa 2
print("\n" + "=" * 70)
print("CRIANDO REGISTROS DE PRODUÇÃO:")
print("=" * 70)

dados_etapa2 = [
    ('platibanda', 100, 'metros lineares'),
    ('platibanda', 80, 'metros lineares'),
    ('platibanda', 120, 'metros lineares'),
    ('respaldo_conclusao', 30, '%'),
    ('respaldo_conclusao', 40, '%'),
    ('laje_conclusao', 50, '%'),
    ('laje_conclusao', 50, '%'),
    ('cobertura_conclusao', 60, '%'),
    ('cobertura_conclusao', 40, '%'),
]

criados = 0
hoje = date.today()

for i, (indicador, quantidade, unidade) in enumerate(dados_etapa2):
    # Alternar entre os pedreiros
    pedreiro = pedreiros[i % len(pedreiros)]
    data_registro = hoje - timedelta(days=(i % 7))
    
    reg, created = RegistroProducao.objects.get_or_create(
        funcionario=pedreiro,
        data=data_registro,
        obra=obra,
        indicador=indicador,
        defaults={
            'quantidade': Decimal(str(quantidade)),
            'etapa': etapa
        }
    )
    
    if created:
        criados += 1
        print(f"✅ {pedreiro.nome_completo}: {indicador} = {quantidade} {unidade} ({data_registro})")
    else:
        print(f"⚠️ Já existe: {indicador} para {pedreiro.nome_completo} em {data_registro}")

print("\n" + "=" * 70)
print(f"RESULTADO: {criados} novos registros criados")
print("=" * 70)

# Verificar totais
print("\nTOTAIS POR INDICADOR DA ETAPA 2:")
for ind in ['platibanda', 'respaldo_conclusao', 'laje_conclusao', 'cobertura_conclusao']:
    count = RegistroProducao.objects.filter(indicador=ind).count()
    print(f"  {ind}: {count} registros")

print("\n✅ CONCLUÍDO! Agora a Etapa 2 deve aparecer no relatório.")
