"""
Debug: Verificar cálculos para período específico de 2 dias de marlon
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao, Funcionario
from datetime import date
from decimal import Decimal

print("=" * 70)
print("DEBUG: QUAIS 2 DIAS GERAM 11% E 250 BLOCOS?")
print("=" * 70)

marlon = Funcionario.objects.filter(nome_completo__icontains='marlon', funcao='pedreiro').first()

# Testar todas as combinações possíveis de 2 dias para Alicerce
print("\nTestando ALICERCE - Buscando 2 dias que dão média de 11%:")
alicerce = RegistroProducao.objects.filter(
    funcionario=marlon,
    indicador='alicerce_percentual'
).order_by('data')

registros = list(alicerce)
for i in range(len(registros)):
    for j in range(i+1, len(registros)):
        r1 = registros[i]
        r2 = registros[j]
        total = float(r1.quantidade) + float(r2.quantidade)
        media = total / 2
        
        if abs(media - 11.0) < 0.5:  # Próximo de 11
            print(f"\n  Combinação encontrada:")
            print(f"    Dia 1: {r1.data} = {r1.quantidade}%")
            print(f"    Dia 2: {r2.data} = {r2.quantidade}%")
            print(f"    Total: {total}%")
            print(f"    Média: {media:.2f}%/dia")

# Testar Parede 7 Fiadas
print("\n" + "─" * 70)
print("\nTestando PAREDE 7 FIADAS - Buscando 2 dias que dão média de 250:")
parede = RegistroProducao.objects.filter(
    funcionario=marlon,
    indicador='parede_7fiadas'
).order_by('data')

registros_parede = list(parede)
for i in range(len(registros_parede)):
    for j in range(i+1, len(registros_parede)):
        r1 = registros_parede[i]
        r2 = registros_parede[j]
        total = float(r1.quantidade) + float(r2.quantidade)
        media = total / 2
        
        if abs(media - 250.0) < 10:  # Próximo de 250
            print(f"\n  Combinação encontrada:")
            print(f"    Dia 1: {r1.data} = {r1.quantidade} blocos")
            print(f"    Dia 2: {r2.data} = {r2.quantidade} blocos")
            print(f"    Total: {total} blocos")
            print(f"    Média: {media:.2f} blocos/dia")

# Verificar se há filtros ativos na view
print("\n" + "=" * 70)
print("VERIFICANDO SE HÁ FILTROS DE DATA:")
print("=" * 70)

# Testar com filtros de data diferentes
from apps.relatorios.services.analytics_indicadores import ranking_por_indicador

# Sem filtro
print("\nSEM FILTRO:")
ranking = ranking_por_indicador('alicerce_percentual', None, top=1)
if ranking['melhores']:
    for item in ranking['melhores']:
        if 'marlon' in item['nome'].lower():
            print(f"  Marlon: {item['media_producao']}%/dia ({item['total_dias']} dias)")

# Com filtro de março
print("\nCOM FILTRO MARÇO (2026-03-01 a 2026-03-02):")
filtros = {
    'data_inicio': date(2026, 3, 1),
    'data_fim': date(2026, 3, 2)
}
ranking = ranking_por_indicador('alicerce_percentual', filtros, top=1)
if ranking['melhores']:
    for item in ranking['melhores']:
        if 'marlon' in item['nome'].lower():
            print(f"  Marlon: {item['media_producao']}%/dia ({item['total_dias']} dias)")

ranking_p = ranking_por_indicador('parede_7fiadas', filtros, top=1)
if ranking_p['melhores']:
    for item in ranking_p['melhores']:
        if 'marlon' in item['nome'].lower():
            print(f"  Marlon Parede: {item['media_producao']} blocos/dia ({item['total_dias']} dias)")

print("\n" + "=" * 70)
