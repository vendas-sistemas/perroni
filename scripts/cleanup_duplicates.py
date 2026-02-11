"""Remove duplicate apontamentos, keeping only the most recent per (funcionario, data, obra)."""
import django, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from apps.funcionarios.models import ApontamentoFuncionario
from django.db.models import Count, Max

dupes = (
    ApontamentoFuncionario.objects
    .values('funcionario_id', 'data', 'obra_id')
    .annotate(cnt=Count('id'), max_id=Max('id'))
    .filter(cnt__gt=1)
)

total_removed = 0
for d in dupes:
    to_delete = ApontamentoFuncionario.objects.filter(
        funcionario_id=d['funcionario_id'],
        data=d['data'],
        obra_id=d['obra_id'],
    ).exclude(id=d['max_id'])
    count = to_delete.count()
    to_delete.delete()
    total_removed += count
    print(f"  Removed {count} dupe(s): func={d['funcionario_id']}, data={d['data']}, obra={d['obra_id']}")

if total_removed == 0:
    print("No duplicates found.")
else:
    print(f"Total removed: {total_removed} duplicate row(s).")
