from django.contrib import admin
from django.utils.html import format_html
from .models import Funcionario, ApontamentoFuncionario, FechamentoSemanal


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = [
        'nome_completo', 'funcao', 'telefone', 'valor_diaria',
        'ativo', 'foto_thumb'
    ]
    list_filter = ['funcao', 'ativo', 'cidade', 'estado']
    search_fields = ['nome_completo', 'cpf', 'telefone']
    date_hierarchy = 'data_admissao'
    
    fieldsets = (
        ('Dados Pessoais', {
            'fields': ('nome_completo', 'cpf', 'rg', 'data_nascimento', 'foto')
        }),
        ('Contato', {
            'fields': ('telefone', 'email')
        }),
        ('Endereço', {
            'fields': ('endereco', 'cidade', 'estado', 'cep')
        }),
        ('Função e Valores', {
            'fields': ('funcao', 'valor_diaria')
        }),
        ('Status', {
            'fields': ('ativo', 'data_admissao', 'data_demissao', 'motivo_inativacao')
        }),
    )
    
    def foto_thumb(self, obj):
        if obj.foto:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.foto.url)
        return "Sem foto"
    foto_thumb.short_description = 'Foto'


@admin.register(ApontamentoFuncionario)
class ApontamentoFuncionarioAdmin(admin.ModelAdmin):
    list_display = ['funcionario', 'obra', 'data', 'valor_diaria']
    list_filter = ['data', 'funcionario__funcao']
    search_fields = ['funcionario__nome_completo', 'obra__nome']
    date_hierarchy = 'data'
    
    fieldsets = (
        ('Apontamento', {
            'fields': ('funcionario', 'obra', 'data')
        }),
        ('Valores', {
            'fields': ('valor_diaria',)
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )


@admin.register(FechamentoSemanal)
class FechamentoSemanalAdmin(admin.ModelAdmin):
    list_display = [
        'funcionario', 'data_inicio', 'data_fim',
        'total_dias', 'total_valor', 'status', 'data_pagamento'
    ]
    list_filter = ['status', 'data_inicio', 'data_pagamento']
    search_fields = ['funcionario__nome_completo']
    date_hierarchy = 'data_inicio'
    
    fieldsets = (
        ('Funcionário e Período', {
            'fields': ('funcionario', 'data_inicio', 'data_fim')
        }),
        ('Totais', {
            'fields': ('total_dias', 'total_valor')
        }),
        ('Status e Pagamento', {
            'fields': ('status', 'data_pagamento')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )
    
    actions = ['calcular_totais_selecionados']
    
    def calcular_totais_selecionados(self, request, queryset):
        for fechamento in queryset:
            fechamento.calcular_totais()
        self.message_user(request, f"{queryset.count()} fechamento(s) recalculado(s).")
    calcular_totais_selecionados.short_description = "Recalcular totais"
