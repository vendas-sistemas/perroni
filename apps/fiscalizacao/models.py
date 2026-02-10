from django.db import models
from django.contrib.auth.models import User
from apps.obras.models import Obra


class RegistroFiscalizacao(models.Model):
    """Registro diário de fiscalização da obra"""
    
    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='fiscalizacoes',
        verbose_name="Obra"
    )
    
    fiscal = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='fiscalizacoes',
        verbose_name="Fiscal"
    )
    
    data_fiscalizacao = models.DateField(verbose_name="Data da Fiscalização")
    
    # Condições da obra
    CLIMA_CHOICES = [
        ('sol', 'Sol'),
        ('chuva', 'Chuva'),
        ('nublado', 'Nublado'),
    ]
    clima = models.CharField(
        max_length=10,
        choices=CLIMA_CHOICES,
        verbose_name="Clima"
    )
    
    # Lixo
    LIXO_CHOICES = [
        ('nao_ha', 'Não há'),
        ('pouco', 'Pouco'),
        ('muito', 'Muito'),
    ]
    lixo = models.CharField(
        max_length=10,
        choices=LIXO_CHOICES,
        default='nao_ha',
        verbose_name="Lixo na Obra"
    )
    
    # Placa instalada
    placa_instalada = models.BooleanField(
        default=False,
        verbose_name="Placa Instalada"
    )
    
    # Ociosidade
    houve_ociosidade = models.BooleanField(
        default=False,
        verbose_name="Houve Ociosidade"
    )
    observacao_ociosidade = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observação sobre Ociosidade"
    )
    
    # Retrabalho
    houve_retrabalho = models.BooleanField(
        default=False,
        verbose_name="Houve Retrabalho"
    )
    motivo_retrabalho = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo do Retrabalho"
    )
    
    # Observações gerais
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações Gerais"
    )
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Registro de Fiscalização"
        verbose_name_plural = "Registros de Fiscalização"
        ordering = ['-data_fiscalizacao', '-created_at']
        unique_together = ['obra', 'data_fiscalizacao']
    
    def __str__(self):
        return f"{self.obra.nome} - {self.data_fiscalizacao.strftime('%d/%m/%Y')}"
    
    def validar_fotos(self):
        """Verifica se há pelo menos 6 fotos"""
        return self.fotos.count() >= 6


class FotoFiscalizacao(models.Model):
    """Fotos da fiscalização (mínimo 6 por registro)"""
    
    fiscalizacao = models.ForeignKey(
        RegistroFiscalizacao,
        on_delete=models.CASCADE,
        related_name='fotos',
        verbose_name="Fiscalização"
    )
    
    foto = models.ImageField(
        upload_to='fiscalizacao/%Y/%m/%d/',
        verbose_name="Foto"
    )
    
    descricao = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Descrição"
    )
    
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem"
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Enviado em"
    )
    
    class Meta:
        verbose_name = "Foto de Fiscalização"
        verbose_name_plural = "Fotos de Fiscalização"
        ordering = ['ordem', 'uploaded_at']
    
    def __str__(self):
        return f"Foto {self.ordem} - {self.fiscalizacao}"
