from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Q, Sum

from apps.fornecedores.models import Fornecedor
from apps.obras.models import Obra


class Ferramenta(models.Model):
    """Representa um tipo/modelo de ferramenta."""

    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código')
    nome = models.CharField(max_length=200, verbose_name='Nome do Modelo')
    descricao = models.TextField(blank=True, null=True, verbose_name='Descrição')

    CATEGORIA_CHOICES = [
        ('manual', 'Ferramenta Manual'),
        ('eletrica', 'Ferramenta Elétrica'),
        ('medicao', 'Instrumento de Medição'),
        ('seguranca', 'EPI/Segurança'),
        ('outros', 'Outros'),
    ]
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, verbose_name='Categoria')

    CLASSIFICACAO_CHOICES = [
        ('propria', 'Patrimônio Próprio'),
        ('alugada', 'Alugada'),
    ]
    classificacao = models.CharField(max_length=20, choices=CLASSIFICACAO_CHOICES, verbose_name='Classificação')
    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ferramentas',
        verbose_name='Fornecedor',
    )

    quantidade_total = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Quantidade Total no Estoque',
        help_text='Total de unidades existentes (soma de todas localizações)',
    )
    valor_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor Unitário (R$)',
        help_text='Preço de uma unidade',
    )
    data_aquisicao = models.DateField(blank=True, null=True, verbose_name='Data da Primeira Aquisição')
    foto = models.ImageField(upload_to='ferramentas/fotos/', blank=True, null=True, verbose_name='Foto do Modelo')

    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Define se a ferramenta está ativa; itens inativos podem ser exibidos via filtro na listagem',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Ferramenta'
        verbose_name_plural = 'Ferramentas'
        ordering = ['nome']

    def __str__(self):
        return f'{self.codigo} - {self.nome} ({self.quantidade_total} un.)'

    @property
    def eh_alugada(self):
        return self.classificacao == 'alugada'

    @property
    def quantidade_deposito(self):
        loc = self.localizacoes.filter(local_tipo='deposito').first()
        return loc.quantidade if loc else 0

    @property
    def quantidade_em_obras(self):
        return self.localizacoes.filter(local_tipo='obra').aggregate(total=Sum('quantidade'))['total'] or 0

    @property
    def quantidade_manutencao(self):
        loc = self.localizacoes.filter(local_tipo='manutencao').first()
        return loc.quantidade if loc else 0

    @property
    def quantidade_perdida(self):
        loc = self.localizacoes.filter(local_tipo='perdida').first()
        return loc.quantidade if loc else 0

    @property
    def valor_total_estoque(self):
        if self.valor_unitario:
            return self.quantidade_total * self.valor_unitario
        return Decimal('0.00')

    @property
    def status_estoque(self):
        if self.quantidade_total == 0:
            return 'esgotado'
        if self.quantidade_total < 5:
            return 'critico'
        if self.quantidade_total < 10:
            return 'baixo'
        return 'ok'

    def get_distribuicao_completa(self):
        distribuicao = {
            'deposito': self.quantidade_deposito,
            'obras': [],
            'manutencao': self.quantidade_manutencao,
            'perdida': self.quantidade_perdida,
            'total': self.quantidade_total,
        }

        for loc in self.localizacoes.filter(local_tipo='obra').select_related('obra'):
            distribuicao['obras'].append({'obra': loc.obra, 'quantidade': loc.quantidade})

        return distribuicao

    def verificar_consistencia(self):
        soma_localizacoes = self.localizacoes.aggregate(total=Sum('quantidade'))['total'] or 0
        if soma_localizacoes != self.quantidade_total:
            return False, f'INCONSISTÊNCIA: Total={self.quantidade_total}, Soma localizações={soma_localizacoes}'
        return True, 'Estoque consistente'


class LocalizacaoFerramenta(models.Model):
    ferramenta = models.ForeignKey(
        Ferramenta,
        on_delete=models.CASCADE,
        related_name='localizacoes',
        verbose_name='Ferramenta',
    )

    LOCAL_TIPO_CHOICES = [
        ('deposito', 'Depósito'),
        ('obra', 'Em Obra'),
        ('manutencao', 'Manutenção'),
        ('perdida', 'Perdida/Extraviada'),
    ]
    local_tipo = models.CharField(max_length=20, choices=LOCAL_TIPO_CHOICES, verbose_name='Tipo de Local')
    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ferramentas_localizadas',
        verbose_name='Obra',
        help_text="Obrigatório apenas se local_tipo='obra'",
    )
    quantidade = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name='Quantidade',
        help_text='Quantas unidades estão neste local',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Localização de Ferramenta'
        verbose_name_plural = 'Localizações de Ferramentas'
        constraints = [
            models.UniqueConstraint(
                fields=['ferramenta', 'local_tipo'],
                condition=Q(obra__isnull=True),
                name='unique_ferramenta_local_nao_obra',
            ),
            models.UniqueConstraint(
                fields=['ferramenta', 'obra'],
                condition=Q(local_tipo='obra'),
                name='unique_ferramenta_obra',
            ),
        ]

    def __str__(self):
        if self.local_tipo == 'obra' and self.obra:
            return f'{self.ferramenta.codigo} - {self.obra.nome}: {self.quantidade} un.'
        return f'{self.ferramenta.codigo} - {self.get_local_tipo_display()}: {self.quantidade} un.'

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.local_tipo == 'obra' and not self.obra:
            raise ValidationError({'obra': 'Obra é obrigatória quando tipo de local é "Em Obra"'})
        if self.local_tipo != 'obra' and self.obra:
            raise ValidationError({'obra': 'Obra só deve ser preenchida quando tipo de local é "Em Obra"'})
        if self.quantidade < 0:
            raise ValidationError({'quantidade': 'Quantidade não pode ser negativa'})

    def save(self, *args, **kwargs):
        from django.db.models.expressions import CombinedExpression

        is_expression = isinstance(self.quantidade, CombinedExpression)
        if not is_expression:
            self.full_clean()

        if self.local_tipo != 'obra':
            self.obra = None

        if not is_expression and self.quantidade == 0:
            if self.pk:
                self.delete()
            return

        super().save(*args, **kwargs)


