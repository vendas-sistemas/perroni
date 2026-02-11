from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.obras.models import Obra, Etapa


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
    
    etapa = models.ForeignKey(
        Etapa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='apontamentos',
        verbose_name="Etapa/Fase"
    )
    
    data = models.DateField(verbose_name="Data")
    
    # Horas trabalhadas
    horas_trabalhadas = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal('8.0'),
        validators=[MinValueValidator(Decimal('0.5')), MaxValueValidator(Decimal('24.0'))],
        verbose_name="Horas Trabalhadas"
    )
    
    # Condições do dia
    CLIMA_CHOICES = [
        ('sol', 'Sol'),
        ('chuva', 'Chuva'),
        ('nublado', 'Nublado'),
    ]
    clima = models.CharField(
        max_length=10,
        choices=CLIMA_CHOICES,
        default='sol',
        verbose_name="Clima"
    )
    
    # Ociosidade
    houve_ociosidade = models.BooleanField(
        default=False,
        verbose_name="Houve Ociosidade"
    )
    observacao_ociosidade = models.TextField(
        blank=True,
        null=True,
        verbose_name="Justificativa da Ociosidade"
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
        # Nota: removido unique_together para permitir múltiplos apontamentos
        # por funcionário na mesma data (mesma obra pode ter vários registros).
    
    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.obra.nome} - {self.data.strftime('%d/%m/%Y')}"
    
    def save(self, *args, **kwargs):
        # Auto-preenche valor da diária se não foi informado
        if not self.valor_diaria:
            self.valor_diaria = self.funcionario.valor_diaria
        super().save(*args, **kwargs)
    
    @property
    def valor_proporcional(self):
        """Calcula valor proporcional baseado nas horas trabalhadas (base 8h)"""
        if self.horas_trabalhadas and self.valor_diaria:
            return (self.valor_diaria * self.horas_trabalhadas / Decimal('8.0')).quantize(Decimal('0.01'))
        return self.valor_diaria


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
    total_horas = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=Decimal('0.0'),
        verbose_name="Total de Horas"
    )
    total_valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total a Pagar (R$)"
    )
    
    # Indicadores
    dias_ociosidade = models.PositiveIntegerField(default=0, verbose_name="Dias com Ociosidade")
    dias_retrabalho = models.PositiveIntegerField(default=0, verbose_name="Dias com Retrabalho")
    
    # Status
    STATUS_CHOICES = [
        ('fechado', 'Fechado'),
        ('pago', 'Pago'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='fechado',
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
        
        # Count distinct days (one diária per date), not number of rows
        self.total_dias = apontamentos.values('data').distinct().count()
        self.total_horas = sum(a.horas_trabalhadas for a in apontamentos) or Decimal('0.0')
        self.total_valor = sum(a.valor_proporcional for a in apontamentos) or Decimal('0.00')
        # Count distinct dates where there was ociosidade / retrabalho
        self.dias_ociosidade = apontamentos.filter(houve_ociosidade=True).values('data').distinct().count()
        self.dias_retrabalho = apontamentos.filter(houve_retrabalho=True).values('data').distinct().count()
        self.save()
        
        return {
            'dias': self.total_dias,
            'horas': self.total_horas,
            'valor': self.total_valor,
            'dias_ociosidade': self.dias_ociosidade,
            'dias_retrabalho': self.dias_retrabalho,
        }
    
    def get_apontamentos(self):
        """Retorna apontamentos do período"""
        return ApontamentoFuncionario.objects.filter(
            funcionario=self.funcionario,
            data__gte=self.data_inicio,
            data__lte=self.data_fim
        ).select_related('obra', 'etapa').order_by('data')
    
    def get_obras_etapas(self):
        """Retorna obras e etapas em que o funcionário atuou na semana"""
        apontamentos = self.get_apontamentos()
        obras_etapas = {}
        seen_days = set()  # track (obra, data) to count one diária per day
        for a in apontamentos:
            key = a.obra.nome
            if key not in obras_etapas:
                obras_etapas[key] = {'dias': 0, 'horas': Decimal('0.0'), 'etapas': set()}
            day_key = (key, a.data)
            if day_key not in seen_days:
                obras_etapas[key]['dias'] += 1
                obras_etapas[key]['horas'] += a.horas_trabalhadas
                seen_days.add(day_key)
            if a.etapa:
                obras_etapas[key]['etapas'].add(a.etapa.get_numero_etapa_display())
        return obras_etapas


# ----------------- User profile for preferences -----------------
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Per-user preferences (e.g., theme)."""
    USER_THEME_CHOICES = [
        ('light', 'Claro'),
        ('dark', 'Escuro'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    theme_preference = models.CharField(max_length=10, choices=USER_THEME_CHOICES, default='light')
    # Theme variant provides alternate palettes for the dark theme
    THEME_VARIANT_CHOICES = [
        ('default', 'Padrão'),
        ('soft', 'Suave'),
        ('gray', 'Cinza'),
        ('blue', 'Azulado'),
    ]
    theme_variant = models.CharField(max_length=20, choices=THEME_VARIANT_CHOICES, default='default')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
