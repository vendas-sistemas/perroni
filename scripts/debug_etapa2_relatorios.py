#!/usr/bin/env python
"""
Script para debugar por que etapa 2 e médias individuais não aparecem nos relatórios
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao, Funcionario
from apps.obras.models import Etapa
from collections import defaultdict

print("=" * 80)
print("DIAGNÓSTICO: Etapa 2 e Médias Individuais nos Relatórios")
print("=" * 80)

# 1. Verificar registros de produção por etapa
print("\n1. REGISTROS DE PRODUÇÃO POR ETAPA:")
print("-" * 80)

registros_por_etapa = (
    RegistroProducao.objects
    .filter(etapa__isnull=False)
    .values('etapa__numero_etapa')
    .distinct()
    .order_by('etapa__numero_etapa')
)

print(f"Etapas com registros de produção: {list(registros_por_etapa)}")

for etapa_num in [1, 2, 3, 4, 5]:
    count = RegistroProducao.objects.filter(etapa__numero_etapa=etapa_num).count()
    print(f"  Etapa {etapa_num}: {count} registros")

# 2. Verificar registros de produção com etapa nula
print("\n2. REGISTROS SEM ETAPA ASSOCIADA:")
print("-" * 80)
sem_etapa = RegistroProducao.objects.filter(etapa__isnull=True).count()
print(f"Total de registros SEM etapa: {sem_etapa}")

# 3. Verificar indicadores da Etapa 2
print("\n3. INDICADORES DA ETAPA 2:")
print("-" * 80)

indicadores_etapa2 = ['respaldo_conclusao', 'laje_conclusao', 'platibanda', 'cobertura_conclusao']

for indicador in indicadores_etapa2:
    # Com etapa 2
    com_etapa = RegistroProducao.objects.filter(
        indicador=indicador,
        etapa__numero_etapa=2
    ).count()
    
    # Sem etapa
    sem_etapa_ind = RegistroProducao.objects.filter(
        indicador=indicador,
        etapa__isnull=True
    ).count()
    
    # Total do indicador
    total_ind = RegistroProducao.objects.filter(indicador=indicador).count()
    
    print(f"  {indicador}:")
    print(f"    - Com etapa 2: {com_etapa}")
    print(f"    - Sem etapa: {sem_etapa_ind}")
    print(f"    - Total: {total_ind}")

# 4. Verificar se há pedreiros com dados
print("\n4. PEDREIROS COM REGISTROS DE PRODUÇÃO:")
print("-" * 80)

pedreiros_com_dados = (
    RegistroProducao.objects
    .filter(funcionario__funcao='pedreiro', quantidade__gt=0)
    .values('funcionario__nome_completo')
    .distinct()
    .count()
)

print(f"Pedreiros com registros de produção: {pedreiros_com_dados}")

# Listar alguns
pedreiros = (
    RegistroProducao.objects
    .filter(funcionario__funcao='pedreiro', quantidade__gt=0)
    .values('funcionario_id', 'funcionario__nome_completo')
    .annotate(total=django.db.models.Count('id'))
    .order_by('-total')[:10]
)

print("\nTop 10 pedreiros com mais registros:")
for p in pedreiros:
    print(f"  - {p['funcionario__nome_completo']}: {p['total']} registros")

# 5. Verificar médias de rendimento por pedreiro
print("\n5. CÁLCULO DE MÉDIAS INDIVIDUAIS:")
print("-" * 80)

from django.db.models import Sum, Count

stats = (
    RegistroProducao.objects
    .filter(funcionario__funcao='pedreiro', quantidade__gt=0)
    .values('funcionario_id', 'funcionario__nome_completo')
    .annotate(
        total_producao=Sum('quantidade'),
        total_dias=Count('data', distinct=True),
    )
    .order_by('-total_producao')[:5]
)

print("Top 5 pedreiros por produção total:")
for s in stats:
    media = float(s['total_producao']) / s['total_dias'] if s['total_dias'] > 0 else 0
    print(f"  - {s['funcionario__nome_completo']}:")
    print(f"      Total produção: {s['total_producao']}")
    print(f"      Total dias: {s['total_dias']}")
    print(f"      Média/dia: {media:.2f}")

# 6. Teste da função ranking_geral_por_etapas
print("\n6. TESTE DA FUNÇÃO ranking_geral_por_etapas:")
print("-" * 80)

from apps.relatorios.services.analytics_indicadores import ranking_geral_por_etapas

resultado = ranking_geral_por_etapas(filtros=None, top=3, bottom=3)

print(f"Total de etapas retornadas: {len(resultado)}")
for etapa in resultado:
    print(f"\n  {etapa['nome']} (Etapa {etapa['numero']}):")
    print(f"    Total de indicadores com dados: {len(etapa['indicadores'])}")
    for ind in etapa['indicadores']:
        print(f"      - {ind['nome']}: {len(ind['melhores'])} melhores, {len(ind['piores'])} piores")

# 7. Teste da função media_rendimento_por_pedreiro
print("\n7. TESTE DA FUNÇÃO media_rendimento_por_pedreiro:")
print("-" * 80)

from apps.relatorios.services.analytics_indicadores import media_rendimento_por_pedreiro

medias = media_rendimento_por_pedreiro(filtros=None)

print(f"Total de pedreiros retornados: {len(medias)}")
if medias:
    print("\nPrimeiros 5 pedreiros:")
    for m in medias[:5]:
        print(f"  - {m['nome']}:")
        print(f"      Média produção: {m.get('media_producao', 'N/A')}")
        print(f"      Total dias: {m['total_dias']}")
        print(f"      Ociosidade: {m['total_ociosidade']}")
        print(f"      Retrabalho: {m['total_retrabalho']}")
else:
    print("  ⚠️  NENHUM pedreiro retornado!")

print("\n" + "=" * 80)
print("DIAGNÓSTICO CONCLUÍDO")
print("=" * 80)
