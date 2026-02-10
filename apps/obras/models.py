from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Obra(models.Model):
    """Model principal para cadastro de obras"""
    
    # Informações básicas
    nome = models.CharField(max_length=200, verbose_name="Nome da Obra")
    endereco = models.TextField(verbose_name="Endereço")
    cliente = models.CharField(max_length=200, verbose_name="Cliente")
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_previsao_termino = models.DateField(
        verbose_name="Previsão de Término",
        null=True,
        blank=True
    )
    
    # Status e progresso
    STATUS_CHOICES = [
        ('planejamento', 'Planejamento'),
        ('em_andamento', 'Em Andamento'),
        ('pausada', 'Pausada'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planejamento',
        verbose_name="Status"
    )
    
    percentual_concluido = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Percentual Concluído (%)"
    )
    
    # Controle
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Obra"
        verbose_name_plural = "Obras"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nome} - {self.cliente}"
    
    def calcular_percentual(self):
        """Calcula percentual baseado nas etapas concluídas"""
        etapas = self.etapas.all()
        if not etapas:
            return Decimal('0.00')
        
        total = Decimal('0.00')
        for etapa in etapas:
            if etapa.concluida:
                total += etapa.percentual_valor
        
        self.percentual_concluido = total
        self.save()
        return total


class Etapa(models.Model):
    """Model para as 5 etapas principais da obra"""
    
    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='etapas',
        verbose_name="Obra"
    )
    
    ETAPA_CHOICES = [
        (1, 'Etapa 1 - Fundação (29.9%)'),
        (2, 'Etapa 2 - Estrutura (45%)'),
        (3, 'Etapa 3 - Revestimentos e Instalações (70%)'),
        (4, 'Etapa 4 - Acabamentos (84%)'),
        (5, 'Etapa 5 - Finalização (95%)'),
    ]
    
    numero_etapa = models.IntegerField(
        choices=ETAPA_CHOICES,
        verbose_name="Número da Etapa"
    )
    
    PERCENTUAIS_ETAPA = {
        1: Decimal('29.9'),
        2: Decimal('45.0'),
        3: Decimal('70.0'),
        4: Decimal('84.0'),
        5: Decimal('95.0'),
    }
    
    percentual_valor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Percentual da Etapa"
    )
    
    data_inicio = models.DateField(null=True, blank=True, verbose_name="Data de Início")
    data_termino = models.DateField(null=True, blank=True, verbose_name="Data de Término")
    concluida = models.BooleanField(default=False, verbose_name="Concluída")
    
    class Meta:
        verbose_name = "Etapa"
        verbose_name_plural = "Etapas"
        ordering = ['numero_etapa']
        unique_together = ['obra', 'numero_etapa']
    
    def __str__(self):
        return f"{self.obra.nome} - {self.get_numero_etapa_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-preenche o percentual baseado no número da etapa
        if not self.percentual_valor:
            self.percentual_valor = self.PERCENTUAIS_ETAPA.get(self.numero_etapa, Decimal('0.00'))
        super().save(*args, **kwargs)


# ========== ETAPA 1 - FUNDAÇÃO (29.9%) ==========

class Etapa1Fundacao(models.Model):
    """Etapa 1: Fundação - 29.9%"""
    
    etapa = models.OneToOneField(
        Etapa,
        on_delete=models.CASCADE,
        related_name='fundacao',
        verbose_name="Etapa"
    )
    
    # Limpeza do Terreno
    limpeza_terreno = models.BooleanField(
        default=False,
        verbose_name="Limpeza do Terreno"
    )
    
    # Instalação de padrão de energia e cavalete d'água
    instalacao_energia_agua = models.BooleanField(
        default=False,
        verbose_name="Instalação de Energia e Água"
    )
    
    # Marcação e Escavação (Dias)
    marcacao_escavacao_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Marcação e Escavação (dias)"
    )
    
    # Locação de Ferragem e concretagem (Dias)
    locacao_ferragem_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Locação de Ferragem (dias)"
    )
    
    # Levantar alicerce, rebocar e impermeabilizar (%)
    alicerce_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Alicerce, Reboco e Impermeabilização (%)"
    )
    
    # Aterrar e fazer o contra piso (Dia)
    aterro_contrapiso_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Aterro e Contrapiso (dias)"
    )
    
    # Parede - 7 fiadas (Unidade de bloco)
    parede_7fiadas_blocos = models.PositiveIntegerField(
        default=0,
        verbose_name="Parede 7 Fiadas (blocos)"
    )
    
    # 8 Fiadas até respaldo (Dia)
    fiadas_respaldo_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="8 Fiadas até Respaldo (dias)"
    )
    
    class Meta:
        verbose_name = "Etapa 1 - Fundação"
        verbose_name_plural = "Etapas 1 - Fundação"
    
    def __str__(self):
        return f"Fundação - {self.etapa.obra.nome}"


