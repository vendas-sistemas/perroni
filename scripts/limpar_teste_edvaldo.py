import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao, ApontamentoDiarioLote
from apps.obras.models import Etapa, Etapa1Fundacao

print("=" * 80)
print("LIMPANDO DADOS DE TESTE PARA NOVO TESTE")
print("=" * 80)

# Deletar registros de Edvaldo
edvaldo_registros = RegistroProducao.objects.filter(
    funcionario__nome_completo__icontains='edvaldo'
)
count = edvaldo_registros.count()
edvaldo_registros.delete()
print(f"\n✅ {count} registro(s) de Edvaldo deletado(s)")

# Resetar valores da etapa Galpão Residencial 42
try:
    etapa = Etapa.objects.get(obra__nome='Galpão Residencial 42', numero_etapa=1)
    detalhes = Etapa1Fundacao.objects.get(etapa=etapa)
    
    print(f"\nValores ANTES:")
    print(f"  levantar_alicerce_percentual: {detalhes.levantar_alicerce_percentual}")
    print(f"  parede_7fiadas_blocos: {detalhes.parede_7fiadas_blocos}")
    
    detalhes.levantar_alicerce_percentual = 0
    detalhes.parede_7fiadas_blocos = 0
    detalhes.save()
    
    print(f"\nValores DEPOIS:")
    print(f"  levantar_alicerce_percentual: {detalhes.levantar_alicerce_percentual}")
    print(f"  parede_7fiadas_blocos: {detalhes.parede_7fiadas_blocos}")
    
    print("\n✅ Etapa resetada")
except Exception as e:
    print(f"\n⚠️ Erro ao resetar etapa: {e}")

# Deletar apontamentos em lote da etapa
try:
    lotes = ApontamentoDiarioLote.objects.filter(etapa=etapa)
    count = lotes.count()
    lotes.delete()
    print(f"\n✅ {count} apontamento(s) em lote deletado(s)")
except Exception as e:
    print(f"\n⚠️ Erro ao deletar lotes: {e}")

print("\n" + "=" * 80)
print("✅ DADOS LIMPOS - PRONTO PARA NOVO TESTE")
print("=" * 80)
print("\nAgora você pode fazer um novo apontamento cadastrando 100 blocos")
print("e o sistema deve salvar EXATAMENTE 100 blocos (não 400).")
