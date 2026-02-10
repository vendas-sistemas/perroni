from django.core.management.base import BaseCommand

from apps.obras.models import Obra, Etapa


class Command(BaseCommand):
    help = 'Inicializa etapas faltantes para todas as Obras existentes.'

    def handle(self, *args, **options):
        created = 0
        for o in Obra.objects.all():
            if o.etapas.count() == 0:
                for num, _label in Etapa.ETAPA_CHOICES:
                    Etapa.objects.create(
                        obra=o,
                        numero_etapa=num,
                        percentual_valor=Etapa.PERCENTUAIS_ETAPA.get(num)
                    )
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Obras sem etapas preenchidas: {created}'))
        self.stdout.write(self.style.SUCCESS(f'Total Etapas: {Etapa.objects.count()}'))