# ========== ETAPA 2 - ESTRUTURA (45%) ==========

class Etapa2Estrutura(models.Model):
    """Etapa 2: Estrutura - 45%"""
    
    etapa = models.OneToOneField(
        Etapa,
        on_delete=models.CASCADE,
        related_name='estrutura',
        verbose_name="Etapa"
    )
    
    # Montagem da Laje e Concretagem (Dias)
    montagem_laje_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Montagem da Laje (dias)"
    )
    
    # Platibanda (Unidade de blocos)
    platibanda_blocos = models.PositiveIntegerField(
        default=0,
        verbose_name="Platibanda (blocos)"
    )
    
    # Cobertura completa (Dias)
    cobertura_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Cobertura Completa (dias)"
    )
    
    class Meta:
        verbose_name = "Etapa 2 - Estrutura"
        verbose_name_plural = "Etapas 2 - Estrutura"
    
    def __str__(self):
        return f"Estrutura - {self.etapa.obra.nome}"


# ========== ETAPA 3 - REVESTIMENTOS E INSTALAÇÕES (70%) ==========

class Etapa3Instalacoes(models.Model):
    """Etapa 3: Revestimentos e Instalações - 70%"""
    
    etapa = models.OneToOneField(
        Etapa,
        on_delete=models.CASCADE,
        related_name='instalacoes',
        verbose_name="Etapa"
    )
    
    # Reboco Externo (m2)
    reboco_externo_m2 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Reboco Externo (m²)"
    )
    
    # Reboco Interno (m2)
    reboco_interno_m2 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Reboco Interno (m²)"
    )
    
    # Instalação de Portais
    instalacao_portais = models.BooleanField(
        default=False,
        verbose_name="Instalação de Portais"
    )
    
    # Água Fria
    agua_fria = models.BooleanField(
        default=False,
        verbose_name="Água Fria"
    )
    
    # Esgoto
    esgoto = models.BooleanField(
        default=False,
        verbose_name="Esgoto"
    )
    
    # Fluvial
    fluvial = models.BooleanField(
        default=False,
        verbose_name="Fluvial"
    )
    
    class Meta:
        verbose_name = "Etapa 3 - Instalações"
        verbose_name_plural = "Etapas 3 - Instalações"
    
    def __str__(self):
        return f"Instalações - {self.etapa.obra.nome}"


# ========== ETAPA 4 - ACABAMENTOS (84%) ==========

class Etapa4Acabamentos(models.Model):
    """Etapa 4: Acabamentos - 84%"""
    
    etapa = models.OneToOneField(
        Etapa,
        on_delete=models.CASCADE,
        related_name='acabamentos',
        verbose_name="Etapa"
    )
    
    # Portas e Janelas
    portas_janelas = models.BooleanField(
        default=False,
        verbose_name="Portas e Janelas"
    )
    
    # Pintura Externa 1º demão (dias)
    pintura_externa_1demao_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Pintura Externa 1ª Demão (dias)"
    )
    
    # Pintura Interna 1º demão (dias)
    pintura_interna_1demao_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Pintura Interna 1ª Demão (dias)"
    )
    
    # Assentamento de piso (dias)
    assentamento_piso_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Assentamento de Piso (dias)"
    )
    
    class Meta:
        verbose_name = "Etapa 4 - Acabamentos"
        verbose_name_plural = "Etapas 4 - Acabamentos"
    
    def __str__(self):
        return f"Acabamentos - {self.etapa.obra.nome}"


# ========== ETAPA 5 - FINALIZAÇÃO (95%) ==========

class Etapa5Finalizacao(models.Model):
    """Etapa 5: Finalização - 95%"""
    
    etapa = models.OneToOneField(
        Etapa,
        on_delete=models.CASCADE,
        related_name='finalizacao',
        verbose_name="Etapa"
    )
    
    # Pintura Externa 2º demão (dias)
    pintura_externa_2demao_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Pintura Externa 2ª Demão (dias)"
    )
    
    # Pintura Interna 2º demão (dias)
    pintura_interna_2demao_dias = models.PositiveIntegerField(
        default=0,
        verbose_name="Pintura Interna 2ª Demão (dias)"
    )
    
    # Instalação das Louças e Metais
    loucas_metais = models.BooleanField(
        default=False,
        verbose_name="Louças e Metais"
    )
    
    # Elétrica
    eletrica = models.BooleanField(
        default=False,
        verbose_name="Elétrica"
    )
    
    class Meta:
        verbose_name = "Etapa 5 - Finalização"
        verbose_name_plural = "Etapas 5 - Finalização"
    
    def __str__(self):
        return f"Finalização - {self.etapa.obra.nome}"
