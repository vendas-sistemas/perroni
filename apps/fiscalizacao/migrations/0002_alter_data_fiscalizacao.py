"""Alter data_fiscalizacao to DateTimeField and remove unique_together.

Generated manually to reflect model changes where data_fiscalizacao became a
DateTimeField and the unique_together constraint (obra, data_fiscalizacao)
was removed so multiple inspections per obra/day (with times) are allowed.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fiscalizacao", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="registrofiscalizacao",
            name="data_fiscalizacao",
            field=models.DateTimeField(verbose_name="Data da Fiscalização"),
        ),
        migrations.AlterModelOptions(
            name="registrofiscalizacao",
            options={
                "verbose_name": "Registro de Fiscalização",
                "verbose_name_plural": "Registros de Fiscalização",
                "ordering": ["-data_fiscalizacao", "-created_at"],
            },
        ),
    ]
