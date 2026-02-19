"""
Debug: Verificar dados reais e cálculos
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao, Funcionario
from datetime import date

print("=" * 70)
print("DEBUG: VERIFICANDO DADOS REAIS DE MARLON")
print("=" * 70)

# Buscar marlon
marlon = Funcionario.objects.filter(nome_completo__icontains='marlon', funcao='pedreiro').first()

if not marlon:
    print("Marlon não encontrado!")
    sys.exit(1)

print(f"\nPedreiro: {marlon.nome_completo} (ID: {marlon.id})")

# 1. Verificar Levantar Alicerce
print("\n" + "─" * 70)
print("1. LEVANTAR ALICERCE (%)")
print("─" * 70)

alicerce = RegistroProducao.objects.filter(
    funcionario=marlon,
    indicador='alicerce_percentual'
).order_by('data')

if alicerce.exists():
    print(f"\nRegistros encontrados: {alicerce.count()}")
    total = 0
    for reg in alicerce:
        print(f"  Data: {reg.data} | Quantidade: {reg.quantidade} | Obra: {reg.obra.nome}")
        total += float(reg.quantidade)
    
    dias_unicos = alicerce.values('data').distinct().count()
    media = total / dias_unicos if dias_unicos > 0 else 0
    
    print(f"\nCálculo:")
    print(f"  Total: {total}")
    print(f"  Dias únicos: {dias_unicos}")
    print(f"  Média CORRETA: {total} / {dias_unicos} = {media:.2f}%/dia")
else:
    print("Nenhum registro encontrado!")

# 2. Verificar Parede 7 Fiadas
print("\n" + "─" * 70)
print("2. PAREDE ATÉ 7 FIADAS (blocos)")
print("─" * 70)

parede = RegistroProducao.objects.filter(
    funcionario=marlon,
    indicador='parede_7fiadas'
).order_by('data')

if parede.exists():
    print(f"\nRegistros encontrados: {parede.count()}")
    total = 0
    for reg in parede:
        print(f"  Data: {reg.data} | Quantidade: {reg.quantidade} | Obra: {reg.obra.nome}")
        total += float(reg.quantidade)
    
    dias_unicos = parede.values('data').distinct().count()
    media = total / dias_unicos if dias_unicos > 0 else 0
    
    print(f"\nCálculo:")
    print(f"  Total: {total}")
    print(f"  Dias únicos: {dias_unicos}")
    print(f"  Média CORRETA: {total} / {dias_unicos} = {media:.2f} blocos/dia")
else:
    print("Nenhum registro encontrado!")

# 3. Testar função de ranking
print("\n" + "─" * 70)
print("3. TESTE DA FUNÇÃO ranking_por_indicador()")
print("─" * 70)

from apps.relatorios.services.analytics_indicadores import ranking_por_indicador

# Teste alicerce
ranking_alicerce = ranking_por_indicador('alicerce_percentual', None, top=3)
print(f"\nRanking Alicerce:")
if ranking_alicerce['melhores']:
    for i, item in enumerate(ranking_alicerce['melhores'], 1):
        print(f"  {i}. {item['nome']}: {item['media_producao']} %/dia ({item['total_dias']} dias)")

# Teste parede
ranking_parede = ranking_por_indicador('parede_7fiadas', None, top=3)
print(f"\nRanking Parede 7 Fiadas:")
if ranking_parede['melhores']:
    for i, item in enumerate(ranking_parede['melhores'], 1):
        print(f"  {i}. {item['nome']}: {item['media_producao']} blocos/dia ({item['total_dias']} dias)")

print("\n" + "=" * 70)
