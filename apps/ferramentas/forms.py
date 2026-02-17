from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from .models import (
    Ferramenta, MovimentacaoFerramenta, 
    ConferenciaFerramenta, ItemConferencia,
    LocalizacaoFerramenta
)
from apps.obras.models import Obra


class FerramentaForm(forms.ModelForm):
    """
    Form para cadastro/edição de ferramentas.
    Valida quantidade_total e valor_unitario.
    """
    
    class Meta:
        model = Ferramenta
        fields = [
            'codigo', 'nome', 'descricao', 'categoria',
            'quantidade_total', 'valor_unitario', 'data_aquisicao',
            'foto', 'ativo'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'data_aquisicao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor_unitario': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'quantidade_total': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Código opcional no cadastro (será gerado se vazio)
        if 'codigo' in self.fields:
            self.fields['codigo'].required = False
            self.fields['codigo'].widget.attrs.setdefault(
                'placeholder', 
                'Opcional — será gerado automaticamente se vazio'
            )
        
        # Se está editando ferramenta existente, bloquear edição da quantidade_total
        if self.instance and self.instance.pk:
            self.fields['quantidade_total'].disabled = True
            self.fields['quantidade_total'].help_text = (
                'A quantidade total é controlada automaticamente por movimentações. '
                'Para aumentar ou reduzir o estoque, use "Movimentar Ferramenta".'
            )
        
        # Aplicar classes CSS
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' form-select').strip()
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs['class'] = 'form-control'
            elif name not in ['ativo']:  # ativo já tem classe
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' form-control').strip()
    
    def clean_quantidade_total(self):
        """Valida quantidade total"""
        quantidade = self.cleaned_data.get('quantidade_total')
        
        if quantidade is None:
            raise ValidationError('Quantidade total é obrigatória.')
        
        if quantidade < 0:
            raise ValidationError('Quantidade não pode ser negativa.')
        
        # Se está editando, verificar se não está diminuindo abaixo das localizações
        if self.instance.pk:
            soma_localizacoes = self.instance.localizacoes.aggregate(
                total=models.Sum('quantidade')
            )['total'] or 0
            
            if quantidade < soma_localizacoes:
                raise ValidationError(
                    f'Não é possível reduzir quantidade total para {quantidade}. '
                    f'Há {soma_localizacoes} unidades distribuídas nas localizações. '
                    f'Remova das localizações primeiro.'
                )
        
        return quantidade
    
    def clean_valor_unitario(self):
        """Valida valor unitário"""
        valor = self.cleaned_data.get('valor_unitario')
        
        if valor is not None and valor < 0:
            raise ValidationError('Valor unitário não pode ser negativo.')
        
        return valor
    
    def clean_codigo(self):
        """Mantém código original se estiver editando e campo vazio"""
        codigo = self.cleaned_data.get('codigo')
        if not codigo and self.instance and self.instance.pk:
            return getattr(self.instance, 'codigo', '')
        return codigo


