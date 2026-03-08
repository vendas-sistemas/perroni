from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from apps.funcionarios.models import ApontamentoFuncionario


class Command(BaseCommand):
    help = (
        "Corrige historico de apontamentos para normalizar horas e valor por obra no dia. "
        "Etapas no mesmo dia/obra nao duplicam custo nem horas."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Aplica as correcoes no banco. Sem esta flag, roda em modo simulacao.",
        )

    def handle(self, *args, **options):
        apply_changes = options.get("apply", False)

        duplicated_groups = (
            ApontamentoFuncionario.objects.values("funcionario_id", "data")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
            .order_by("funcionario_id", "data")
        )

        total_groups = duplicated_groups.count()
        if total_groups == 0:
            self.stdout.write(self.style.SUCCESS("Nenhum funcionario com multiplos apontamentos no mesmo dia."))
            return

        self.stdout.write(
            self.style.WARNING(
                f"Encontrados {total_groups} grupo(s) com multiplos apontamentos no mesmo dia."
            )
        )

        adjusted_groups = 0
        total_rows = 0

        with transaction.atomic():
            for group in duplicated_groups:
                funcionario_id = group["funcionario_id"]
                data = group["data"]

                before = {
                    pk: (horas, valor)
                    for pk, horas, valor in ApontamentoFuncionario.objects.filter(
                        funcionario_id=funcionario_id,
                        data=data,
                    ).values_list("pk", "horas_trabalhadas", "valor_diaria")
                }

                ApontamentoFuncionario.ratear_diaria_por_obra(
                    funcionario_id=funcionario_id,
                    data=data,
                )

                after = {
                    pk: (horas, valor)
                    for pk, horas, valor in ApontamentoFuncionario.objects.filter(
                        funcionario_id=funcionario_id,
                        data=data,
                    ).values_list("pk", "horas_trabalhadas", "valor_diaria")
                }

                changed_rows = sum(1 for pk, novo in after.items() if before.get(pk) != novo)
                if changed_rows > 0:
                    adjusted_groups += 1
                    total_rows += changed_rows

            if not apply_changes:
                self.stdout.write(
                    self.style.WARNING(
                        f"SIMULACAO: {adjusted_groups} grupo(s) afetado(s), {total_rows} registro(s) seriam atualizados."
                    )
                )
                self.stdout.write(self.style.WARNING("Use --apply para aplicar as mudancas."))
                transaction.set_rollback(True)
                return

        if total_rows == 0:
            self.stdout.write(self.style.SUCCESS("Nenhuma atualizacao necessaria (historico ja normalizado)."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Correcao aplicada com sucesso: {adjusted_groups} grupo(s), {total_rows} registro(s) atualizados."
            )
        )
