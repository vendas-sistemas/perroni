# Migration: adicionar 3 novos campos em Etapa1Fundacao e platibanda_blocos em Etapa2Estrutura

from django.db import migrations, models
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('obras', '0008_etapahistorico'),
    ]

    operations = [
        # ── Etapa1Fundacao: levantar_alicerce_percentual ──
        migrations.AddField(
            model_name='etapa1fundacao',
            name='levantar_alicerce_percentual',
            field=models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=Decimal('0.00'),
                validators=[
                    django.core.validators.MinValueValidator(Decimal('0.00')),
                    django.core.validators.MaxValueValidator(Decimal('100.00')),
                ],
                verbose_name='Levantar Alicerce (%)',
                help_text='Percentual de conclusão do levantamento do alicerce',
            ),
        ),
        # ── Etapa1Fundacao: rebocar_alicerce_concluido ──
        migrations.AddField(
            model_name='etapa1fundacao',
            name='rebocar_alicerce_concluido',
            field=models.BooleanField(default=False, verbose_name='Rebocar Alicerce Concluído'),
        ),
        # ── Etapa1Fundacao: impermeabilizar_alicerce_concluido ──
        migrations.AddField(
            model_name='etapa1fundacao',
            name='impermeabilizar_alicerce_concluido',
            field=models.BooleanField(default=False, verbose_name='Impermeabilizar Alicerce Concluído'),
        ),
        # ── Etapa2Estrutura: platibanda_blocos (restaurado) ──
        migrations.AddField(
            model_name='etapa2estrutura',
            name='platibanda_blocos',
            field=models.PositiveIntegerField(default=0, verbose_name='Platibanda (Unidades de Blocos)'),
        ),
    ]
