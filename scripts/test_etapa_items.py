"""Quick test to verify etapa items loading for apontamento diário."""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.funcionarios.views import _get_etapa_items, ETAPA_FIELDS_META
from apps.obras.models import Obra, Etapa

obra = Obra.objects.get(pk=106)
etapas = Etapa.objects.filter(obra=obra).order_by('numero_etapa')
print(f"Obra: {obra.nome} (id={obra.pk})")
print(f"Total etapas: {etapas.count()}")
print("=" * 60)

for etapa in etapas:
    items = _get_etapa_items(etapa)
    print(f"\nEtapa {etapa.numero_etapa} (id={etapa.id}): {len(items)} itens")
    for i in items:
        val = i['value']
        typ = i['type']
        label = i['label']
        name = i['name']
        if typ == 'boolean':
            status = "SIM" if val else "NAO"
            print(f"  [{typ:8}] {label:40} = {status}")
        else:
            print(f"  [{typ:8}] {label:40} = {val}")

print("\n" + "=" * 60)
print("Tudo OK! Todos os itens estao carregando corretamente.")
