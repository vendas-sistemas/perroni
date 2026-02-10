from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'telefone', 'email', 'ativo')
    search_fields = ('nome', 'cpf', 'email')
    list_filter = ('ativo',)
    readonly_fields = ('created_at', 'updated_at')
