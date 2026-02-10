from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Ferramenta, MovimentacaoFerramenta,
    ConferenciaFerramenta, ItemConferencia
)


@admin.register(Ferramenta)
class FerramentaAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nome', 'categoria', 'status',
        'obra_atual', 'ativo', 'foto_thumb'
    ]
    list_filter = ['categoria', 'status', 'ativo']
    search_fields = ['codigo', 'nome', 'descricao']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'descricao', 'categoria', 'foto')
        }),
        ('Status e Localização', {
            'fields': ('status', 'obra_atual')
        }),
        ('Informações Adicionais', {
            'fields': ('data_aquisicao', 'valor_aquisicao')
        }),
        ('Controle', {
            'fields': ('ativo',)
        }),
    )
    
    def foto_thumb(self, obj):
        if obj.foto:
            return format_html('<img src="{}" width="50" height="50" />', obj.foto.url)
        return "Sem foto"
    foto_thumb.short_description = 'Foto'


@admin.register(MovimentacaoFerramenta)
class MovimentacaoFerramentaAdmin(admin.ModelAdmin):
    list_display = [
        'ferramenta', 'tipo', 'obra_origem', 'obra_destino',
        'responsavel', 'data_movimentacao'
    ]
    list_filter = ['tipo', 'data_movimentacao']
    search_fields = ['ferramenta__codigo', 'ferramenta__nome']
    date_hierarchy = 'data_movimentacao'
    
    fieldsets = (
        ('Ferramenta', {
            'fields': ('ferramenta', 'tipo')
        }),
        ('Origem e Destino', {
            'fields': ('origem', 'obra_origem', 'destino', 'obra_destino')
        }),
        ('Responsável', {
            'fields': ('responsavel',)
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )


class ItemConferenciaInline(admin.TabularInline):
    model = ItemConferencia
    extra = 0
    fields = ['ferramenta', 'status', 'observacoes']


@admin.register(ConferenciaFerramenta)
class ConferenciaFerramentaAdmin(admin.ModelAdmin):
    list_display = ['obra', 'data_conferencia', 'fiscal', 'total_itens']
    list_filter = ['data_conferencia']
    search_fields = ['obra__nome', 'fiscal__username']
    date_hierarchy = 'data_conferencia'
    inlines = [ItemConferenciaInline]
    
    def total_itens(self, obj):
        return obj.itens.count()
    total_itens.short_description = 'Total de Itens'


@admin.register(ItemConferencia)
class ItemConferenciaAdmin(admin.ModelAdmin):
    list_display = ['conferencia', 'ferramenta', 'status']
    list_filter = ['status']
    search_fields = ['ferramenta__codigo', 'ferramenta__nome']
