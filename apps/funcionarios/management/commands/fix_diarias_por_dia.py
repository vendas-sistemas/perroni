from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from apps.funcionarios.models import ApontamentoFuncionario


class Command(BaseCommand):
    help = (
        "Corrige histórico de apontamentos para garantir 1 diária por funcionário/dia. "
        "Mantém 1 registro com valor da diária base do funcionário e zera os demais no mesmo dia."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Aplica as correções no banco. Sem esta flag, roda em modo simulação.",
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
            self.stdout.write(self.style.SUCCESS("Nenhum funcionário com múltiplos apontamentos no mesmo dia."))
            return

        self.stdout.write(
            self.style.WARNING(
                f"Encontrados {total_groups} grupo(s) com múltiplos apontamentos no mesmo dia."
            )
        )

        rows_to_update = []
        adjusted_groups = 0

        for group in duplicated_groups:
            funcionario_id = group["funcionario_id"]
            data = group["data"]
            group_changes = 0

            day_rows = list(
                ApontamentoFuncionario.objects.filter(
                    funcionario_id=funcionario_id,
                    data=data,
                )
                .select_related("funcionario")
                .order_by("created_at", "pk")
            )

            if not day_rows:
                continue

            diaria_base = day_rows[0].funcionario.valor_diaria or Decimal("0.00")
            keeper = day_rows[0]

            # Regra: 1 diária cheia no primeiro registro do dia, demais zerados.
            if keeper.valor_diaria != diaria_base:
                rows_to_update.append((keeper.pk, diaria_base))
                group_changes += 1

            for row in day_rows[1:]:
                if row.valor_diaria != Decimal("0.00"):
                    rows_to_update.append((row.pk, Decimal("0.00")))
                    group_changes += 1

            if group_changes > 0:
                adjusted_groups += 1

        total_rows = len(rows_to_update)

        if not apply_changes:
            self.stdout.write(
                self.style.WARNING(
                    f"SIMULAÇÃO: {adjusted_groups} grupo(s) afetado(s), {total_rows} registro(s) seriam atualizados."
                )
            )
            self.stdout.write(self.style.WARNING("Use --apply para aplicar as mudanças."))
            return

        if total_rows == 0:
            self.stdout.write(self.style.SUCCESS("Nenhuma atualização necessária (histórico já normalizado)."))
            return

        with transaction.atomic():
            for pk, new_value in rows_to_update:
                ApontamentoFuncionario.objects.filter(pk=pk).update(valor_diaria=new_value)

        self.stdout.write(
            self.style.SUCCESS(
                f"Correção aplicada com sucesso: {adjusted_groups} grupo(s), {total_rows} registro(s) atualizados."
            )
        )
