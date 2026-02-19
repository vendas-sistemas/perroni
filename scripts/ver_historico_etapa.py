import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.obras.models import Etapa, Etapa1Fundacao, EtapaHistorico
from apps.funcionarios.models import ApontamentoDiarioLote

print("=" * 80)
print("HISTÓRICO DA ETAPA - Galpão Residencial 42")
print("=" * 80)

# Buscar a etapa
try:
    etapa = Etapa.objects.get(obra__nome='Galpão Residencial 42', numero_etapa=1)
    print(f"\nEtapa encontrada: {etapa}")
    
    # Buscar detalhes da etapa
    try:
        detalhes = Etapa1Fundacao.objects.get(etapa=etapa)
        print(f"\nValores ATUAIS da etapa:")
        for field in detalhes._meta.get_fields():
            if field.name not in ['id', 'etapa'] and hasattr(detalhes, field.name):
                valor = getattr(detalhes, field.name)
                if valor:
                    print(f"  {field.name}: {valor}")
    except Etapa1Fundacao.DoesNotExist:
        print("\n⚠️ Detalhes da etapa não encontrados")
    
    # Buscar histórico
    print("\n" + "=" * 80)
    print("HISTÓRICO DE ALTERAÇÕES:")
    print("=" * 80)
    
    historico = EtapaHistorico.objects.filter(etapa=etapa).order_by('data_hora')
    
    if historico.exists():
        for hist in historico:
            print(f"\n[{hist.data_hora}] - {hist.origem}")
            print(f"Usuario: {hist.usuario}")
            print(f"Descrição:")
            print(hist.descricao)
            print("-" * 80)
    else:
        print("\n⚠️ Nenhum histórico encontrado")
    
    # Buscar apontamentos em lote para esta etapa
    print("\n" + "=" * 80)
    print("APONTAMENTOS EM LOTE DESTA ETAPA:")
    print("=" * 80)
    
    lotes = ApontamentoDiarioLote.objects.filter(etapa=etapa).order_by('criado_em')
    
    if lotes.exists():
        for lote in lotes:
            print(f"\n[{lote.criado_em}] Lote ID {lote.id}")
            print(f"  Data: {lote.data}")
            print(f"  Produção Total: {lote.producao_total}")
            print(f"  Campos da etapa neste apontamento:")
            campos = lote.get_campos_etapa_dict()
            for campo, valor in campos.items():
                print(f"    {campo}: {valor}")
    else:
        print("\n⚠️ Nenhum apontamento encontrado")
    
except Etapa.DoesNotExist:
    print("\n⚠️ Etapa não encontrada")

print("\n" + "=" * 80)
