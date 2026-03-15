from django.contrib import admin

from .models import Fornecedor


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'ativo', 'updated_at')
    list_filter = ('ativo',)
    search_fields = ('nome', 'telefone', 'endereco')

