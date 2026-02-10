from django.contrib import admin
from .models import (
    Obra, Etapa, Etapa1Fundacao, Etapa2Estrutura,
    Etapa3Instalacoes, Etapa4Acabamentos, Etapa5Finalizacao
)


class EtapaInline(admin.TabularInline):
    model = Etapa
    extra = 0
    fields = ['numero_etapa', 'data_inicio', 'data_termino', 'concluida']
    readonly_fields = ['percentual_valor']


@admin.register(Obra)
class ObraAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cliente', 'status', 'percentual_concluido', 'data_inicio', 'ativo']
    list_filter = ['status', 'ativo', 'data_inicio']
    search_fields = ['nome', 'cliente', 'endereco']
    date_hierarchy = 'data_inicio'
    inlines = [EtapaInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'endereco', 'cliente')
        }),
        ('Datas', {
            'fields': ('data_inicio', 'data_previsao_termino')
        }),
        ('Status', {
            'fields': ('status', 'percentual_concluido', 'ativo')
        }),
    )


@admin.register(Etapa)
class EtapaAdmin(admin.ModelAdmin):
    list_display = ['obra', 'numero_etapa', 'percentual_valor', 'data_inicio', 'data_termino', 'concluida']
    list_filter = ['numero_etapa', 'concluida']
    search_fields = ['obra__nome']
    date_hierarchy = 'data_inicio'


@admin.register(Etapa1Fundacao)
class Etapa1FundacaoAdmin(admin.ModelAdmin):
    list_display = ['etapa', 'limpeza_terreno', 'instalacao_energia_agua', 'alicerce_percentual']
    search_fields = ['etapa__obra__nome']


@admin.register(Etapa2Estrutura)
class Etapa2EstruturaAdmin(admin.ModelAdmin):
    list_display = ['etapa', 'montagem_laje_dias', 'platibanda_blocos', 'cobertura_dias']
    search_fields = ['etapa__obra__nome']


@admin.register(Etapa3Instalacoes)
class Etapa3InstalacoesAdmin(admin.ModelAdmin):
    list_display = ['etapa', 'reboco_externo_m2', 'reboco_interno_m2', 'agua_fria', 'esgoto']
    search_fields = ['etapa__obra__nome']


@admin.register(Etapa4Acabamentos)
class Etapa4AcabamentosAdmin(admin.ModelAdmin):
    list_display = ['etapa', 'portas_janelas', 'pintura_externa_1demao_dias', 'assentamento_piso_dias']
    search_fields = ['etapa__obra__nome']


@admin.register(Etapa5Finalizacao)
class Etapa5FinalizacaoAdmin(admin.ModelAdmin):
    list_display = ['etapa', 'pintura_externa_2demao_dias', 'loucas_metais', 'eletrica']
    search_fields = ['etapa__obra__nome']
