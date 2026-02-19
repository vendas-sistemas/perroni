import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao
from datetime import date

print("=" * 80)
print("VERIFICANDO TODOS OS INDICADORES DE MARLON")
print("=" * 80)

indicadores = [
    'alicerce_percentual',
    'parede_7fiadas',
    'respaldo_conclusao',
    'laje_conclusao',
    'platibanda',
    'cobertura_conclusao',
    'reboco_externo',
    'reboco_interno',
]

for indicador in indicadores:
    registros = RegistroProducao.objects.filter(
        funcionario__nome_completo__icontains='marlon',
        indicador=indicador
    ).order_by('data')
    
    if not registros.exists():
        continue
    
    print(f"\n{'=' * 80}")
    print(f"{dict(RegistroProducao.INDICADOR_CHOICES).get(indicador, indicador)}")
    print(f"{'=' * 80}")
    
    # Cálculo completo
    total_completo = 0
    dias_completo = set()
    
    print("\nRegistros completos:")
    for reg in registros:
        print(f"  {reg.data} | {reg.quantidade:7.2f} | {reg.obra.nome}")
        total_completo += float(reg.quantidade)
        dias_completo.add(reg.data)
    
    num_dias_completo = len(dias_completo)
    media_completo = total_completo / num_dias_completo if num_dias_completo > 0 else 0
    
    print(f"\n  Total: {total_completo:.2f}")
    print(f"  Dias únicos: {num_dias_completo}")
    print(f"  Média completa: {media_completo:.2f} por dia")
    
    # Cálculo filtrado para março
    registros_marco = registros.filter(data__gte=date(2026, 3, 1), data__lte=date(2026, 3, 2))
    
    if registros_marco.exists():
        total_marco = 0
        dias_marco = set()
        
        print("\n  Registros de março (01/03 a 02/03):")
        for reg in registros_marco:
            print(f"    {reg.data} | {reg.quantidade:7.2f}")
            total_marco += float(reg.quantidade)
            dias_marco.add(reg.data)
        
        num_dias_marco = len(dias_marco)
        media_marco = total_marco / num_dias_marco if num_dias_marco > 0 else 0
        
        print(f"\n    Total março: {total_marco:.2f}")
        print(f"    Dias março: {num_dias_marco}")
        print(f"    Média março: {media_marco:.2f} por dia")

print("\n" + "=" * 80)
print("✅ VERIFICAÇÃO COMPLETA")
print("=" * 80)
