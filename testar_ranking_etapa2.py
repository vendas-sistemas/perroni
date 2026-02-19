#!/usr/bin/env python
"""Testar ranking_geral_por_etapas em detalhe"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.relatorios.services.analytics_indicadores import ranking_geral_por_etapas, ranking_por_indicador

print("=" * 70)
print("TESTE: ranking_geral_por_etapas()")
print("=" * 70)

resultado = ranking_geral_por_etapas(filtros=None, top=3, bottom=3)

for etapa in resultado:
    if etapa['numero'] == 2:
        print(f"\n{'=' * 70}")
        print(f"📊 {etapa['nome']}")
        print(f"{'=' * 70}")
        print(f"Total de indicadores retornados: {len(etapa['indicadores'])}")
        
        for ind in etapa['indicadores']:
            print(f"\n  ▶ {ind['nome']} ({ind['unidade']})")
            print(f"     Tipo: {ind['tipo']}")
            print(f"     Código: {ind['codigo']}")
            print(f"     Melhores: {len(ind['melhores'])}")
            print(f"     Piores: {len(ind['piores'])}")
            
            if ind['melhores']:
                print(f"     Top 1: {ind['melhores'][0]['nome']} = {ind['melhores'][0]['media_producao']}")

print("\n" + "=" * 70)
print("TESTE INDIVIDUAL DE CADA INDICADOR DA ETAPA 2:")
print("=" * 70)

indicadores = ['respaldo_conclusao', 'laje_conclusao', 'platibanda', 'cobertura_conclusao']

for ind in indicadores:
    print(f"\n{ind}:")
    ranking = ranking_por_indicador(ind, None, top=3, bottom=3)
    
    tem_melhores = bool(ranking['melhores'])
    tem_piores = bool(ranking['piores'])
    
    print(f"  Retornou melhores? {tem_melhores}")
    print(f"  Retornou piores? {tem_piores}")
    print(f"  Será incluído? {tem_melhores or tem_piores}")
