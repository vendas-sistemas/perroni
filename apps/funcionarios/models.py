from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.obras.models import Obra, Etapa
from django.contrib.auth.models import User


class Funcionario(models.Model):
    """Cadastro de pedreiros e serventes"""
    
    # Dados pessoais
    nome_completo = models.CharField(max_length=200, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    rg = models.CharField(max_length=20, blank=True, null=True, verbose_name="RG")
    data_nascimento = models.DateField(blank=True, null=True, verbose_name="Data de Nascimento")
    
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
    data_admissao = models.DateField(blank=True, null=True, verbose_name="Data de Admissão")
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
    
    # Possui Placa
    possui_placa = models.BooleanField(
        default=False,
        verbose_name="Possui Placa",
        help_text="Marque se a obra possui placa de identificação"
    )
    
    # Metragem executada no dia
    metragem_executada = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Metragem Executada (m²)"
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
        ordering = ['-data', '-created_at']
        # ✅ PERMITE múltiplos registros do mesmo funcionário no mesmo dia
        # ✅ PERMITE mesmo funcionário ir e voltar da mesma obra no mesmo dia
        # Cada apontamento é único e registra um período trabalhado
        # Sem unique_together = registros ilimitados
    
    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.obra.nome} - {self.data.strftime('%d/%m/%Y')}"
    
    def save(self, *args, **kwargs):
        diaria_base = self.funcionario.valor_diaria or Decimal('0.00')

        # Auto-preenche valor da diária se não foi informado
        if self.valor_diaria is None:
            self.valor_diaria = diaria_base

        with transaction.atomic():
            super().save(*args, **kwargs)
            self._normalizar_valor_diaria_dia(diaria_base)

    def _normalizar_valor_diaria_dia(self, diaria_base):
        """Garante 1 diária por funcionário/dia (independente da quantidade de obras)."""
        qs_dia = type(self).objects.filter(
            funcionario=self.funcionario,
            data=self.data,
        ).order_by('created_at', 'pk')

        apontamento_principal_id = qs_dia.values_list('pk', flat=True).first()
        if not apontamento_principal_id:
            return

        type(self).objects.filter(pk=apontamento_principal_id).exclude(
            valor_diaria=diaria_base
        ).update(valor_diaria=diaria_base)

        type(self).objects.filter(
            funcionario=self.funcionario,
            data=self.data,
        ).exclude(pk=apontamento_principal_id).exclude(
            valor_diaria=Decimal('0.00')
        ).update(valor_diaria=Decimal('0.00'))
    
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
        # Count distinct days (one diária per date)
        dates_qs = apontamentos.values_list('data', flat=True).distinct()
        self.total_dias = dates_qs.count()

        # Total hours is sum of all apontamento rows
        self.total_horas = sum(a.horas_trabalhadas for a in apontamentos) or Decimal('0.0')

        # Calculate total_valor as one full diária per distinct date (employee
        # is paid per day regardless of hours or number of obras)
        diaria_base = self.funcionario.valor_diaria or Decimal('0.00')
        self.total_valor = (diaria_base * Decimal(self.total_dias)).quantize(Decimal('0.01'))

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
        # For each obra, track distinct dates (to count dias) and sum hours across rows
        for a in apontamentos:
            key = a.obra.nome if a.obra else '—'
            if key not in obras_etapas:
                obras_etapas[key] = {'dias_set': set(), 'dias': 0, 'horas': Decimal('0.0'), 'etapas': set()}
            # Always add hours
            obras_etapas[key]['horas'] += a.horas_trabalhadas or Decimal('0.0')
            # Count distinct days per obra
            if a.data not in obras_etapas[key]['dias_set']:
                obras_etapas[key]['dias_set'].add(a.data)
                obras_etapas[key]['dias'] += 1
            if a.etapa:
                obras_etapas[key]['etapas'].add(a.etapa.get_numero_etapa_display())

        # Cleanup: convert etapas set to sorted list and remove dias_set
        for k, v in obras_etapas.items():
            v['etapas'] = sorted(list(v['etapas']))
            v.pop('dias_set', None)

        return obras_etapas


