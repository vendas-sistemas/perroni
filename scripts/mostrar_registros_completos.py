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
print("TODOS OS REGISTROS DE MARLON - DETALHADO")
print("=" * 80)

marlon_producoes = RegistroProducao.objects.filter(
    funcionario__nome_completo__icontains='marlon'
).select_related('funcionario', 'obra').order_by('data', 'indicador')

print(f"\nTotal de registros encontrados: {marlon_producoes.count()}")
print("\n" + "=" * 80)

for reg in marlon_producoes:
    print(f"""
ID: {reg.id}
Data: {reg.data}
Funcionário: {reg.funcionario.nome_completo}
Obra: {reg.obra.nome}
Indicador: {reg.indicador}
Quantidade: {reg.quantidade}
Unidade: {reg.get_indicador_display()}
Criado em: {reg.criado_em}
{'=' * 80}""")

print("\n" + "=" * 80)
print("AGRUPANDO POR INDICADOR:")
print("=" * 80)

indicadores = marlon_producoes.values_list('indicador', flat=True).distinct()

for indicador in indicadores:
    registros = marlon_producoes.filter(indicador=indicador).order_by('data')
    print(f"\n{indicador}:")
    print("-" * 80)
    
    total = 0
    dias_unicos = set()
    
    for reg in registros:
        print(f"  [{reg.id}] {reg.data} | {reg.quantidade} | {reg.obra.nome}")
        total += reg.quantidade
        dias_unicos.add(reg.data)
    
    num_dias = len(dias_unicos)
    media = total / num_dias if num_dias > 0 else 0
    
    print(f"\n  Total: {total}")
    print(f"  Dias únicos: {num_dias} → {sorted(dias_unicos)}")
    print(f"  Média: {total} ÷ {num_dias} = {media:.2f}")
    print("-" * 80)

print("\n" + "=" * 80)
print("VERIFICANDO DUPLICAÇÕES:")
print("=" * 80)

# Verificar se há registros duplicados (mesma data, indicador, funcionário, obra)
from django.db.models import Count

duplicados = RegistroProducao.objects.filter(
    funcionario__nome_completo__icontains='marlon'
).values('data', 'indicador', 'funcionario', 'obra').annotate(
    count=Count('id')
).filter(count__gt=1)

if duplicados.exists():
    print("\n⚠️ DUPLICAÇÕES ENCONTRADAS:")
    for dup in duplicados:
        print(f"  Data: {dup['data']}")
        print(f"  Indicador: {dup['indicador']}")
        print(f"  Quantidade de registros duplicados: {dup['count']}")
        print("-" * 40)
        
        # Mostrar os registros duplicados
        regs_dup = RegistroProducao.objects.filter(
            funcionario__nome_completo__icontains='marlon',
            data=dup['data'],
            indicador=dup['indicador']
        )
        for reg in regs_dup:
            print(f"    ID {reg.id}: {reg.quantidade}")
        print()
else:
    print("\n✅ Nenhuma duplicação encontrada")
