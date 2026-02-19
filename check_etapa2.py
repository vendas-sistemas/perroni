#!/usr/bin/env python
"""Script para verificar dados da Etapa 2"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao

print("=" * 70)
print("VERIFICAÇÃO DE DADOS POR INDICADOR")
print("=" * 70)

indicadores = [
    ('alicerce_percentual', 'Etapa 1'),
    ('parede_7fiadas', 'Etapa 1'),
    ('respaldo_conclusao', 'Etapa 2'),
    ('laje_conclusao', 'Etapa 2'),
    ('platibanda', 'Etapa 2'),
    ('cobertura_conclusao', 'Etapa 2'),
    ('reboco_externo', 'Etapa 3'),
    ('reboco_interno', 'Etapa 3'),
]

print("\nCONTAGEM DE REGISTROS:")
for ind, etapa in indicadores:
    count = RegistroProducao.objects.filter(indicador=ind).count()
    symbol = "✅" if count > 0 else "❌"
    print(f"{symbol} {etapa} - {ind}: {count} registros")

print("\n" + "=" * 70)
print("TOTAL GERAL:", RegistroProducao.objects.count(), "registros")
print("=" * 70)

# Verificar se há registros com campos esperados
print("\nAMOSTRA DE 3 REGISTROS:")
for reg in RegistroProducao.objects.all()[:3]:
    print(f"  - {reg.funcionario.nome_completo}: {reg.indicador} = {reg.quantidade} ({reg.data})")