# ----------------- Apontamento em Lote -----------------

class ApontamentoDiarioLote(models.Model):
    """
    Apontamento em LOTE de uma equipe trabalhando junta.
    Armazena a produção TOTAL do dia e divide entre os funcionários.
    """
    
    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='apontamentos_lote',
        verbose_name="Obra"
    )
    
    data = models.DateField(verbose_name="Data")
    
    etapa = models.ForeignKey(
        Etapa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Etapa"
    )
    
    # Produção TOTAL da equipe (opcional, usado quando não há campos específicos)
    producao_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        null=True,
        blank=True,
        verbose_name="Produção Total",
        help_text="Total produzido pela equipe (blocos, m², %, etc)"
    )
    
    unidade_medida = models.CharField(
        max_length=20,
        choices=[
            ('blocos', 'Blocos'),
            ('m2', 'Metros Quadrados (m²)'),
            ('percentual', 'Percentual (%)'),
        ],
        default='blocos',
        blank=True,
        verbose_name="Unidade de Medida"
    )
    
    # Clima
    clima = models.CharField(
        max_length=10,
        choices=[('sol', 'Sol'), ('chuva', 'Chuva'), ('nublado', 'Nublado')],
        default='sol',
        verbose_name="Clima"
    )
    
    # Indicadores
    houve_ociosidade = models.BooleanField(
        default=False,
        verbose_name="Houve Ociosidade"
    )
    observacao_ociosidade = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observação Ociosidade"
    )
    
    houve_retrabalho = models.BooleanField(
        default=False,
        verbose_name="Houve Retrabalho"
    )
    motivo_retrabalho = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo Retrabalho"
    )
    
    # Possui Placa
    possui_placa = models.BooleanField(
        default=False,
        verbose_name="Possui Placa",
        help_text="Marque se a obra possui placa de identificação"
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observações"
    )
    
    # Responsável pelo lançamento
    criado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Criado por"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Apontamento Diário em Lote"
        verbose_name_plural = "Apontamentos Diários em Lote"
        ordering = ['-data', '-created_at']
    
    def __str__(self):
        producao = self.producao_total if self.producao_total else Decimal('0.00')
        return f"{self.obra.nome} - {self.data.strftime('%d/%m/%Y')} - {producao} {self.unidade_medida}"
    
    def get_detalhes_producao(self):
        """
        Retorna detalhes de produção da etapa para exibição.
        Busca campos numéricos relevantes.
        """
        if not self.etapa:
            return []
        
        detalhes = []
        numero_etapa = self.etapa.numero_etapa
        
        try:
            if numero_etapa == 1 and hasattr(self.etapa, 'fundacao'):
                fund = self.etapa.fundacao
                if fund.levantar_alicerce_percentual > 0:
                    detalhes.append(f"Alicerce: {fund.levantar_alicerce_percentual}%")
                if fund.parede_7fiadas_blocos > 0:
                    detalhes.append(f"Parede 7 Fiadas: {fund.parede_7fiadas_blocos} blocos")
                    
            elif numero_etapa == 2 and hasattr(self.etapa, 'estrutura'):
                est = self.etapa.estrutura
                if est.platibanda_blocos > 0:
                    detalhes.append(f"Platibanda: {est.platibanda_blocos} blocos")
                    
            elif numero_etapa == 3 and hasattr(self.etapa, 'instalacoes'):
                inst = self.etapa.instalacoes
                if inst.reboco_externo_m2 > 0:
                    detalhes.append(f"Reboco Ext: {inst.reboco_externo_m2} m²")
                if inst.reboco_interno_m2 > 0:
                    detalhes.append(f"Reboco Int: {inst.reboco_interno_m2} m²")
        except Exception:
            pass
        
        return detalhes
    
    def get_campos_etapa_dict(self):
        """
        Retorna dicionário com valores dos campos da etapa para processamento.
        Usado para criar RegistroProducao.
        ✅ Filtra campos vazios (0, None) para evitar registros desnecessários.
        """
        if not self.etapa:
            return {}
        
        campos = {}
        numero_etapa = self.etapa.numero_etapa
        
        try:
            if numero_etapa == 1 and hasattr(self.etapa, 'fundacao'):
                fund = self.etapa.fundacao
                # ✅ Só adicionar se valor > 0
                if fund.levantar_alicerce_percentual and fund.levantar_alicerce_percentual > 0:
                    campos['alicerce_percentual'] = fund.levantar_alicerce_percentual
                if fund.parede_7fiadas_blocos and fund.parede_7fiadas_blocos > 0:
                    campos['parede_7fiadas_blocos'] = fund.parede_7fiadas_blocos
                    
            elif numero_etapa == 2 and hasattr(self.etapa, 'estrutura'):
                est = self.etapa.estrutura
                # ✅ Só adicionar se valor > 0
                if hasattr(est, 'respaldo_conclusao') and est.respaldo_conclusao and est.respaldo_conclusao > 0:
                    campos['respaldo_conclusao'] = est.respaldo_conclusao
                if hasattr(est, 'laje_conclusao') and est.laje_conclusao and est.laje_conclusao > 0:
                    campos['laje_conclusao'] = est.laje_conclusao
                if hasattr(est, 'platibanda_blocos') and est.platibanda_blocos and est.platibanda_blocos > 0:
                    campos['platibanda_metros'] = est.platibanda_blocos
                if hasattr(est, 'cobertura_conclusao') and est.cobertura_conclusao and est.cobertura_conclusao > 0:
                    campos['cobertura_conclusao'] = est.cobertura_conclusao
                    
            elif numero_etapa == 3 and hasattr(self.etapa, 'instalacoes'):
                inst = self.etapa.instalacoes
                # ✅ Só adicionar se valor > 0
                if inst.reboco_externo_m2 and inst.reboco_externo_m2 > 0:
                    campos['reboco_externo_m2'] = inst.reboco_externo_m2
                if inst.reboco_interno_m2 and inst.reboco_interno_m2 > 0:
                    campos['reboco_interno_m2'] = inst.reboco_interno_m2
                
            elif numero_etapa == 4 and hasattr(self.etapa, 'acabamentos'):
                acab = self.etapa.acabamentos
                # Adicionar campos de acabamentos se existirem
                pass
                
            elif numero_etapa == 5 and hasattr(self.etapa, 'finalizacao'):
                fin = self.etapa.finalizacao
                # Adicionar campos de finalização se existirem
                pass
                
        except Exception:
            pass
        
        return campos
    
    def gerar_apontamentos_individuais(self):
        """
        Divide a produção total entre os pedreiros da equipe
        e cria apontamentos individuais.
        """
        from apps.obras.models import EtapaHistorico
        
        # Buscar funcionários deste lote
        funcionarios_lote = self.funcionarios.all()
        
        if not funcionarios_lote.exists():
            return
        
        # Filtrar apenas PEDREIROS (serventes não contam na divisão)
        pedreiros = [f for f in funcionarios_lote if f.funcionario.funcao == 'pedreiro']
        
        if not pedreiros:
            # Se não há pedreiros, ainda assim criar apontamentos para serventes
            for func_lote in funcionarios_lote:
                self._criar_apontamento_individual(func_lote, Decimal('0.00'))
            return
        
        # Calcular produção por pedreiro (somente se producao_total foi preenchida)
        quantidade_pedreiros = len(pedreiros)
        if self.producao_total and self.producao_total > 0:
            producao_por_pedreiro = (self.producao_total / Decimal(quantidade_pedreiros)).quantize(Decimal('0.01'))
        else:
            producao_por_pedreiro = Decimal('0.00')
        
        # Criar apontamento individual para cada funcionário
        apontamentos_criados = 0
        for func_lote in funcionarios_lote:
            # Pedreiros recebem parte da produção
            # Serventes recebem 0 (mas são contabilizados no fechamento)
            if func_lote.funcionario.funcao == 'pedreiro':
                valor_produzido = producao_por_pedreiro
            else:
                valor_produzido = Decimal('0.00')
            
            self._criar_apontamento_individual(func_lote, valor_produzido)
            apontamentos_criados += 1
        
        # Registrar no histórico da etapa
        if self.etapa:
            self._registrar_historico_etapa(pedreiros)
        
        return apontamentos_criados
    
    def _criar_apontamento_individual(self, func_lote, valor_produzido):
        """Cria um apontamento individual para um funcionário"""
        ApontamentoFuncionario.objects.create(
            funcionario=func_lote.funcionario,
            obra=self.obra,
            etapa=self.etapa,
            data=self.data,
            horas_trabalhadas=func_lote.horas_trabalhadas,
            clima=self.clima,
            metragem_executada=valor_produzido,
            houve_ociosidade=self.houve_ociosidade,
            observacao_ociosidade=self.observacao_ociosidade or '',
            houve_retrabalho=self.houve_retrabalho,
            motivo_retrabalho=self.motivo_retrabalho or '',
            observacoes=self.observacoes or '',
            valor_diaria=func_lote.funcionario.valor_diaria or Decimal('0.00'),
        )
        
        # Criar registros de produção individuais
        # Usar valores do DIA (se disponíveis) ao invés de valores ACUMULADOS da etapa
        if hasattr(self, '_valores_dia'):
            # Se _valores_dia existe, usar APENAS ele (mesmo que vazio)
            # Vazio significa que nenhum campo foi preenchido no dia (não criar registros)
            campos_dict = self._valores_dia
        else:
            # Fallback: usar valores acumulados da etapa (compatibilidade com código antigo)
            campos_dict = self.get_campos_etapa_dict()
        
        # ✅ Só criar registros se houver campos com valores
        if campos_dict:
            self._criar_registro_producao(
                funcionario=func_lote.funcionario,
                obra=self.obra,
                etapa=self.etapa,
                data=self.data,
                detalhes_producao=campos_dict
            )
    
    def _registrar_historico_etapa(self, pedreiros):
        """Registra o apontamento em lote no histórico da etapa"""
        from apps.obras.models import EtapaHistorico
        
        quantidade_pedreiros = len(pedreiros)
        
        # Verificar se há produção total
        if self.producao_total and self.producao_total > 0:
            producao_por_pedreiro = (self.producao_total / Decimal(quantidade_pedreiros)).quantize(Decimal('0.01'))
        else:
            producao_por_pedreiro = Decimal('0.00')
        
        unidade_texto = {
            'blocos': 'blocos',
            'm2': 'm²',
            'percentual': '%'
        }.get(self.unidade_medida, self.unidade_medida)
        
        linhas = [
            f"🔄 APONTAMENTO EM LOTE",
            f"Obra: {self.obra.nome}",
            f"Data: {self.data.strftime('%d/%m/%Y')}",
            f"Etapa: {self.etapa.get_numero_etapa_display()}",
            f"",
        ]
        
        # Adicionar informação de produção apenas se houver
        if self.producao_total and self.producao_total > 0:
            linhas.append(f"📊 PRODUÇÃO TOTAL: {self.producao_total} {unidade_texto}")
        else:
            linhas.append(f"📊 PRODUÇÃO TOTAL: 0.00 {unidade_texto}")
        
        linhas.append(f"")
        linhas.append(f"👷 EQUIPE ({self.funcionarios.count()} funcionário(s)):")
        
        for func_lote in self.funcionarios.all():
            func = func_lote.funcionario
            if func.funcao == 'pedreiro':
                linhas.append(f"  • {func.nome_completo} (Pedreiro) - {producao_por_pedreiro} {unidade_texto}")
            else:
                linhas.append(f"  • {func.nome_completo} (Servente) - 0 {unidade_texto}")
        
        # Mostrar divisão apenas se houver produção
        if self.producao_total and self.producao_total > 0:
            linhas.append(f"")
            linhas.append(f"📋 DIVISÃO AUTOMÁTICA:")
            linhas.append(f"  {self.producao_total} {unidade_texto} ÷ {quantidade_pedreiros} pedreiro(s) = {producao_por_pedreiro} {unidade_texto}/pedreiro")
        
        if self.houve_ociosidade:
            linhas.append(f"")
            linhas.append(f"⚠️ Ociosidade: {self.observacao_ociosidade or 'Sem justificativa'}")
        
        if self.houve_retrabalho:
            linhas.append(f"")
            linhas.append(f"⚠️ Retrabalho: {self.motivo_retrabalho or 'Sem motivo informado'}")
        
        if self.observacoes:
            linhas.append(f"")
            linhas.append(f"💬 Observações: {self.observacoes}")
        
        EtapaHistorico.objects.create(
            etapa=self.etapa,
            origem='Apontamento em Lote',
            descricao='\n'.join(linhas),
            usuario=self.criado_por
        )
    
    def _criar_registro_producao(self, funcionario, obra, etapa, data, detalhes_producao):
        """Cria registros de produção individuais com base nos campos da etapa e seus valores"""
        
        # ✅ CORREÇÃO PROBLEMA 2: Mapeamento COMPLETO de campos de etapa para indicadores
        mapeamento_campos = {
            # Etapa 1 - Fundação
            'alicerce_percentual': 'alicerce_percentual',
            'levantar_alicerce_percentual': 'alicerce_percentual',
            'parede_7fiadas_blocos': 'parede_7fiadas',
            
            # Etapa 2 - Estrutura (CORRIGIDO E EXPANDIDO)
            'respaldo_conclusao': 'respaldo_conclusao',
            'fiadas_respaldo_dias': 'respaldo_conclusao',  # Alias
            'laje_conclusao': 'laje_conclusao',
            'montagem_laje_dias': 'laje_conclusao',  # Alias
            'montagem_laje_conclusao': 'laje_conclusao',  # Alias adicional
            'platibanda_metros': 'platibanda',
            'platibanda_blocos': 'platibanda',  # Alias
            'cobertura_conclusao': 'cobertura_conclusao',
            'cobertura_dias': 'cobertura_conclusao',  # Alias
            
            # Etapa 3 - Instalações
            'reboco_externo_m2': 'reboco_externo',
            'reboco_interno_m2': 'reboco_interno',
        }
        
        # ✅ CORREÇÃO PROBLEMA 1: Para cada campo que foi preenchido, criar registro APENAS SE > 0
        for campo_etapa, indicador in mapeamento_campos.items():
            if campo_etapa in detalhes_producao and detalhes_producao[campo_etapa]:
                quantidade_campo = Decimal(str(detalhes_producao[campo_etapa]))
                
                # Só criar registro se quantidade > 0 (evita registros vazios)
                if quantidade_campo > 0:
                    # Buscar funcionários do lote para dividir a produção
                    funcionarios_lote = self.funcionarios.all()
                    pedreiros = [f for f in funcionarios_lote if f.funcionario.funcao == 'pedreiro']
                    
                    if pedreiros:
                        quantidade_por_pedreiro = (quantidade_campo / Decimal(len(pedreiros))).quantize(Decimal('0.01'))
                        
                        # Verificar se o funcionário é pedreiro
                        if funcionario.funcao == 'pedreiro':
                            # Verificar se já existe um registro para este indicador neste dia
                            registro, created = RegistroProducao.objects.get_or_create(
                                funcionario=funcionario,
                                data=data,
                                obra=obra,
                                indicador=indicador,
                                defaults={
                                    'quantidade': quantidade_por_pedreiro,
                                    'etapa': etapa
                                }
                            )
                            
                            # Se já existe, somar a nova quantidade (para múltiplos apontamentos no mesmo dia)
                            if not created:
                                registro.quantidade += quantidade_por_pedreiro
                                registro.save()


