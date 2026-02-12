from django.contrib import admin
from .models import ProducaoDiaria


@admin.register(ProducaoDiaria)
class ProducaoDiariaAdmin(admin.ModelAdmin):
    list_display = [
        'funcionario', 'obra', 'etapa', 'data',
        'metragem_executada', 'clima', 'houve_ociosidade', 'houve_retrabalho',
    ]
    list_filter = ['clima', 'houve_ociosidade', 'houve_retrabalho', 'obra', 'etapa']
    search_fields = ['funcionario__nome_completo', 'obra__nome']
    date_hierarchy = 'data'
    ordering = ['-data']
