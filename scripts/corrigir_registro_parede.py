import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao
from decimal import Decimal

print("=" * 80)
print("CORRIGINDO REGISTRO DE PAREDE - MARLON")
print("=" * 80)

# Buscar o registro
registro = RegistroProducao.objects.get(id=43)

print(f"\nRegistro encontrado:")
print(f"  ID: {registro.id}")
print(f"  Data: {registro.data}")
print(f"  Funcionário: {registro.funcionario.nome_completo}")
print(f"  Indicador: {registro.get_indicador_display()}")
print(f"  Obra: {registro.obra.nome}")
print(f"  Quantidade ANTES: {registro.quantidade} blocos")

# Corrigir
registro.quantidade = Decimal('100.00')
registro.save()

print(f"  Quantidade DEPOIS: {registro.quantidade} blocos")
print("\n✅ Registro corrigido com sucesso!")

# Validar novo cálculo
print("\n" + "=" * 80)
print("VALIDANDO NOVO CÁLCULO")
print("=" * 80)

registros = RegistroProducao.objects.filter(
    funcionario__nome_completo__icontains='marlon',
    indicador='parede_7fiadas'
).order_by('data')

total = 0
dias = set()

print("\nRegistros atualizados:")
for reg in registros:
    print(f"  {reg.data} | {reg.quantidade} blocos | {reg.obra.nome}")
    total += float(reg.quantidade)
    dias.add(reg.data)

num_dias = len(dias)
media = total / num_dias if num_dias > 0 else 0

print(f"\nTotal: {total:.2f} blocos")
print(f"Dias únicos: {num_dias}")
print(f"Média: {total:.2f} ÷ {num_dias} = {media:.2f} blocos/dia")

# Validar apenas março
print("\n" + "=" * 80)
print("VALIDANDO PERÍODO DE MARÇO (01/03 a 02/03)")
print("=" * 80)

from datetime import date
registros_marco = registros.filter(data__gte=date(2026, 3, 1), data__lte=date(2026, 3, 2))

total_marco = 0
dias_marco = set()

print("\nRegistros de março:")
for reg in registros_marco:
    print(f"  {reg.data} | {reg.quantidade} blocos")
    total_marco += float(reg.quantidade)
    dias_marco.add(reg.data)

num_dias_marco = len(dias_marco)
media_marco = total_marco / num_dias_marco if num_dias_marco > 0 else 0

print(f"\nTotal: {total_marco:.2f} blocos")
print(f"Dias únicos: {num_dias_marco}")
print(f"Média: {total_marco:.2f} ÷ {num_dias_marco} = {media_marco:.2f} blocos/dia")

if media_marco == 150.0:
    print("\n✅ PERFEITO! Média de março agora é 150 blocos/dia!")
else:
    print(f"\n⚠️ Média esperada: 150.0, obtida: {media_marco:.2f}")

print("\n" + "=" * 80)