class FuncionarioLote(models.Model):
    """Relaciona funcionários ao apontamento em lote"""
    
    lote = models.ForeignKey(
        ApontamentoDiarioLote,
        on_delete=models.CASCADE,
        related_name='funcionarios',
        verbose_name="Lote"
    )
    
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        verbose_name="Funcionário"
    )
    
    horas_trabalhadas = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=Decimal('8.0'),
        validators=[MinValueValidator(Decimal('0.5')), MaxValueValidator(Decimal('24.0'))],
        verbose_name="Horas Trabalhadas"
    )
    
    class Meta:
        verbose_name = "Funcionário do Lote"
        verbose_name_plural = "Funcionários do Lote"
        unique_together = ['lote', 'funcionario']
    
    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.horas_trabalhadas}h"


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


class RegistroProducao(models.Model):
    """Rastreamento de produção individual por indicador para relatórios"""
    
    # Indicadores que serão rastreados
    INDICADOR_CHOICES = [
        ('alicerce_percentual', 'Levantar Alicerce (%)'),
        ('parede_7fiadas', 'Parede até 7 Fiadas (blocos)'),
        ('respaldo_conclusao', 'Respaldo - Conclusão (%)'),
        ('laje_conclusao', 'Laje - Conclusão (%)'),
        ('platibanda', 'Platibanda (metros lineares)'),
        ('cobertura_conclusao', 'Cobertura - Conclusão (%)'),
        ('reboco_externo', 'Reboco Externo (m²)'),
        ('reboco_interno', 'Reboco Interno (m²)'),
    ]
    
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name='registros_producao',
        verbose_name="Funcionário"
    )
    
    data = models.DateField(verbose_name="Data")
    obra = models.ForeignKey(
        Obra,
        on_delete=models.CASCADE,
        related_name='registros_producao',
        verbose_name="Obra"
    )
    
    indicador = models.CharField(
        max_length=30,
        choices=INDICADOR_CHOICES,
        verbose_name="Indicador"
    )
    
    quantidade = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Quantidade Produzida"
    )
    
    etapa = models.ForeignKey(
        Etapa,
        on_delete=models.CASCADE,
        related_name='registros_producao',
        verbose_name="Etapa",
        null=True,
        blank=True
    )
    
    # Metadados
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Registro de Produção"
        verbose_name_plural = "Registros de Produção"
        unique_together = ['funcionario', 'data', 'obra', 'indicador']
        ordering = ['-data', 'funcionario__nome_completo']
        indexes = [
            models.Index(fields=['funcionario', 'data']),
            models.Index(fields=['obra', 'indicador']),
            models.Index(fields=['data', 'indicador']),
        ]
    
    def __str__(self):
        return f"{self.funcionario.nome_completo} - {self.get_indicador_display()} - {self.data.strftime('%d/%m/%Y')}"


