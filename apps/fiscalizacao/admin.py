from django.contrib import admin
from .models import RegistroFiscalizacao, FotoFiscalizacao


class FotoFiscalizacaoInline(admin.TabularInline):
    model = FotoFiscalizacao
    extra = 6
    fields = ['foto', 'descricao', 'ordem']


@admin.register(RegistroFiscalizacao)
class RegistroFiscalizacaoAdmin(admin.ModelAdmin):
    list_display = [
        'obra', 'data_fiscalizacao', 'fiscal', 'clima',
        'lixo', 'placa_instalada', 'houve_ociosidade', 'houve_retrabalho'
    ]
    list_filter = ['data_fiscalizacao', 'clima', 'lixo', 'placa_instalada', 'houve_ociosidade', 'houve_retrabalho']
    search_fields = ['obra__nome', 'fiscal__username']
    date_hierarchy = 'data_fiscalizacao'
    inlines = [FotoFiscalizacaoInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('obra', 'fiscal', 'data_fiscalizacao')
        }),
        ('Condições da Obra', {
            'fields': ('clima', 'lixo', 'placa_instalada')
        }),
        ('Ocorrências', {
            'fields': (
                'houve_ociosidade', 'observacao_ociosidade',
                'houve_retrabalho', 'motivo_retrabalho'
            )
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )


@admin.register(FotoFiscalizacao)
class FotoFiscalizacaoAdmin(admin.ModelAdmin):
    list_display = ['fiscalizacao', 'ordem', 'descricao', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['fiscalizacao__obra__nome', 'descricao']
