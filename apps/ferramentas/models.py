from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models import Sum, F, Q
from django.db import transaction
from apps.obras.models import Obra
from decimal import Decimal


class Ferramenta(models.Model):
    """
    Representa um TIPO/MODELO de ferramenta (não unidade individual).
    Exemplo: "Alicate de Pressão 10 polegadas" com 20 unidades no estoque.
    """
    
    # Identificação
    codigo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código"
    )
    nome = models.CharField(
        max_length=200,
        verbose_name="Nome do Modelo"
    )
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
    
    # Quantidade e Valor
    quantidade_total = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Quantidade Total no Estoque",
        help_text="Total de unidades existentes (soma de todas localizações)"
    )
    
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Valor Unitário (R$)",
        help_text="Preço de uma unidade"
    )
    
    # Informações adicionais
    data_aquisicao = models.DateField(
        blank=True,
        null=True,
        verbose_name="Data da Primeira Aquisição"
    )
    
    foto = models.ImageField(
        upload_to='ferramentas/fotos/',
        blank=True,
        null=True,
        verbose_name="Foto do Modelo"
    )
    
    # Controle
    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Define se a ferramenta está ativa; itens inativos podem ser exibidos via filtro na listagem"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Ferramenta"
        verbose_name_plural = "Ferramentas"
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome} ({self.quantidade_total} un.)"
    
    # ========== PROPERTIES PARA QUANTIDADES POR LOCALIZAÇÃO ==========
    
    @property
    def quantidade_deposito(self):
        """Retorna quantidade no depósito"""
        loc = self.localizacoes.filter(local_tipo='deposito').first()
        return loc.quantidade if loc else 0
    
    @property
    def quantidade_em_obras(self):
        """Retorna soma das quantidades em todas as obras"""
        return self.localizacoes.filter(
            local_tipo='obra'
        ).aggregate(
            total=Sum('quantidade')
        )['total'] or 0
    
    @property
    def quantidade_manutencao(self):
        """Retorna quantidade em manutenção"""
        loc = self.localizacoes.filter(local_tipo='manutencao').first()
        return loc.quantidade if loc else 0
    
    @property
    def quantidade_perdida(self):
        """Retorna quantidade perdida/extraviada"""
        loc = self.localizacoes.filter(local_tipo='perdida').first()
        return loc.quantidade if loc else 0
    
    @property
    def valor_total_estoque(self):
        """Retorna valor total do estoque (quantidade × valor unitário)"""
        if self.valor_unitario:
            return self.quantidade_total * self.valor_unitario
        return Decimal('0.00')
    
    @property
    def status_estoque(self):
        """Retorna status visual do estoque"""
        if self.quantidade_total == 0:
            return 'esgotado'
        elif self.quantidade_total < 5:
            return 'critico'
        elif self.quantidade_total < 10:
            return 'baixo'
        return 'ok'
    
    def get_distribuicao_completa(self):
        """
        Retorna distribuição completa das quantidades.
        
        Returns:
            dict: {
                'deposito': 10,
                'obras': [{'obra': Obra, 'quantidade': 5}, ...],
                'manutencao': 2,
                'perdida': 1,
                'total': 18
            }
        """
        distribuicao = {
            'deposito': self.quantidade_deposito,
            'obras': [],
            'manutencao': self.quantidade_manutencao,
            'perdida': self.quantidade_perdida,
            'total': self.quantidade_total
        }
        
        # Listar obras com quantidades
        obras_loc = self.localizacoes.filter(
            local_tipo='obra'
        ).select_related('obra')
        
        for loc in obras_loc:
            distribuicao['obras'].append({
                'obra': loc.obra,
                'quantidade': loc.quantidade
            })
        
        return distribuicao
    
    def verificar_consistencia(self):
        """
        Verifica se a soma das localizações bate com quantidade_total.
        
        Returns:
            tuple: (bool, str) - (está_ok, mensagem)
        """
        soma_localizacoes = self.localizacoes.aggregate(
            total=Sum('quantidade')
        )['total'] or 0
        
        if soma_localizacoes != self.quantidade_total:
            return (
                False,
                f"INCONSISTÊNCIA: Total={self.quantidade_total}, "
                f"Soma localizações={soma_localizacoes}"
            )
        return (True, "Estoque consistente")