class FotoApontamento(models.Model):
    """Fotos anexadas aos apontamentos"""
    
    apontamento_individual = models.ForeignKey(
        ApontamentoFuncionario,
        on_delete=models.CASCADE,
        related_name='fotos',
        verbose_name="Apontamento Individual",
        null=True,
        blank=True
    )
    
    apontamento_lote = models.ForeignKey(
        ApontamentoDiarioLote,
        on_delete=models.CASCADE,
        related_name='fotos',
        verbose_name="Apontamento em Lote",
        null=True,
        blank=True
    )
    
    obra = models.ForeignKey(
        'obras.Obra',
        on_delete=models.CASCADE,
        related_name='fotos_apontamentos',
        verbose_name="Obra",
        help_text="Facilita buscar todas as fotos de uma obra"
    )
    
    foto = models.ImageField(
        upload_to='apontamentos/fotos/%Y/%m/',
        verbose_name="Foto"
    )
    
    descricao = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Descrição",
        help_text="Descrição opcional da foto"
    )
    
    data_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data do Upload"
    )
    
    class Meta:
        verbose_name = "Foto do Apontamento"
        verbose_name_plural = "Fotos dos Apontamentos"
        ordering = ['-data_upload']
    
    def __str__(self):
        return f"Foto - {self.obra.nome} - {self.data_upload.strftime('%d/%m/%Y')}"
