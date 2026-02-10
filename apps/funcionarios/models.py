from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.obras.models import Obra


class Funcionario(models.Model):
    """Cadastro de pedreiros e serventes"""
    
    # Dados pessoais
    nome_completo = models.CharField(max_length=200, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    rg = models.CharField(max_length=20, blank=True, null=True, verbose_name="RG")
    data_nascimento = models.DateField(verbose_name="Data de Nascimento")
    
    # Contato
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    
    # Endereço
    endereco = models.TextField(verbose_name="Endereço")
    cidade = models.CharField(max_length=100, verbose_name="Cidade")
    estado = models.CharField(max_length=2, verbose_name="Estado")
    cep = models.CharField(max_length=9, verbose_name="CEP")
    
    # Função
    FUNCAO_CHOICES = [
        ('pedreiro', 'Pedreiro'),
        ('servente', 'Servente'),
    ]
    funcao = models.CharField(
        max_length=10,
        choices=FUNCAO_CHOICES,
        verbose_name="Função"
    )
    
    # Valores
    valor_diaria = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Valor da Diária (R$)"
    )
    
    # Foto
    foto = models.ImageField(
        upload_to='funcionarios/fotos/',
        blank=True,
        null=True,
        verbose_name="Foto"
    )
    
    # Status
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    data_admissao = models.DateField(verbose_name="Data de Admissão")
    data_demissao = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Demissão"
    )
    motivo_inativacao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo da Inativação"
    )
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ['nome_completo']
    
    def __str__(self):
        return f"{self.nome_completo} - {self.get_funcao_display()}"
    
    def inativar(self, motivo):
        """Inativa o funcionário"""
        from django.utils import timezone
        self.ativo = False
        self.data_demissao = timezone.now().date()
        self.motivo_inativacao = motivo
        self.save()


class ApontamentoFuncionario(models.Model):
    """Apontamento diário de funcionários nas obras"""
    
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        related_name='apontamentos',
        verbose_name="Funcionário"
    )
    
    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='apontamentos_funcionarios',
        verbose_name="Obra"
    )
    
    data = models.DateField(verbose_name="Data")
    
    # Valores
    valor_diaria = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Valor da Diária (R$)"
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Apontamento de Funcionário"
        verbose_name_plural = "Apontamentos de Funcionários"
        ordering = ['-data']
        unique_together = ['funcionario', 'obra', 'data']
    
    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.obra.nome} - {self.data.strftime('%d/%m/%Y')}"
    
    def save(self, *args, **kwargs):
        # Auto-preenche valor da diária se não foi informado
        if not self.valor_diaria:
            self.valor_diaria = self.funcionario.valor_diaria
        super().save(*args, **kwargs)


class FechamentoSemanal(models.Model):
    """Fechamento semanal de pagamento de funcionários"""
    
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        related_name='fechamentos',
        verbose_name="Funcionário"
    )
    
    data_inicio = models.DateField(verbose_name="Data Início da Semana")
    data_fim = models.DateField(verbose_name="Data Fim da Semana")
    
    # Totais
    total_dias = models.PositiveIntegerField(default=0, verbose_name="Total de Dias")
    total_valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total a Pagar (R$)"
    )
    
    # Status
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('fechado', 'Fechado'),
        ('pago', 'Pago'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='aberto',
        verbose_name="Status"
    )
    
    data_pagamento = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data do Pagamento"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Fechamento Semanal"
        verbose_name_plural = "Fechamentos Semanais"
        ordering = ['-data_inicio']
        unique_together = ['funcionario', 'data_inicio', 'data_fim']
    
    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.data_inicio.strftime('%d/%m/%Y')} a {self.data_fim.strftime('%d/%m/%Y')}"
    
    def calcular_totais(self):
        """Calcula os totais baseado nos apontamentos da semana"""
        apontamentos = ApontamentoFuncionario.objects.filter(
            funcionario=self.funcionario,
            data__gte=self.data_inicio,
            data__lte=self.data_fim
        )
        
        self.total_dias = apontamentos.count()
        self.total_valor = sum(a.valor_diaria for a in apontamentos)
        self.save()
        
        return {
            'dias': self.total_dias,
            'valor': self.total_valor
        }
