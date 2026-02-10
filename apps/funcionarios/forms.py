from django import forms
from .models import Funcionario
from .models import ApontamentoFuncionario, FechamentoSemanal
import datetime


class ApontamentoForm(forms.ModelForm):
    class Meta:
        model = ApontamentoFuncionario
        fields = ['funcionario', 'obra', 'data', 'valor_diaria', 'observacoes']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor_diaria': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'obra': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # default date to today
        if not self.instance.pk and not self.initial.get('data'):
            self.fields['data'].initial = datetime.date.today()


class FechamentoForm(forms.ModelForm):
    class Meta:
        model = FechamentoSemanal
        fields = ['funcionario', 'data_inicio', 'observacoes']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get('data_inicio'):
            self.fields['data_inicio'].initial = datetime.date.today()


class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = [
            'nome_completo', 'cpf', 'rg', 'data_nascimento',
            'telefone', 'email', 'endereco', 'cidade', 'estado', 'cep',
            'funcao', 'valor_diaria', 'foto', 'ativo', 'data_admissao', 'data_demissao', 'motivo_inativacao'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_admissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_demissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'motivo_inativacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valor_diaria': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control'}),
            'funcao': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        # Basic cleanup: keep digits only
        if cpf:
            cleaned = ''.join(ch for ch in cpf if ch.isdigit())
            if len(cleaned) not in (11,):
                raise forms.ValidationError('CPF inválido (deve conter 11 dígitos).')
            return cpf
        return cpf
