from django.db import models


class Fornecedor(models.Model):
    nome = models.CharField(max_length=200, verbose_name='Nome')
    endereco = models.TextField(blank=True, null=True, verbose_name='Endereço')
    telefone = models.CharField(max_length=30, blank=True, null=True, verbose_name='Telefone')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['nome']

    def __str__(self):
        return self.nome