class MovimentacaoFerramenta(models.Model):
    ferramenta = models.ForeignKey(
        Ferramenta,
        on_delete=models.CASCADE,
        related_name='movimentacoes',
        verbose_name='Ferramenta',
    )
    quantidade = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Quantidade',
        help_text='Quantas unidades estão sendo movimentadas',
        default=1,
    )
    data_movimentacao = models.DateTimeField(auto_now_add=True, verbose_name='Data da Movimentação')

    TIPO_CHOICES = [
        ('entrada_deposito', 'Entrada no Depósito (Compra/Recebimento)'),
        ('saida_obra', 'Saída para Obra'),
        ('transferencia', 'Transferência entre Obras'),
        ('retorno_deposito', 'Retorno ao Depósito'),
        ('envio_manutencao', 'Envio para Manutenção'),
        ('retorno_manutencao', 'Retorno de Manutenção'),
        ('perda', 'Perda/Extravio'),
        ('descarte', 'Descarte/Baixa'),
        ('devolver_fornecedor', 'Devolver ao Fornecedor'),
    ]
    tipo = models.CharField(max_length=25, choices=TIPO_CHOICES, verbose_name='Tipo de Movimentação')

    origem_tipo = models.CharField(max_length=20, blank=True, verbose_name='Tipo de Origem')
    obra_origem = models.ForeignKey(
        Obra,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_saida_ferramenta',
        verbose_name='Obra Origem',
    )

    destino_tipo = models.CharField(max_length=20, blank=True, verbose_name='Tipo de Destino')
    obra_destino = models.ForeignKey(
        Obra,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_entrada_ferramenta',
        verbose_name='Obra Destino',
    )

    responsavel = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='movimentacoes_ferramenta',
        verbose_name='Responsável',
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Movimentação de Ferramenta'
        verbose_name_plural = 'Movimentações de Ferramentas'
        ordering = ['-data_movimentacao']

    def __str__(self):
        return (
            f'{self.ferramenta.codigo} - {self.quantidade} un. - '
            f'{self.get_tipo_display()} - {self.data_movimentacao.strftime("%d/%m/%Y %H:%M")}'
        )

    def get_origem_label(self):
        if self.obra_origem:
            return self.obra_origem.nome
        if self.tipo == 'entrada_deposito':
            return 'Compra/Recebimento'
        if self.tipo in {'envio_manutencao', 'perda', 'descarte', 'devolver_fornecedor'}:
            return 'Depósito'
        if self.tipo == 'retorno_manutencao':
            return 'Manutenção'
        return self.origem_tipo or '-'

    def get_destino_label(self):
        if self.obra_destino:
            return self.obra_destino.nome
        if self.tipo in {'entrada_deposito', 'retorno_deposito', 'retorno_manutencao'}:
            return 'Depósito'
        if self.tipo == 'envio_manutencao':
            return 'Manutenção'
        if self.tipo == 'perda':
            return 'Perdida/Extraviada'
        if self.tipo == 'descarte':
            return 'Baixa'
        if self.tipo == 'devolver_fornecedor':
            return self.ferramenta.fornecedor.nome if self.ferramenta.fornecedor else 'Fornecedor'
        return self.destino_tipo or '-'

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.atualizar_localizacoes()

    def atualizar_localizacoes(self):
        ferramenta = self.ferramenta
        quantidade = self.quantidade

        if self.tipo == 'entrada_deposito':
            self._adicionar_em_localizacao('deposito', None, quantidade)
            ferramenta.quantidade_total = F('quantidade_total') + quantidade
            ferramenta.save(update_fields=['quantidade_total'])
            ferramenta.refresh_from_db()

        elif self.tipo == 'saida_obra':
            self._remover_de_localizacao('deposito', None, quantidade)
            self._adicionar_em_localizacao('obra', self.obra_destino, quantidade)

        elif self.tipo == 'transferencia':
            self._remover_de_localizacao('obra', self.obra_origem, quantidade)
            self._adicionar_em_localizacao('obra', self.obra_destino, quantidade)

        elif self.tipo == 'retorno_deposito':
            self._remover_de_localizacao('obra', self.obra_origem, quantidade)
            self._adicionar_em_localizacao('deposito', None, quantidade)

        elif self.tipo == 'envio_manutencao':
            if self.obra_origem:
                self._remover_de_localizacao('obra', self.obra_origem, quantidade)
            else:
                self._remover_de_localizacao('deposito', None, quantidade)
            self._adicionar_em_localizacao('manutencao', None, quantidade)

        elif self.tipo == 'retorno_manutencao':
            self._remover_de_localizacao('manutencao', None, quantidade)
            self._adicionar_em_localizacao('deposito', None, quantidade)

        elif self.tipo == 'perda':
            if self.obra_origem:
                self._remover_de_localizacao('obra', self.obra_origem, quantidade)
            else:
                self._remover_de_localizacao('deposito', None, quantidade)
            self._adicionar_em_localizacao('perdida', None, quantidade)

        elif self.tipo == 'descarte':
            if self.obra_origem:
                self._remover_de_localizacao('obra', self.obra_origem, quantidade)
            else:
                self._remover_de_localizacao('deposito', None, quantidade)
            ferramenta.quantidade_total = F('quantidade_total') - quantidade
            ferramenta.save(update_fields=['quantidade_total'])
            ferramenta.refresh_from_db()

        elif self.tipo == 'devolver_fornecedor':
            self._remover_de_localizacao('deposito', None, quantidade)
            ferramenta.quantidade_total = F('quantidade_total') - quantidade
            ferramenta.save(update_fields=['quantidade_total'])
            ferramenta.refresh_from_db()

    def _adicionar_em_localizacao(self, local_tipo, obra, quantidade):
        filtro = {'ferramenta': self.ferramenta, 'local_tipo': local_tipo}
        if local_tipo == 'obra':
            filtro['obra'] = obra

        loc, created = LocalizacaoFerramenta.objects.get_or_create(
            **filtro,
            defaults={'quantidade': quantidade},
        )
        if not created:
            LocalizacaoFerramenta.objects.filter(pk=loc.pk).update(quantidade=F('quantidade') + quantidade)

    def _remover_de_localizacao(self, local_tipo, obra, quantidade):
        filtro = {'ferramenta': self.ferramenta, 'local_tipo': local_tipo}
        if local_tipo == 'obra':
            filtro['obra'] = obra

        try:
            loc = LocalizacaoFerramenta.objects.get(**filtro)
            LocalizacaoFerramenta.objects.filter(pk=loc.pk).update(quantidade=F('quantidade') - quantidade)
            loc.refresh_from_db()
            if loc.quantidade <= 0:
                loc.delete()
        except LocalizacaoFerramenta.DoesNotExist:
            pass


