from django import forms
from django.core.exceptions import ValidationError
from django.db import models

from apps.fornecedores.models import Fornecedor
from apps.obras.models import Obra

from .models import (
    ConferenciaFerramenta,
    Ferramenta,
    ItemConferencia,
    LocalizacaoFerramenta,
    MovimentacaoFerramenta,
)


class FerramentaForm(forms.ModelForm):
    class Meta:
        model = Ferramenta
        fields = [
            'codigo',
            'nome',
            'descricao',
            'categoria',
            'classificacao',
            'fornecedor',
            'quantidade_total',
            'valor_unitario',
            'data_aquisicao',
            'foto',
            'ativo',
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

        if 'codigo' in self.fields:
            self.fields['codigo'].required = False
            self.fields['codigo'].widget.attrs.setdefault(
                'placeholder',
                'Opcional - será gerado automaticamente se vazio',
            )

        self.fields['classificacao'].required = True
        self.fields['fornecedor'].required = False
        self.fields['fornecedor'].queryset = self.fields['fornecedor'].queryset.filter(ativo=True).order_by('nome')
        self.fields['fornecedor'].empty_label = 'Selecione um fornecedor'
        self.fields['fornecedor'].help_text = 'Obrigatório quando a ferramenta for alugada.'

        if self.instance and self.instance.pk:
            self.fields['quantidade_total'].disabled = True
            self.fields['quantidade_total'].help_text = (
                'A quantidade total é controlada automaticamente por movimentações. '
                'Para aumentar ou reduzir o estoque, use "Movimentar Ferramenta".'
            )

        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' form-select').strip()
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs['class'] = 'form-control'
            elif name != 'ativo':
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' form-control').strip()

    def clean_quantidade_total(self):
        quantidade = self.cleaned_data.get('quantidade_total')
        if quantidade is None:
            raise ValidationError('Quantidade total é obrigatória.')
        if quantidade < 0:
            raise ValidationError('Quantidade não pode ser negativa.')

        if self.instance.pk:
            soma_localizacoes = self.instance.localizacoes.aggregate(total=models.Sum('quantidade'))['total'] or 0
            if quantidade < soma_localizacoes:
                raise ValidationError(
                    f'Não é possível reduzir quantidade total para {quantidade}. '
                    f'Há {soma_localizacoes} unidades distribuídas nas localizações. '
                    f'Remova das localizações primeiro.'
                )
        return quantidade

    def clean_valor_unitario(self):
        valor = self.cleaned_data.get('valor_unitario')
        if valor is not None and valor < 0:
            raise ValidationError('Valor unitário não pode ser negativo.')
        return valor

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if not codigo and self.instance and self.instance.pk:
            return getattr(self.instance, 'codigo', '')
        return codigo

    def clean(self):
        cleaned = super().clean()
        classificacao = cleaned.get('classificacao')
        fornecedor = cleaned.get('fornecedor')

        if classificacao == 'alugada' and not fornecedor:
            self.add_error('fornecedor', 'Informe o fornecedor quando a ferramenta for alugada.')

        if classificacao == 'propria':
            cleaned['fornecedor'] = None

        return cleaned


