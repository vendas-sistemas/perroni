#!/usr/bin/env python
"""Script para testar o relatório com Etapa 2"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.relatorios.services.analytics_indicadores import ranking_geral_por_etapas

print("=" * 70)
print("TESTANDO RELATÓRIO - RANKING GERAL POR ETAPAS")
print("=" * 70)

# Testar sem filtros (todos os dados)
resultado = ranking_geral_por_etapas(filtros=None, top=3, bottom=3)

print(f"\n✅ Total de etapas retornadas: {len(resultado)}")

for etapa in resultado:
    print(f"\n{'=' * 70}")
    print(f"📊 {etapa['nome']}")
    print(f"{'=' * 70}")
    print(f"Indicadores: {len(etapa['indicadores'])}")
    
    for ind in etapa['indicadores']:
        print(f"\n  📈 {ind['nome']} ({ind['unidade']})")
        print(f"     Tipo: {ind['tipo']}")
        print(f"     Melhores: {len(ind['melhores'])} pedreiros")
        
        if ind['melhores']:
            for i, m in enumerate(ind['melhores'][:3], 1):
                print(f"       {i}º {m['nome']}: {m['media_producao']} {ind['unidade']}/dia")

print("\n" + "=" * 70)
print("✅ TESTE CONCLUÍDO")
print("=" * 70)
