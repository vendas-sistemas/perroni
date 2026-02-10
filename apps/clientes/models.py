from django.db import models
from django.core.validators import RegexValidator


class Cliente(models.Model):
    """Cadastro de clientes (pessoas físicas)."""

    nome = models.CharField(max_length=200, verbose_name='Nome')
    cpf = models.CharField(
        max_length=14,
        unique=True,
        verbose_name='CPF',
        help_text='Somente números ou formatado (000.000.000-00)',
        validators=[RegexValidator(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{11}$', 'CPF inválido')]
    )
    endereco = models.TextField(verbose_name='Endereço', blank=True, null=True)
    data_nascimento = models.DateField(verbose_name='Data de Nascimento', blank=True, null=True)
    telefone = models.CharField(max_length=30, verbose_name='Telefone', blank=True, null=True)
    email = models.EmailField(verbose_name='E-mail', blank=True, null=True)

    # Controle
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.cpf}"
