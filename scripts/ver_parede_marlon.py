import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao

print("=" * 80)
print("REGISTROS DE MARLON - PAREDE 7 FIADAS")
print("=" * 80)

registros = RegistroProducao.objects.filter(
    funcionario__nome_completo__icontains='marlon',
    indicador='parede_7fiadas'
).select_related('funcionario', 'obra').order_by('data')

print(f"\nTotal de registros: {registros.count()}\n")

total = 0
dias = set()

for reg in registros:
    print(f"ID {reg.id:3d} | {reg.data} | {reg.quantidade:7.2f} blocos | {reg.obra.nome}")
    total += float(reg.quantidade)
    dias.add(reg.data)

num_dias = len(dias)
media = total / num_dias if num_dias > 0 else 0

print("\n" + "=" * 80)
print(f"Total: {total:.2f} blocos")
print(f"Dias únicos: {num_dias}")
print(f"Dias: {sorted(dias)}")
print(f"Média: {total:.2f} ÷ {num_dias} = {media:.2f} blocos/dia")
print("=" * 80)

# Verificar duplicações
print("\nVerificando duplicações (mesma data + indicador):")
from django.db.models import Count

duplicados = RegistroProducao.objects.filter(
    funcionario__nome_completo__icontains='marlon',
    indicador='parede_7fiadas'
).values('data').annotate(
    count=Count('id'),
    total=Count('id')
).filter(count__gt=1)

if duplicados.exists():
    print("\n⚠️ DUPLICAÇÕES ENCONTRADAS:")
    for dup in duplicados:
        print(f"\nData: {dup['data']} tem {dup['count']} registros:")
        regs = RegistroProducao.objects.filter(
            funcionario__nome_completo__icontains='marlon',
            indicador='parede_7fiadas',
            data=dup['data']
        )
        for reg in regs:
            print(f"  ID {reg.id}: {reg.quantidade} blocos | Obra: {reg.obra.nome}")
else:
    print("\n✅ Nenhuma duplicação encontrada")
