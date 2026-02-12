from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from apps.funcionarios.models import Funcionario
from apps.obras.models import Obra, Etapa


class ProducaoDiaria(models.Model):
    """Registro de produção diária por pedreiro e etapa da obra."""

    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        related_name='producoes_diarias',
        verbose_name='Pedreiro',
        limit_choices_to={'funcao': 'pedreiro'},
    )

    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='producoes_diarias',
        verbose_name='Obra',
    )

    etapa = models.ForeignKey(
        Etapa,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='producoes_diarias',
        verbose_name='Etapa',
    )

    data = models.DateField(verbose_name='Data')

    CLIMA_CHOICES = [
        ('sol', 'Sol'),
        ('chuva', 'Chuva'),
        ('nublado', 'Nublado'),
    ]
    clima = models.CharField(
        max_length=10,
        choices=CLIMA_CHOICES,
        default='sol',
        verbose_name='Clima/Tempo',
    )

    houve_ociosidade = models.BooleanField(
        default=False,
        verbose_name='Houve Ociosidade',
    )

    houve_retrabalho = models.BooleanField(
        default=False,
        verbose_name='Houve Retrabalho',
    )
    motivo_retrabalho = models.TextField(
        blank=True,
        default='',
        verbose_name='Motivo do Retrabalho',
    )

    metragem_executada = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Metragem Executada (m²)',
    )

    observacoes = models.TextField(
        blank=True,
        default='',
        verbose_name='Observações',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Produção Diária'
        verbose_name_plural = 'Produções Diárias'
        ordering = ['-data', 'funcionario__nome_completo']
        unique_together = ['funcionario', 'obra', 'etapa', 'data']

    def __str__(self):
        return (
            f'{self.funcionario.nome_completo} — '
            f'{self.obra.nome} — '
            f'{self.etapa} — '
            f'{self.data:%d/%m/%Y} — '
            f'{self.metragem_executada} m²'
        )
