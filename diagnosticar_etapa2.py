#!/usr/bin/env python
"""Verificar por que indicadores de conclusão não aparecem"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao
from apps.relatorios.services.analytics_indicadores import ranking_por_indicador

print("=" * 70)
print("DIAGNÓSTICO: INDICADORES DA ETAPA 2")
print("=" * 70)

indicadores_etapa2 = [
    ('platibanda', 'quantitativo'),
    ('respaldo_conclusao', 'conclusão'),
    ('laje_conclusao', 'conclusão'),
    ('cobertura_conclusao', 'conclusão'),
]

for indicador, tipo in indicadores_etapa2:
    print(f"\n{'=' * 70}")
    print(f"📊 {indicador} ({tipo})")
    print(f"{'=' * 70}")
    
    # Contar registros
    count = RegistroProducao.objects.filter(indicador=indicador).count()
    print(f"Registros no banco: {count}")
    
    if count > 0:
        # Mostrar amostra
        registros = RegistroProducao.objects.filter(indicador=indicador)[:3]
        print("\nAmostra de registros:")
        for reg in registros:
            print(f"  - {reg.funcionario.nome_completo}: {reg.quantidade} ({reg.data})")
        
        # Testar ranking
        print("\nTestando ranking_por_indicador():")
        try:
            ranking = ranking_por_indicador(indicador, None, top=3, bottom=0)
            
            if ranking:
                print(f"  ✅ Ranking retornou dados")
                print(f"  Melhores: {len(ranking.get('melhores', []))}")
                print(f"  Piores: {len(ranking.get('piores', []))}")
                
                if ranking.get('melhores'):
                    print("\n  Top 3:")
                    for i, m in enumerate(ranking['melhores'][:3], 1):
                        print(f"    {i}º {m['nome']}: {m['media_producao']}")
                else:
                    print("  ⚠️ Lista 'melhores' está vazia!")
            else:
                print("  ❌ Ranking retornou None ou vazio")
                
        except Exception as e:
            print(f"  ❌ ERRO ao calcular ranking: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("  ❌ Nenhum registro encontrado no banco!")

print("\n" + "=" * 70)
print("TESTE CONCLUÍDO")
print("=" * 70)
