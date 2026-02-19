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
print("INVESTIGANDO REGISTROS DE EDVALDO")
print("=" * 80)

edvaldo_producoes = RegistroProducao.objects.filter(
    funcionario__nome_completo__icontains='edvaldo'
).select_related('funcionario', 'obra').order_by('-criado_em', 'data', 'indicador')

print(f"\nTotal de registros encontrados: {edvaldo_producoes.count()}")

if edvaldo_producoes.count() > 0:
    print("\n" + "=" * 80)
    print("TODOS OS REGISTROS (do mais recente ao mais antigo):")
    print("=" * 80)
    
    for reg in edvaldo_producoes:
        print(f"""
ID: {reg.id}
Criado em: {reg.criado_em}
Data do registro: {reg.data}
Funcionário: {reg.funcionario.nome_completo}
Obra: {reg.obra.nome}
Indicador: {reg.get_indicador_display()}
Quantidade: {reg.quantidade}
{'=' * 80}""")
    
    # Agrupar por indicador
    print("\n" + "=" * 80)
    print("AGRUPANDO POR INDICADOR:")
    print("=" * 80)
    
    indicadores = edvaldo_producoes.values_list('indicador', flat=True).distinct()
    
    for indicador in indicadores:
        registros = edvaldo_producoes.filter(indicador=indicador).order_by('data')
        print(f"\n{dict(RegistroProducao.INDICADOR_CHOICES).get(indicador, indicador)}:")
        print("-" * 80)
        
        total = 0
        dias_unicos = set()
        
        for reg in registros:
            print(f"  ID {reg.id:3d} | {reg.data} | {reg.quantidade:7.2f} | {reg.obra.nome} | Criado: {reg.criado_em}")
            total += float(reg.quantidade)
            dias_unicos.add(reg.data)
        
        num_dias = len(dias_unicos)
        media = total / num_dias if num_dias > 0 else 0
        
        print(f"\n  Total: {total:.2f}")
        print(f"  Dias únicos: {num_dias}")
        print(f"  Média: {total:.2f} ÷ {num_dias} = {media:.2f} por dia")
        print("-" * 80)
    
    # Verificar duplicações
    print("\n" + "=" * 80)
    print("VERIFICANDO DUPLICAÇÕES:")
    print("=" * 80)
    
    from django.db.models import Count
    
    duplicados = RegistroProducao.objects.filter(
        funcionario__nome_completo__icontains='edvaldo'
    ).values('data', 'indicador', 'funcionario', 'obra').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    if duplicados.exists():
        print("\n⚠️ DUPLICAÇÕES ENCONTRADAS:")
        for dup in duplicados:
            print(f"\nData: {dup['data']} | Indicador: {dup['indicador']}")
            print(f"Quantidade de registros duplicados: {dup['count']}")
            print("-" * 40)
            
            # Mostrar os registros duplicados
            regs_dup = RegistroProducao.objects.filter(
                funcionario__nome_completo__icontains='edvaldo',
                data=dup['data'],
                indicador=dup['indicador']
            ).order_by('criado_em')
            
            for reg in regs_dup:
                print(f"  ID {reg.id}: {reg.quantidade} | Criado em: {reg.criado_em}")
            print()
    else:
        print("\n✅ Nenhuma duplicação encontrada")
    
    # Procurar especificamente por registros com 100
    print("\n" + "=" * 80)
    print("PROCURANDO REGISTROS COM QUANTIDADE = 100:")
    print("=" * 80)
    
    registros_100 = edvaldo_producoes.filter(quantidade=100)
    
    if registros_100.exists():
        print(f"\nEncontrados {registros_100.count()} registro(s) com quantidade = 100:")
        for reg in registros_100:
            print(f"\n  ID: {reg.id}")
            print(f"  Data: {reg.data}")
            print(f"  Indicador: {reg.get_indicador_display()}")
            print(f"  Quantidade: {reg.quantidade}")
            print(f"  Criado em: {reg.criado_em}")
    else:
        print("\n⚠️ Nenhum registro com quantidade = 100 encontrado")
else:
    print("\n⚠️ Nenhum registro de Edvaldo encontrado no banco de dados")

print("\n" + "=" * 80)
