from django import forms
from .models import (
    Etapa, Etapa1Fundacao, Etapa2Estrutura, Etapa3Instalacoes,
    Etapa4Acabamentos, Etapa5Finalizacao
)


class EtapaForm(forms.ModelForm):
    class Meta:
        model = Etapa
        fields = ['numero_etapa', 'percentual_valor', 'data_inicio', 'data_termino', 'concluida']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_termino': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'percentual_valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'concluida': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'numero_etapa': forms.Select(attrs={'class': 'form-select'})
        }


class Etapa1FundacaoForm(forms.ModelForm):
    class Meta:
        model = Etapa1Fundacao
        exclude = ('etapa',)
        widgets = {
            'marcacao_escavacao_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'locacao_ferragem_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'alicerce_percentual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'aterro_contrapiso_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'parede_7fiadas_blocos': forms.NumberInput(attrs={'class': 'form-control'}),
            'fiadas_respaldo_dias': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class Etapa2EstruturaForm(forms.ModelForm):
    class Meta:
        model = Etapa2Estrutura
        exclude = ('etapa',)
        widgets = {
            'montagem_laje_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'platibanda_blocos': forms.NumberInput(attrs={'class': 'form-control'}),
            'cobertura_dias': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class Etapa3InstalacoesForm(forms.ModelForm):
    class Meta:
        model = Etapa3Instalacoes
        exclude = ('etapa',)
        widgets = {
            'reboco_externo_m2': forms.NumberInput(attrs={'class': 'form-control'}),
            'reboco_interno_m2': forms.NumberInput(attrs={'class': 'form-control'}),
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
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_previsao_termino': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
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
        # Pop the cliente from cleaned_data to avoid ModelForm attempting to assign the Cliente instance
        selected = self.cleaned_data.pop('cliente', None)
        instance = super().save(commit=False)
        if selected:
            instance.cliente = selected.nome
        if commit:
            instance.save()
        return instance