class ConferenciaFerramenta(models.Model):
    """Conferência diária de ferramentas em uma obra."""

    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='conferencias_ferramentas',
        verbose_name='Obra',
    )
    fiscal = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='conferencias_ferramentas',
        verbose_name='Fiscal',
    )
    data_conferencia = models.DateTimeField(verbose_name='Data e Hora da Conferência')
    observacoes_gerais = models.TextField(blank=True, null=True, verbose_name='Observações Gerais')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Conferência de Ferramenta'
        verbose_name_plural = 'Conferências de Ferramentas'
        ordering = ['-data_conferencia']

    def __str__(self):
        return f'Conferência {self.obra.nome} - {self.data_conferencia.strftime("%d/%m/%Y")}'

    @property
    def total_itens(self):
        return self.itens.count()

    @property
    def total_divergencias(self):
        return self.itens.exclude(status='ok').count()

    @property
    def tem_divergencias(self):
        return self.total_divergencias > 0


class ItemConferencia(models.Model):
    """Item conferido: compara quantidade esperada vs encontrada."""

    conferencia = models.ForeignKey(
        ConferenciaFerramenta,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Conferência',
    )
    ferramenta = models.ForeignKey(
        Ferramenta,
        on_delete=models.PROTECT,
        related_name='conferencias',
        verbose_name='Ferramenta',
    )
    quantidade_esperada = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name='Quantidade Esperada',
        help_text='Quantidade que deveria estar na obra segundo o sistema',
    )
    quantidade_encontrada = models.IntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name='Quantidade Encontrada',
        help_text='Quantidade realmente encontrada na conferência',
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
        verbose_name='Status',
        help_text='Calculado automaticamente',
    )
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Item de Conferência'
        verbose_name_plural = 'Itens de Conferência'
        unique_together = ['conferencia', 'ferramenta']

    def __str__(self):
        return (
            f'{self.ferramenta.codigo} - {self.get_status_display()} '
            f'(Esp: {self.quantidade_esperada}, Enc: {self.quantidade_encontrada})'
        )

    @property
    def diferenca(self):
        return self.quantidade_encontrada - self.quantidade_esperada

    def save(self, *args, **kwargs):
        if self.quantidade_encontrada == self.quantidade_esperada:
            self.status = 'ok'
        elif self.quantidade_encontrada < self.quantidade_esperada:
            self.status = 'falta'
        else:
            self.status = 'sobra'

        super().save(*args, **kwargs)
