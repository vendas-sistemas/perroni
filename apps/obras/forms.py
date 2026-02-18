from django import forms
from .models import (
    Etapa, Etapa1Fundacao, Etapa2Estrutura, Etapa3Instalacoes,
    Etapa4Acabamentos, Etapa5Finalizacao
)


class EtapaForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em andamento'),
        ('concluida', 'Concluída'),
    ]

    class Meta:
        model = Etapa
        fields = ['percentual_valor', 'data_inicio', 'data_termino', 'status']
        widgets = {
            'data_inicio': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'data_termino': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'percentual_valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(['data_inicio', 'data_termino', 'status', 'percentual_valor'])
        self.fields['data_inicio'].input_formats = ['%Y-%m-%d']
        self.fields['data_termino'].input_formats = ['%Y-%m-%d']

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_termino = cleaned_data.get('data_termino')

        if data_inicio and data_termino and data_termino < data_inicio:
            self.add_error('data_termino', 'A data de término deve ser maior ou igual à data de início.')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


class Etapa1FundacaoForm(forms.ModelForm):
    class Meta:
        model = Etapa1Fundacao
        exclude = ('etapa',)
        widgets = {
            'limpeza_terreno': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'instalacao_energia_agua': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'marcacao_escavacao_conclusao': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'locacao_ferragem_conclusao': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'aterro_contrapiso_conclusao': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'fiadas_respaldo_conclusao': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            # Campos novos
            'levantar_alicerce_percentual': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '0.00 – 100.00'
            }),
            'rebocar_alicerce_concluido': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'impermeabilizar_alicerce_concluido': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fname in ['marcacao_escavacao_conclusao', 'locacao_ferragem_conclusao',
                      'aterro_contrapiso_conclusao', 'fiadas_respaldo_conclusao']:
            if fname in self.fields:
                self.fields[fname].input_formats = ['%Y-%m-%d']


class Etapa2EstruturaForm(forms.ModelForm):
    class Meta:
        model = Etapa2Estrutura
        exclude = ('etapa',)
        widgets = {
            'montagem_laje_conclusao': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'cobertura_conclusao': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'platibanda_blocos': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fname in ['montagem_laje_conclusao', 'cobertura_conclusao']:
            if fname in self.fields:
                self.fields[fname].input_formats = ['%Y-%m-%d']


class Etapa3InstalacoesForm(forms.ModelForm):
    class Meta:
        model = Etapa3Instalacoes
        exclude = ('etapa',)
        widgets = {
            'reboco_externo_m2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reboco_interno_m2': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'instalacao_portais': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'agua_fria': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'esgoto': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fluvial': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class Etapa4AcabamentosForm(forms.ModelForm):
    class Meta:
        model = Etapa4Acabamentos
        exclude = ('etapa',)
        widgets = {
            'pintura_externa_1demao_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'pintura_interna_1demao_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'assentamento_piso_dias': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class Etapa5FinalizacaoForm(forms.ModelForm):
    class Meta:
        model = Etapa5Finalizacao
        exclude = ('etapa',)
        widgets = {
            'pintura_externa_2demao_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'pintura_interna_2demao_dias': forms.NumberInput(attrs={'class': 'form-control'}),
        }
from django import forms
from .models import Obra
from apps.clientes.models import Cliente


class ObraForm(forms.ModelForm):
    class Meta:
        model = Obra
        fields = [
            'nome', 'endereco', 'cliente', 'data_inicio', 'data_previsao_termino',
            'status', 'percentual_concluido', 'ativo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'data_previsao_termino': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'percentual_concluido': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_percentual_concluido(self):
        pct = self.cleaned_data.get('percentual_concluido')
        if pct is None:
            return 0
        if pct < 0:
            raise forms.ValidationError('Percentual não pode ser negativo')
        if pct > 100:
            raise forms.ValidationError('Percentual não pode exceder 100')
        return pct

    # Use ModelChoiceField to present clientes, but store cliente.nome in Obra.cliente
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(ativo=True).order_by('nome'),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='(Selecione um cliente)'
    )

    def save(self, commit=True):
        # Assign the selected Cliente instance to the Obra.cliente FK
        selected = self.cleaned_data.get('cliente')
        instance = super().save(commit=False)
        if selected:
            instance.cliente = selected
        if commit:
            instance.save()
        return instance