class MovimentacaoForm(forms.ModelForm):
    """
    Form para movimentação de ferramentas.
    Valida quantidade disponível baseado no tipo de movimentação.
    """
    
    class Meta:
        model = MovimentacaoFerramenta
        fields = [
            'ferramenta', 'quantidade', 'tipo', 
            'obra_origem', 'obra_destino', 'observacoes'
        ]
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apenas ferramentas ativas
        self.fields['ferramenta'].queryset = Ferramenta.objects.filter(
            ativo=True
        ).order_by('nome')
        
        # Apenas obras ativas
        self.fields['obra_origem'].queryset = Obra.objects.filter(
            ativo=True
        ).order_by('nome')
        self.fields['obra_destino'].queryset = Obra.objects.filter(
            ativo=True
        ).order_by('nome')
        
        # Aplicar classes CSS
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = (existing + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (existing + ' form-control').strip()
        
        # Help texts dinâmicos
        self.fields['quantidade'].help_text = (
            'Quantas unidades serão movimentadas'
        )
    
    def clean(self):
        """
        Validação complexa baseada no tipo de movimentação.
        Verifica se há quantidade disponível no local de origem.
        """
        cleaned = super().clean()
        
        ferramenta = cleaned.get('ferramenta')
        tipo = cleaned.get('tipo')
        quantidade = cleaned.get('quantidade')
        obra_origem = cleaned.get('obra_origem')
        obra_destino = cleaned.get('obra_destino')
        
        if not ferramenta or not tipo or not quantidade:
            return cleaned
        
        # ========== ENTRADA NO DEPÓSITO ==========
        if tipo == 'entrada_deposito':
            # Não precisa validar disponibilidade (está entrando no estoque)
            cleaned['origem_tipo'] = 'compra'
            cleaned['destino_tipo'] = 'deposito'
        
        # ========== SAÍDA PARA OBRA ==========
        elif tipo == 'saida_obra':
            if not obra_destino:
                self.add_error(
                    'obra_destino',
                    'Informe a obra de destino para saída.'
                )
                return cleaned
            
            # Verificar quantidade disponível NO DEPÓSITO
            qtd_disponivel = ferramenta.quantidade_deposito
            
            if quantidade > qtd_disponivel:
                self.add_error(
                    'quantidade',
                    f'Apenas {qtd_disponivel} unidade(s) disponível(is) no depósito. '
                    f'Você está tentando mover {quantidade}.'
                )
            
            cleaned['origem_tipo'] = 'deposito'
            cleaned['destino_tipo'] = 'obra'
        
        # ========== TRANSFERÊNCIA ENTRE OBRAS ==========
        elif tipo == 'transferencia':
            if not obra_origem:
                self.add_error(
                    'obra_origem',
                    'Informe a obra de origem para transferência.'
                )
            if not obra_destino:
                self.add_error(
                    'obra_destino',
                    'Informe a obra de destino para transferência.'
                )
            
            if obra_origem and obra_destino and obra_origem == obra_destino:
                self.add_error(
                    'obra_destino',
                    'A obra de destino deve ser diferente da origem.'
                )
            
            if obra_origem:
                # Verificar quantidade disponível NA OBRA ORIGEM
                try:
                    loc = ferramenta.localizacoes.get(
                        local_tipo='obra',
                        obra=obra_origem
                    )
                    qtd_disponivel = loc.quantidade
                except LocalizacaoFerramenta.DoesNotExist:
                    qtd_disponivel = 0
                
                if quantidade > qtd_disponivel:
                    self.add_error(
                        'quantidade',
                        f'Apenas {qtd_disponivel} unidade(s) disponível(is) '
                        f'em {obra_origem.nome}. Você está tentando mover {quantidade}.'
                    )
            
            cleaned['origem_tipo'] = 'obra'
            cleaned['destino_tipo'] = 'obra'
        
        # ========== RETORNO AO DEPÓSITO ==========
        elif tipo == 'retorno_deposito':
            if not obra_origem:
                self.add_error(
                    'obra_origem',
                    'Informe a obra de origem para retorno.'
                )
            
            if obra_origem:
                # Verificar quantidade disponível NA OBRA
                try:
                    loc = ferramenta.localizacoes.get(
                        local_tipo='obra',
                        obra=obra_origem
                    )
                    qtd_disponivel = loc.quantidade
                except LocalizacaoFerramenta.DoesNotExist:
                    qtd_disponivel = 0
                
                if quantidade > qtd_disponivel:
                    self.add_error(
                        'quantidade',
                        f'Apenas {qtd_disponivel} unidade(s) disponível(is) '
                        f'em {obra_origem.nome}.'
                    )
            
            cleaned['origem_tipo'] = 'obra'
            cleaned['destino_tipo'] = 'deposito'
        
        # ========== ENVIO PARA MANUTENÇÃO ==========
        elif tipo == 'envio_manutencao':
            # Pode ser do depósito ou de uma obra
            if obra_origem:
                # Vindo de obra
                try:
                    loc = ferramenta.localizacoes.get(
                        local_tipo='obra',
                        obra=obra_origem
                    )
                    qtd_disponivel = loc.quantidade
                except LocalizacaoFerramenta.DoesNotExist:
                    qtd_disponivel = 0
                
                if quantidade > qtd_disponivel:
                    self.add_error(
                        'quantidade',
                        f'Apenas {qtd_disponivel} unidade(s) disponível(is) '
                        f'em {obra_origem.nome}.'
                    )
                cleaned['origem_tipo'] = 'obra'
            else:
                # Vindo do depósito
                qtd_disponivel = ferramenta.quantidade_deposito
                if quantidade > qtd_disponivel:
                    self.add_error(
                        'quantidade',
                        f'Apenas {qtd_disponivel} unidade(s) disponível(is) no depósito.'
                    )
                cleaned['origem_tipo'] = 'deposito'
            
            cleaned['destino_tipo'] = 'manutencao'
        
        # ========== RETORNO DE MANUTENÇÃO ==========
        elif tipo == 'retorno_manutencao':
            # Verificar quantidade em manutenção
            qtd_disponivel = ferramenta.quantidade_manutencao
            
            if quantidade > qtd_disponivel:
                self.add_error(
                    'quantidade',
                    f'Apenas {qtd_disponivel} unidade(s) em manutenção.'
                )
            
            cleaned['origem_tipo'] = 'manutencao'
            cleaned['destino_tipo'] = 'deposito'
        
        # ========== PERDA/EXTRAVIO ==========
        elif tipo == 'perda':
            if obra_origem:
                # Perda em obra
                try:
                    loc = ferramenta.localizacoes.get(
                        local_tipo='obra',
                        obra=obra_origem
                    )
                    qtd_disponivel = loc.quantidade
                except LocalizacaoFerramenta.DoesNotExist:
                    qtd_disponivel = 0
                
                if quantidade > qtd_disponivel:
                    self.add_error(
                        'quantidade',
                        f'Apenas {qtd_disponivel} unidade(s) em {obra_origem.nome}.'
                    )
                cleaned['origem_tipo'] = 'obra'
            else:
                # Perda no depósito
                qtd_disponivel = ferramenta.quantidade_deposito
                if quantidade > qtd_disponivel:
                    self.add_error(
                        'quantidade',
                        f'Apenas {qtd_disponivel} unidade(s) no depósito.'
                    )
                cleaned['origem_tipo'] = 'deposito'
            
            cleaned['destino_tipo'] = 'perdida'
        
        # ========== DESCARTE ==========
        elif tipo == 'descarte':
            if obra_origem:
                # Descarte de obra
                try:
                    loc = ferramenta.localizacoes.get(
                        local_tipo='obra',
                        obra=obra_origem
                    )
                    qtd_disponivel = loc.quantidade
                except LocalizacaoFerramenta.DoesNotExist:
                    qtd_disponivel = 0
                
                if quantidade > qtd_disponivel:
                    self.add_error(
                        'quantidade',
                        f'Apenas {qtd_disponivel} unidade(s) em {obra_origem.nome}.'
                    )
                cleaned['origem_tipo'] = 'obra'
            else:
                # Descarte do depósito
                qtd_disponivel = ferramenta.quantidade_deposito
                if quantidade > qtd_disponivel:
                    self.add_error(
                        'quantidade',
                        f'Apenas {qtd_disponivel} unidade(s) no depósito.'
                    )
                cleaned['origem_tipo'] = 'deposito'
            
            cleaned['destino_tipo'] = 'descarte'
        
        return cleaned
    
    def save(self, commit=True):
        """Injeta origem_tipo e destino_tipo antes de salvar"""
        instance = super().save(commit=False)
        
        # Pegar do cleaned_data
        if hasattr(self, 'cleaned_data'):
            instance.origem_tipo = self.cleaned_data.get('origem_tipo', '')
            instance.destino_tipo = self.cleaned_data.get('destino_tipo', '')
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class ConferenciaForm(forms.ModelForm):
    """Form para criar conferência"""
    
    class Meta:
        model = ConferenciaFerramenta
        fields = ['obra', 'observacoes_gerais']
        widgets = {
            'observacoes_gerais': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Apenas obras ativas
        self.fields['obra'].queryset = Obra.objects.filter(ativo=True).order_by('nome')
        
        # CSS
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')


class ItemConferenciaForm(forms.ModelForm):
    """
    Form para item de conferência.
    Auto-preenche quantidade_esperada baseado na obra.
    """
    
    class Meta:
        model = ItemConferencia
        fields = ['ferramenta', 'quantidade_encontrada', 'observacoes']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        # Pegar obra da conferência se disponível
        self.obra = kwargs.pop('obra', None)
        super().__init__(*args, **kwargs)
        
        # Apenas ferramentas ativas
        self.fields['ferramenta'].queryset = Ferramenta.objects.filter(
            ativo=True
        ).order_by('nome')
        
        # CSS
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')
        
        # Se tem obra, auto-preencher quantidade_esperada no help_text
        if self.obra and 'ferramenta' in self.fields:
            self.fields['quantidade_encontrada'].help_text = (
                'Informe quantas unidades foram realmente encontradas na obra'
            )
    
    def save(self, commit=True):
        """Auto-preenche quantidade_esperada antes de salvar"""
        instance = super().save(commit=False)
        
        # Se não tem quantidade_esperada preenchida, pegar da localização
        if not instance.quantidade_esperada and instance.ferramenta and self.obra:
            try:
                loc = instance.ferramenta.localizacoes.get(
                    local_tipo='obra',
                    obra=self.obra
                )
                instance.quantidade_esperada = loc.quantidade
            except LocalizacaoFerramenta.DoesNotExist:
                instance.quantidade_esperada = 0
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance
