from django.contrib.auth.models import Group
from django.db import models

from config.access_control import AREA_CHOICES


class GroupAreaPermission(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='area_permissions',
        verbose_name='Grupo',
    )
    area = models.CharField(max_length=64, choices=AREA_CHOICES, verbose_name='Área')
    can_view = models.BooleanField(default=False, verbose_name='Ver')
    can_create = models.BooleanField(default=False, verbose_name='Criar')
    can_edit = models.BooleanField(default=False, verbose_name='Editar')
    can_delete = models.BooleanField(default=False, verbose_name='Excluir')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Permissão do Grupo por Área'
        verbose_name_plural = 'Permissões dos Grupos por Área'
        unique_together = ('group', 'area')
        ordering = ('group__name', 'area')

    def __str__(self):
        return f'{self.group.name} - {self.area}'