class MovimentacaoForm(forms.ModelForm):
    fornecedor_movimentacao = forms.ModelChoiceField(
        queryset=Fornecedor.objects.none(),
        required=False,
        label='Fornecedor',
        empty_label='Selecione um fornecedor',
    )

    class Meta:
        model = MovimentacaoFerramenta
        fields = ['ferramenta', 'fornecedor_movimentacao', 'quantidade', 'tipo', 'obra_origem', 'obra_destino', 'observacoes']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['ferramenta'].queryset = Ferramenta.objects.filter(ativo=True).select_related('fornecedor').order_by('nome')
        self.fields['fornecedor_movimentacao'].queryset = Fornecedor.objects.filter(ativo=True).order_by('nome')
        self.fields['obra_origem'].queryset = Obra.objects.filter(ativo=True).order_by('nome')
        self.fields['obra_destino'].queryset = Obra.objects.filter(ativo=True).order_by('nome')
        self.fields['fornecedor_movimentacao'].help_text = (
            'Obrigatorio na entrada ao deposito de ferramenta alugada, para confirmar o fornecedor.'
        )

        ferramenta_choices = [('', 'Selecione uma ferramenta')]
        for ferramenta in self.fields['ferramenta'].queryset:
            label = f'{ferramenta.codigo} - {ferramenta.nome}'
            if ferramenta.eh_alugada and ferramenta.fornecedor:
                label = f'{label} ({ferramenta.fornecedor.nome})'
            ferramenta_choices.append((ferramenta.pk, label))
        self.fields['ferramenta'].choices = ferramenta_choices

        self.ferramenta_obras_map = self._build_ferramenta_obras_map()
        self.ferramenta_saldos_map = self._build_ferramenta_saldos_map()
        self.ferramenta_obras_quantidades_map = self._build_ferramenta_obras_quantidades_map()
        self.ferramenta_info_map = self._build_ferramenta_info_map()

        ferramenta_id = self._get_selected_ferramenta_id()
        if ferramenta_id:
            self.fields['obra_origem'].queryset = self._get_obras_origem_queryset(ferramenta_id)

        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = (existing + ' form-select').strip()
            else:
                field.widget.attrs['class'] = (existing + ' form-control').strip()

        self.fields['quantidade'].help_text = 'Quantas unidades serão movimentadas'

    def _get_selected_ferramenta_id(self):
        ferramenta_id = self.data.get('ferramenta') or self.initial.get('ferramenta')
        if not ferramenta_id and self.instance and self.instance.pk:
            ferramenta_id = self.instance.ferramenta_id
        return str(ferramenta_id) if ferramenta_id else ''

    def _get_obras_origem_queryset(self, ferramenta_id):
        return Obra.objects.filter(
            ativo=True,
            ferramentas_localizadas__ferramenta_id=ferramenta_id,
            ferramentas_localizadas__local_tipo='obra',
            ferramentas_localizadas__quantidade__gt=0,
        ).distinct().order_by('nome')

    def _build_ferramenta_obras_map(self):
        mapa = {}
        localizacoes = LocalizacaoFerramenta.objects.filter(
            local_tipo='obra',
            quantidade__gt=0,
            ferramenta__ativo=True,
            obra__ativo=True,
        ).values('ferramenta_id', 'obra_id')
        for item in localizacoes:
            ferramenta_id = str(item['ferramenta_id'])
            obra_id = item['obra_id']
            if not obra_id:
                continue
            mapa.setdefault(ferramenta_id, [])
            if obra_id not in mapa[ferramenta_id]:
                mapa[ferramenta_id].append(obra_id)
        return mapa

    def _build_ferramenta_saldos_map(self):
        mapa = {}
        ferramentas = Ferramenta.objects.filter(ativo=True).only('id', 'quantidade_total')
        for ferramenta in ferramentas:
            mapa[str(ferramenta.id)] = {
                'deposito': ferramenta.quantidade_deposito,
                'manutencao': ferramenta.quantidade_manutencao,
                'perdida': ferramenta.quantidade_perdida,
                'total': ferramenta.quantidade_total,
            }
        return mapa

    def _build_ferramenta_obras_quantidades_map(self):
        mapa = {}
        localizacoes = LocalizacaoFerramenta.objects.filter(
            local_tipo='obra',
            quantidade__gt=0,
            ferramenta__ativo=True,
            obra__ativo=True,
        ).values('ferramenta_id', 'obra_id', 'quantidade')
        for item in localizacoes:
            ferramenta_id = str(item['ferramenta_id'])
            obra_id = str(item['obra_id'])
            if not item['obra_id']:
                continue
            mapa.setdefault(ferramenta_id, {})
            mapa[ferramenta_id][obra_id] = item['quantidade']
        return mapa

    def _build_ferramenta_info_map(self):
        mapa = {}
        ferramentas = Ferramenta.objects.filter(ativo=True).select_related('fornecedor').order_by('nome')
        for ferramenta in ferramentas:
            mapa[str(ferramenta.id)] = {
                'classificacao': ferramenta.classificacao,
                'classificacao_label': ferramenta.get_classificacao_display(),
                'eh_alugada': ferramenta.eh_alugada,
                'fornecedor_id': ferramenta.fornecedor_id or '',
                'fornecedor': ferramenta.fornecedor.nome if ferramenta.fornecedor else '',
                'estoque_disponivel': ferramenta.quantidade_deposito,
                'estoque_total': ferramenta.quantidade_total,
            }
        return mapa

    def clean(self):
        cleaned = super().clean()

        ferramenta = cleaned.get('ferramenta')
        fornecedor_movimentacao = cleaned.get('fornecedor_movimentacao')
        tipo = cleaned.get('tipo')
        quantidade = cleaned.get('quantidade')
        obra_origem = cleaned.get('obra_origem')
        obra_destino = cleaned.get('obra_destino')

        if not ferramenta or not tipo or not quantidade:
            return cleaned

        if tipo == 'entrada_deposito':
            if ferramenta.eh_alugada:
                if not ferramenta.fornecedor:
                    self.add_error('ferramenta', 'Esta ferramenta alugada nao possui fornecedor vinculado.')
                if not fornecedor_movimentacao and ferramenta.fornecedor:
                    fornecedor_movimentacao = ferramenta.fornecedor
                    cleaned['fornecedor_movimentacao'] = fornecedor_movimentacao
                if not fornecedor_movimentacao:
                    self.add_error('fornecedor_movimentacao', 'Informe o fornecedor da ferramenta alugada.')
                elif ferramenta.fornecedor_id != fornecedor_movimentacao.id:
                    self.add_error(
                        'fornecedor_movimentacao',
                        'O fornecedor informado nao corresponde ao fornecedor vinculado a ferramenta selecionada.',
                    )
                    self.add_error(
                        'ferramenta',
                        'Selecione a ferramenta alugada do fornecedor correto antes de concluir a entrada.',
                    )
            else:
                cleaned['fornecedor_movimentacao'] = None
            cleaned['obra_origem'] = None
            cleaned['obra_destino'] = None
            cleaned['origem_tipo'] = 'compra'
            cleaned['destino_tipo'] = 'deposito'

        elif tipo == 'saida_obra':
            if not obra_destino:
                self.add_error('obra_destino', 'Informe a obra de destino para saída.')
                return cleaned
            qtd_disponivel = ferramenta.quantidade_deposito
            if quantidade > qtd_disponivel:
                self.add_error(
                    'quantidade',
                    f'Apenas {qtd_disponivel} unidade(s) disponível(is) no depósito. '
                    f'Você está tentando mover {quantidade}.',
                )
            cleaned['obra_origem'] = None
            cleaned['origem_tipo'] = 'deposito'
            cleaned['destino_tipo'] = 'obra'

        elif tipo == 'transferencia':
            if not obra_origem:
                self.add_error('obra_origem', 'Informe a obra de origem para transferência.')
            if not obra_destino:
                self.add_error('obra_destino', 'Informe a obra de destino para transferência.')
            if obra_origem and obra_destino and obra_origem == obra_destino:
                self.add_error('obra_destino', 'A obra de destino deve ser diferente da origem.')

            if obra_origem:
                try:
                    loc = ferramenta.localizacoes.get(local_tipo='obra', obra=obra_origem)
                    qtd_disponivel = loc.quantidade
                except LocalizacaoFerramenta.DoesNotExist:
                    qtd_disponivel = 0

                if quantidade > qtd_disponivel:
                    self.add_error(
                        'quantidade',
                        f'Apenas {qtd_disponivel} unidade(s) disponível(is) em {obra_origem.nome}. '
                        f'Você está tentando mover {quantidade}.',
                    )

            cleaned['origem_tipo'] = 'obra'
            cleaned['destino_tipo'] = 'obra'

        elif tipo == 'retorno_deposito':
            if not obra_origem:
                self.add_error('obra_origem', 'Informe a obra de origem para retorno.')

            if obra_origem:
                try:
                    loc = ferramenta.localizacoes.get(local_tipo='obra', obra=obra_origem)
                    qtd_disponivel = loc.quantidade
                except LocalizacaoFerramenta.DoesNotExist:
                    qtd_disponivel = 0

                if quantidade > qtd_disponivel:
                    self.add_error('quantidade', f'Apenas {qtd_disponivel} unidade(s) disponível(is) em {obra_origem.nome}.')

            cleaned['obra_destino'] = None
            cleaned['origem_tipo'] = 'obra'
            cleaned['destino_tipo'] = 'deposito'

        elif tipo == 'envio_manutencao':
            qtd_disponivel = ferramenta.quantidade_deposito
            if quantidade > qtd_disponivel:
                self.add_error('quantidade', f'Apenas {qtd_disponivel} unidade(s) disponível(is) no depósito.')
            cleaned['obra_origem'] = None
            cleaned['obra_destino'] = None
            cleaned['origem_tipo'] = 'deposito'
            cleaned['destino_tipo'] = 'manutencao'

        elif tipo == 'retorno_manutencao':
            qtd_disponivel = ferramenta.quantidade_manutencao
            if quantidade > qtd_disponivel:
                self.add_error('quantidade', f'Apenas {qtd_disponivel} unidade(s) em manutenção.')
            cleaned['obra_origem'] = None
            cleaned['obra_destino'] = None
            cleaned['origem_tipo'] = 'manutencao'
            cleaned['destino_tipo'] = 'deposito'

        elif tipo == 'perda':
            qtd_disponivel = ferramenta.quantidade_deposito
            if quantidade > qtd_disponivel:
                self.add_error('quantidade', f'Apenas {qtd_disponivel} unidade(s) no depósito.')
            cleaned['obra_origem'] = None
            cleaned['obra_destino'] = None
            cleaned['origem_tipo'] = 'deposito'
            cleaned['destino_tipo'] = 'perdida'

        elif tipo == 'descarte':
            qtd_disponivel = ferramenta.quantidade_deposito
            if quantidade > qtd_disponivel:
                self.add_error('quantidade', f'Apenas {qtd_disponivel} unidade(s) no depósito.')
            cleaned['obra_origem'] = None
            cleaned['obra_destino'] = None
            cleaned['origem_tipo'] = 'deposito'
            cleaned['destino_tipo'] = 'descarte'

        elif tipo == 'devolver_fornecedor':
            if not ferramenta.eh_alugada:
                self.add_error('tipo', 'Somente ferramentas alugadas podem ser devolvidas ao fornecedor.')
            if not ferramenta.fornecedor:
                self.add_error('ferramenta', 'Esta ferramenta não possui fornecedor vinculado.')
            qtd_disponivel = ferramenta.quantidade_deposito
            if quantidade > qtd_disponivel:
                self.add_error('quantidade', f'Apenas {qtd_disponivel} unidade(s) disponível(is) no depósito.')
            cleaned['obra_origem'] = None
            cleaned['obra_destino'] = None
            cleaned['origem_tipo'] = 'deposito'
            cleaned['destino_tipo'] = 'fornecedor'

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, 'cleaned_data'):
            instance.origem_tipo = self.cleaned_data.get('origem_tipo', '')
            instance.destino_tipo = self.cleaned_data.get('destino_tipo', '')
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ConferenciaForm(forms.ModelForm):
    class Meta:
        model = ConferenciaFerramenta
        fields = ['obra', 'observacoes_gerais']
        widgets = {
            'observacoes_gerais': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['obra'].queryset = Obra.objects.filter(ativo=True).order_by('nome')
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')


class ItemConferenciaForm(forms.ModelForm):
    class Meta:
        model = ItemConferencia
        fields = ['ferramenta', 'quantidade_encontrada', 'observacoes']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.obra = kwargs.pop('obra', None)
        super().__init__(*args, **kwargs)
        self.fields['ferramenta'].queryset = Ferramenta.objects.filter(ativo=True).order_by('nome')
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')
        if self.obra and 'ferramenta' in self.fields:
            self.fields['quantidade_encontrada'].help_text = 'Informe quantas unidades foram realmente encontradas na obra'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.quantidade_esperada and instance.ferramenta and self.obra:
            try:
                loc = instance.ferramenta.localizacoes.get(local_tipo='obra', obra=self.obra)
                instance.quantidade_esperada = loc.quantidade
            except LocalizacaoFerramenta.DoesNotExist:
                instance.quantidade_esperada = 0

        if commit:
            instance.save()
            self.save_m2m()
        return instance