class LocalizacaoFerramenta(models.Model):
    """
    Representa ONDE estão as quantidades de uma ferramenta.
    Distribui o estoque total entre depósito, obras, manutenção, etc.
    """
    
    ferramenta = models.ForeignKey(
        Ferramenta,
        on_delete=models.CASCADE,
        related_name='localizacoes',
        verbose_name="Ferramenta"
    )
    
    LOCAL_TIPO_CHOICES = [
        ('deposito', 'Depósito'),
        ('obra', 'Em Obra'),
        ('manutencao', 'Manutenção'),
        ('perdida', 'Perdida/Extraviada'),
    ]
    local_tipo = models.CharField(
        max_length=20,
        choices=LOCAL_TIPO_CHOICES,
        verbose_name="Tipo de Local"
    )
    
    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ferramentas_localizadas',
        verbose_name="Obra",
        help_text="Obrigatório apenas se local_tipo='obra'"
    )
    
    quantidade = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Quantidade",
        help_text="Quantas unidades estão neste local"
    )
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Localização de Ferramenta"
        verbose_name_plural = "Localizações de Ferramentas"
        
        # Constraints para evitar duplicatas
        constraints = [
            # Não pode ter duas entradas "deposito" para mesma ferramenta
            models.UniqueConstraint(
                fields=['ferramenta', 'local_tipo'],
                condition=Q(obra__isnull=True),
                name='unique_ferramenta_local_nao_obra'
            ),
            # Não pode ter duas entradas para mesma ferramenta+obra
            models.UniqueConstraint(
                fields=['ferramenta', 'obra'],
                condition=Q(local_tipo='obra'),
                name='unique_ferramenta_obra'
            ),
        ]
    
    def __str__(self):
        if self.local_tipo == 'obra' and self.obra:
            return f"{self.ferramenta.codigo} - {self.obra.nome}: {self.quantidade} un."
        return f"{self.ferramenta.codigo} - {self.get_local_tipo_display()}: {self.quantidade} un."
    
    def clean(self):
        """Validação customizada"""
        from django.core.exceptions import ValidationError
        
        # Se tipo é 'obra', obra é OBRIGATÓRIA
        if self.local_tipo == 'obra' and not self.obra:
            raise ValidationError({
                'obra': 'Obra é obrigatória quando tipo de local é "Em Obra"'
            })
        
        # Se tipo NÃO é 'obra', obra deve ser NULL
        if self.local_tipo != 'obra' and self.obra:
            raise ValidationError({
                'obra': 'Obra só deve ser preenchida quando tipo de local é "Em Obra"'
            })
        
        # Quantidade não pode ser negativa
        if self.quantidade < 0:
            raise ValidationError({
                'quantidade': 'Quantidade não pode ser negativa'
            })
    
    def save(self, *args, **kwargs):
        """
        Limpa obra se necessário e remove registro se quantidade = 0
        """
        # Verificar se quantidade é uma expressão F() ou valor real
        from django.db.models.expressions import CombinedExpression
        is_expression = isinstance(self.quantidade, CombinedExpression)
        
        # Validar apenas se não for expressão F()
        if not is_expression:
            self.full_clean()
        
        # Se local_tipo != 'obra', garantir que obra é None
        if self.local_tipo != 'obra':
            self.obra = None
        
        # Se quantidade chegou a zero, deletar ao invés de salvar
        # (só verifica se não for expressão F())
        if not is_expression and self.quantidade == 0:
            if self.pk:  # Só deleta se já existe
                self.delete()
            return
        
        super().save(*args, **kwargs)


class MovimentacaoFerramenta(models.Model):
    """
    Registra movimentações de QUANTIDADES de ferramentas.
    Atualiza automaticamente as LocalizacaoFerramenta ao salvar.
    """
    
    ferramenta = models.ForeignKey(
        Ferramenta,
        on_delete=models.CASCADE,
        related_name='movimentacoes',
        verbose_name="Ferramenta"
    )
    
    quantidade = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Quantidade",
        help_text="Quantas unidades estão sendo movimentadas",
        default=1
    )
    
    data_movimentacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Movimentação"
    )
    
    # Tipo de movimentação
    TIPO_CHOICES = [
        ('entrada_deposito', 'Entrada no Depósito (Compra/Recebimento)'),
        ('saida_obra', 'Saída para Obra'),
        ('transferencia', 'Transferência entre Obras'),
        ('retorno_deposito', 'Retorno ao Depósito'),
        ('envio_manutencao', 'Envio para Manutenção'),
        ('retorno_manutencao', 'Retorno de Manutenção'),
        ('perda', 'Perda/Extravio'),
        ('descarte', 'Descarte/Baixa'),
    ]
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Movimentação"
    )
    
    # Origem
    origem_tipo = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Tipo de Origem"
    )
    obra_origem = models.ForeignKey(
        Obra,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_saida_ferramenta',
        verbose_name="Obra Origem"
    )
    
    # Destino
    destino_tipo = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Tipo de Destino"
    )
    obra_destino = models.ForeignKey(
        Obra,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_entrada_ferramenta',
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
        return (
            f"{self.ferramenta.codigo} - {self.quantidade} un. - "
            f"{self.get_tipo_display()} - "
            f"{self.data_movimentacao.strftime('%d/%m/%Y %H:%M')}"
        )
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Salva a movimentação E atualiza as localizações automaticamente.
        Usa transaction.atomic para garantir consistência.
        """
        is_new = self.pk is None
        
        # Salvar o registro primeiro
        super().save(*args, **kwargs)
        
        # Atualizar localizações apenas se é novo registro
        if is_new:
            self.atualizar_localizacoes()
    
    def atualizar_localizacoes(self):
        """
        Atualiza LocalizacaoFerramenta baseado no tipo de movimentação.
        CRÍTICO: Usa F() expressions para evitar race conditions.
        """
        ferramenta = self.ferramenta
        quantidade = self.quantidade
        
        # ========== ENTRADA NO DEPÓSITO ==========
        if self.tipo == 'entrada_deposito':
            # Adicionar no depósito
            self._adicionar_em_localizacao('deposito', None, quantidade)
            # Aumentar quantidade total
            ferramenta.quantidade_total = F('quantidade_total') + quantidade
            ferramenta.save(update_fields=['quantidade_total'])
            ferramenta.refresh_from_db()
        
        # ========== SAÍDA PARA OBRA ==========
        elif self.tipo == 'saida_obra':
            # Remover do depósito
            self._remover_de_localizacao('deposito', None, quantidade)
            # Adicionar na obra destino
            self._adicionar_em_localizacao('obra', self.obra_destino, quantidade)
        
        # ========== TRANSFERÊNCIA ENTRE OBRAS ==========
        elif self.tipo == 'transferencia':
            # Remover da obra origem
            self._remover_de_localizacao('obra', self.obra_origem, quantidade)
            # Adicionar na obra destino
            self._adicionar_em_localizacao('obra', self.obra_destino, quantidade)
        
        # ========== RETORNO AO DEPÓSITO ==========
        elif self.tipo == 'retorno_deposito':
            # Remover da obra origem
            self._remover_de_localizacao('obra', self.obra_origem, quantidade)
            # Adicionar no depósito
            self._adicionar_em_localizacao('deposito', None, quantidade)
        
        # ========== ENVIO PARA MANUTENÇÃO ==========
        elif self.tipo == 'envio_manutencao':
            # Remover do local de origem (depósito ou obra)
            if self.obra_origem:
                self._remover_de_localizacao('obra', self.obra_origem, quantidade)
            else:
                self._remover_de_localizacao('deposito', None, quantidade)
            # Adicionar em manutenção
            self._adicionar_em_localizacao('manutencao', None, quantidade)
        
        # ========== RETORNO DE MANUTENÇÃO ==========
        elif self.tipo == 'retorno_manutencao':
            # Remover de manutenção
            self._remover_de_localizacao('manutencao', None, quantidade)
            # Adicionar no depósito
            self._adicionar_em_localizacao('deposito', None, quantidade)
        
        # ========== PERDA/EXTRAVIO ==========
        elif self.tipo == 'perda':
            # Remover do local de origem
            if self.obra_origem:
                self._remover_de_localizacao('obra', self.obra_origem, quantidade)
            else:
                self._remover_de_localizacao('deposito', None, quantidade)
            # Adicionar em perdidas
            self._adicionar_em_localizacao('perdida', None, quantidade)
        
        # ========== DESCARTE ==========
        elif self.tipo == 'descarte':
            # Remover do local de origem
            if self.obra_origem:
                self._remover_de_localizacao('obra', self.obra_origem, quantidade)
            else:
                self._remover_de_localizacao('deposito', None, quantidade)
            # REDUZIR quantidade total (descarte remove do estoque)
            ferramenta.quantidade_total = F('quantidade_total') - quantidade
            ferramenta.save(update_fields=['quantidade_total'])
            ferramenta.refresh_from_db()
    
    def _adicionar_em_localizacao(self, local_tipo, obra, quantidade):
        """
        Adiciona quantidade em uma localização.
        Cria se não existe, incrementa se existe.
        """
        filtro = {'ferramenta': self.ferramenta, 'local_tipo': local_tipo}
        if local_tipo == 'obra':
            filtro['obra'] = obra
        
        loc, created = LocalizacaoFerramenta.objects.get_or_create(
            **filtro,
            defaults={'quantidade': quantidade}
        )
        
        if not created:
            # Já existe, incrementar usando update() com F()
            LocalizacaoFerramenta.objects.filter(pk=loc.pk).update(
                quantidade=F('quantidade') + quantidade
            )
    
    def _remover_de_localizacao(self, local_tipo, obra, quantidade):
        """
        Remove quantidade de uma localização.
        Deleta se quantidade chegar a zero ou ficar negativa.
        """
        filtro = {'ferramenta': self.ferramenta, 'local_tipo': local_tipo}
        if local_tipo == 'obra':
            filtro['obra'] = obra
        
        try:
            loc = LocalizacaoFerramenta.objects.get(**filtro)
            
            # Usar update() direto com F() para evitar race conditions
            LocalizacaoFerramenta.objects.filter(pk=loc.pk).update(
                quantidade=F('quantidade') - quantidade
            )
            
            # Recarregar para verificar o valor atualizado
            loc.refresh_from_db()
            if loc.quantidade <= 0:
                loc.delete()
        
        except LocalizacaoFerramenta.DoesNotExist:
            # Não deveria acontecer, mas não quebrar
            pass


class ConferenciaFerramenta(models.Model):
    """
    Conferência diária de ferramentas em uma obra.
    Registra quantidades esperadas vs encontradas.
    """
    
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
    
    data_conferencia = models.DateTimeField(
        verbose_name="Data e Hora da Conferência"
    )
    
    observacoes_gerais = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações Gerais"
    )
    
    # Controle
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Conferência de Ferramenta"
        verbose_name_plural = "Conferências de Ferramentas"
        ordering = ['-data_conferencia']
    
    def __str__(self):
        return (
            f"Conferência {self.obra.nome} - "
            f"{self.data_conferencia.strftime('%d/%m/%Y')}"
        )
    
    @property
    def total_itens(self):
        """Total de itens conferidos"""
        return self.itens.count()
    
    @property
    def total_divergencias(self):
        """Total de itens com divergência (falta ou sobra)"""
        return self.itens.exclude(status='ok').count()
    
    @property
    def tem_divergencias(self):
        """Retorna True se há alguma divergência"""
        return self.total_divergencias > 0


class ItemConferencia(models.Model):
    """
    Item conferido: compara quantidade esperada vs encontrada.
    Status é calculado automaticamente.
    """
    
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
    
    quantidade_esperada = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Quantidade Esperada",
        help_text="Quantidade que deveria estar na obra segundo o sistema"
    )
    
    quantidade_encontrada = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Quantidade Encontrada",
        help_text="Quantidade realmente encontrada na conferência"
    )
    
    STATUS_CHOICES = [
        ('ok', 'OK - Bate'),
        ('falta', 'Falta'),
        ('sobra', 'Sobra'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ok',
        verbose_name="Status",
        help_text="Calculado automaticamente"
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
        return (
            f"{self.ferramenta.codigo} - {self.get_status_display()} "
            f"(Esp: {self.quantidade_esperada}, Enc: {self.quantidade_encontrada})"
        )
    
    @property
    def diferenca(self):
        """Retorna diferença: positivo = sobra, negativo = falta"""
        return self.quantidade_encontrada - self.quantidade_esperada
    
    def save(self, *args, **kwargs):
        """Auto-calcula o status antes de salvar"""
        # Calcular status
        if self.quantidade_encontrada == self.quantidade_esperada:
            self.status = 'ok'
        elif self.quantidade_encontrada < self.quantidade_esperada:
            self.status = 'falta'
        else:  # encontrada > esperada
            self.status = 'sobra'
        
        super().save(*args, **kwargs)
