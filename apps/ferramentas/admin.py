from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Ferramenta, MovimentacaoFerramenta,
    ConferenciaFerramenta, ItemConferencia,
    LocalizacaoFerramenta
)


class LocalizacaoFerramentaInline(admin.TabularInline):
    """Inline para distribuição de quantidades por localização"""
    model = LocalizacaoFerramenta
    extra = 0
    fields = ['local_tipo', 'obra', 'quantidade']
    readonly_fields = []
    
    def get_readonly_fields(self, request, obj=None):
        # Se já existe, deixar local_tipo e obra readonly
        if obj:
            return ['local_tipo', 'obra']
        return []


@admin.register(Ferramenta)
class FerramentaAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nome', 'categoria', 'quantidade_total',
        'qtd_deposito', 'qtd_obras', 'qtd_manutencao',
        'ativo', 'foto_thumb'
    ]
    list_filter = ['categoria', 'ativo']
    search_fields = ['codigo', 'nome', 'descricao']
    inlines = [LocalizacaoFerramentaInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'descricao', 'categoria', 'foto')
        }),
        ('Quantidade e Valor', {
            'fields': ('quantidade_total', 'valor_unitario', 'data_aquisicao')
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
    
    def qtd_deposito(self, obj):
        return obj.quantidade_deposito
    qtd_deposito.short_description = 'Depósito'
    
    def qtd_obras(self, obj):
        return obj.quantidade_em_obras
    qtd_obras.short_description = 'Em Obras'
    
    def qtd_manutencao(self, obj):
        return obj.quantidade_manutencao
    qtd_manutencao.short_description = 'Manutenção'


@admin.register(MovimentacaoFerramenta)
class MovimentacaoFerramentaAdmin(admin.ModelAdmin):
    list_display = [
        'ferramenta', 'quantidade', 'tipo', 'origem_tipo', 'destino_tipo',
        'obra_origem', 'obra_destino', 'responsavel', 'data_movimentacao'
    ]
    list_filter = ['tipo', 'origem_tipo', 'destino_tipo', 'data_movimentacao']
    search_fields = ['ferramenta__codigo', 'ferramenta__nome']
    date_hierarchy = 'data_movimentacao'
    readonly_fields = ['origem_tipo', 'destino_tipo']
    
    fieldsets = (
        ('Ferramenta', {
            'fields': ('ferramenta', 'quantidade', 'tipo')
        }),
        ('Origem e Destino', {
            'fields': ('origem_tipo', 'obra_origem', 'destino_tipo', 'obra_destino')
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
    fields = ['ferramenta', 'quantidade_esperada', 'quantidade_encontrada', 'diferenca_display', 'status', 'observacoes']
    readonly_fields = ['diferenca_display', 'status']
    
    def diferenca_display(self, obj):
        """Mostra diferença entre esperado e encontrado"""
        if obj.pk:
            dif = obj.diferenca
            if dif > 0:
                return format_html('<span style="color: red;">+{}</span>', dif)
            elif dif < 0:
                return format_html('<span style="color: orange;">{}</span>', dif)
            return format_html('<span style="color: green;">0</span>')
        return '-'
    diferenca_display.short_description = 'Diferença'


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
    list_display = ['conferencia', 'ferramenta', 'quantidade_esperada', 'quantidade_encontrada', 'diferenca_display', 'status']
    list_filter = ['status', 'conferencia__data_conferencia']
    search_fields = ['ferramenta__codigo', 'ferramenta__nome', 'conferencia__obra__nome']
    readonly_fields = ['status']
    
    def diferenca_display(self, obj):
        dif = obj.diferenca
        if dif > 0:
            return format_html('<span style="color: red;">+{}</span>', dif)
        elif dif < 0:
            return format_html('<span style="color: orange;">{}</span>', dif)
        return format_html('<span style="color: green;">0</span>')
    diferenca_display.short_description = 'Diferença'
