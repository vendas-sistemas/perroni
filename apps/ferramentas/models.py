from django.db import models
from django.contrib.auth.models import User
from apps.obras.models import Obra


class Ferramenta(models.Model):
    """Cadastro de ferramentas da empresa"""
    
    # Identificação
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código"
    )
    nome = models.CharField(max_length=200, verbose_name="Nome")
    descricao = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descrição"
    )
    
    # Categoria
    CATEGORIA_CHOICES = [
        ('manual', 'Ferramenta Manual'),
        ('eletrica', 'Ferramenta Elétrica'),
        ('medicao', 'Instrumento de Medição'),
        ('seguranca', 'EPI/Segurança'),
        ('outros', 'Outros'),
    ]
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        verbose_name="Categoria"
    )
    
    # Status
    STATUS_CHOICES = [
        ('deposito', 'No Depósito'),
        ('em_obra', 'Em Obra'),
        ('manutencao', 'Em Manutenção'),
        ('perdida', 'Perdida'),
        ('descartada', 'Descartada'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='deposito',
        verbose_name="Status"
    )
    
    # Localização atual
    obra_atual = models.ForeignKey(
        Obra,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ferramentas_alocadas',
        verbose_name="Obra Atual"
    )
    
    # Informações adicionais
    data_aquisicao = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data de Aquisição"
    )
    valor_aquisicao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Valor de Aquisição (R$)"
    )
    
    # Foto
    foto = models.ImageField(
        upload_to='ferramentas/fotos/',
        blank=True,
        null=True,
        verbose_name="Foto"
    )
    
    # Controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Ferramenta"
        verbose_name_plural = "Ferramentas"
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class MovimentacaoFerramenta(models.Model):
    """Histórico de movimentação de ferramentas"""
    
    ferramenta = models.ForeignKey(
        Ferramenta,
        on_delete=models.CASCADE,
        related_name='movimentacoes',
        verbose_name="Ferramenta"
    )
    
    data_movimentacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Movimentação"
    )
    
    # Tipo de movimentação
    TIPO_CHOICES = [
        ('entrada_deposito', 'Entrada no Depósito'),
        ('saida_obra', 'Saída para Obra'),
        ('transferencia', 'Transferência entre Obras'),
        ('retorno_deposito', 'Retorno ao Depósito'),
        ('manutencao', 'Envio para Manutenção'),
        ('retorno_manutencao', 'Retorno de Manutenção'),
        ('perda', 'Perda/Extravio'),
        ('descarte', 'Descarte'),
    ]
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Movimentação"
    )
    
    # Origem e Destino
    origem = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Origem"
    )
    obra_origem = models.ForeignKey(
        Obra,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_saida',
        verbose_name="Obra Origem"
    )
    
    destino = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Destino"
    )
    obra_destino = models.ForeignKey(
        Obra,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_entrada',
        verbose_name="Obra Destino"
    )
    
    # Responsável
    responsavel = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='movimentacoes_ferramenta',
        verbose_name="Responsável"
    )
    
    # Observações
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    
    class Meta:
        verbose_name = "Movimentação de Ferramenta"
        verbose_name_plural = "Movimentações de Ferramentas"
        ordering = ['-data_movimentacao']
    
    def __str__(self):
        return f"{self.ferramenta.codigo} - {self.get_tipo_display()} - {self.data_movimentacao.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Atualiza o status e localização da ferramenta
        self.atualizar_ferramenta()
    
    def atualizar_ferramenta(self):
        """Atualiza o status e localização da ferramenta baseado na movimentação"""
        ferramenta = self.ferramenta
        
        if self.tipo in ['entrada_deposito', 'retorno_deposito', 'retorno_manutencao']:
            ferramenta.status = 'deposito'
            ferramenta.obra_atual = None
        
        elif self.tipo in ['saida_obra', 'transferencia']:
            ferramenta.status = 'em_obra'
            ferramenta.obra_atual = self.obra_destino
        
        elif self.tipo == 'manutencao':
            ferramenta.status = 'manutencao'
        
        elif self.tipo == 'perda':
            ferramenta.status = 'perdida'
            ferramenta.ativo = False
        
        elif self.tipo == 'descarte':
            ferramenta.status = 'descartada'
            ferramenta.ativo = False
        
        ferramenta.save()


class ConferenciaFerramenta(models.Model):
    """Conferência diária de ferramentas pelo fiscal"""
    
    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='conferencias_ferramentas',
        verbose_name="Obra"
    )
    
    fiscal = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='conferencias_ferramentas',
        verbose_name="Fiscal"
    )
    
    data_conferencia = models.DateField(verbose_name="Data da Conferência")
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Conferência de Ferramenta"
        verbose_name_plural = "Conferências de Ferramentas"
        ordering = ['-data_conferencia']
        unique_together = ['obra', 'data_conferencia']
    
    def __str__(self):
        return f"Conferência {self.obra.nome} - {self.data_conferencia.strftime('%d/%m/%Y')}"


class ItemConferencia(models.Model):
    """Itens conferidos em cada conferência"""
    
    conferencia = models.ForeignKey(
        ConferenciaFerramenta,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Conferência"
    )
    
    ferramenta = models.ForeignKey(
        Ferramenta,
        on_delete=models.PROTECT,
        related_name='conferencias',
        verbose_name="Ferramenta"
    )
    
    # Status da conferência
    STATUS_CHOICES = [
        ('ok', 'OK - Presente'),
        ('ausente', 'Ausente'),
        ('danificada', 'Danificada'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="Status"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    
    class Meta:
        verbose_name = "Item de Conferência"
        verbose_name_plural = "Itens de Conferência"
        unique_together = ['conferencia', 'ferramenta']
    
    def __str__(self):
        return f"{self.ferramenta.codigo} - {self.get_status_display()}"
