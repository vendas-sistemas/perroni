from django import forms
from .models import Funcionario
from .models import ApontamentoFuncionario, FechamentoSemanal
from apps.obras.models import Obra, Etapa
import datetime
from django.core.exceptions import ValidationError


class ApontamentoForm(forms.ModelForm):
    class Meta:
        model = ApontamentoFuncionario
        fields = [
            'funcionario', 'obra', 'etapa', 'data', 'horas_trabalhadas',
            'clima', 'houve_ociosidade', 'observacao_ociosidade',
            'houve_retrabalho', 'motivo_retrabalho',
            'valor_diaria', 'observacoes'
        ]
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'horas_trabalhadas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0.5', 'max': '24'}),
            'valor_diaria': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observacao_ociosidade': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descreva o motivo da ociosidade...'}),
            'motivo_retrabalho': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descreva o motivo do retrabalho...'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'obra': forms.Select(attrs={'class': 'form-select'}),
            'etapa': forms.Select(attrs={'class': 'form-select'}),
            'clima': forms.Select(attrs={'class': 'form-select'}),
            'houve_ociosidade': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'houve_retrabalho': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        obra_id = kwargs.pop('obra_id', None)
        super().__init__(*args, **kwargs)
        # default date to today
        if not self.instance.pk and not self.initial.get('data'):
            self.fields['data'].initial = datetime.date.today()
        # Filter etapas by obra if provided
        if obra_id:
            self.fields['etapa'].queryset = Etapa.objects.filter(obra_id=obra_id)
        elif self.instance and self.instance.pk and self.instance.obra_id:
            self.fields['etapa'].queryset = Etapa.objects.filter(obra_id=self.instance.obra_id)
        else:
            self.fields['etapa'].queryset = Etapa.objects.all()
        # Make etapa not required in form but encouraged
        self.fields['etapa'].required = False
        self.fields['valor_diaria'].required = False
        self.fields['observacao_ociosidade'].required = False
        self.fields['motivo_retrabalho'].required = False

    def clean(self):
        cleaned = super().clean()
        funcionario = cleaned.get('funcionario')
        data = cleaned.get('data')
        obra = cleaned.get('obra')

        if funcionario and data:
            # Validate: same funcionario should not be pointed in TWO DIFFERENT obras on same day.
            qs = ApontamentoFuncionario.objects.filter(funcionario=funcionario, data=data)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                # If any existing apontamento is for a different obra than the one being saved, block.
                different_obras = [a for a in qs if (obra and a.obra_id != obra.id)] if obra else [a for a in qs if a.obra_id is not None]
                if different_obras:
                    existing = qs.first()
                    existing_obra = existing.obra.nome if existing.obra else '(sem obra)'
                    raise ValidationError(f"Funcionário já está apontado em {existing_obra} na data {data.strftime('%d/%m/%Y')}. Remova ou edite o apontamento existente ou mova-o para outra obra.")
                # else: all existing apontamentos (if any) are for the same obra - allow multiple records for updates/extra entries.
        
        # Validate conditional required fields
        if cleaned.get('houve_ociosidade') and not cleaned.get('observacao_ociosidade'):
            self.add_error('observacao_ociosidade', 'Justificativa obrigatória quando há ociosidade.')
        if cleaned.get('houve_retrabalho') and not cleaned.get('motivo_retrabalho'):
            self.add_error('motivo_retrabalho', 'Motivo obrigatório quando há retrabalho.')
        
        return cleaned


class ApontamentoDiarioItemForm(forms.ModelForm):
    """Form para cada funcionário dentro do apontamento diário"""
    class Meta:
        model = ApontamentoFuncionario
        fields = [
            'funcionario', 'etapa', 'horas_trabalhadas',
            'houve_ociosidade', 'observacao_ociosidade',
            'houve_retrabalho', 'motivo_retrabalho',
            'valor_diaria', 'observacoes'
        ]
        widgets = {
            'horas_trabalhadas': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.5', 'min': '0.5', 'max': '24'}),
            'valor_diaria': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 1}),
            'observacao_ociosidade': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 1}),
            'motivo_retrabalho': forms.Textarea(attrs={'class': 'form-control form-control-sm', 'rows': 1}),
            'funcionario': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'etapa': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'houve_ociosidade': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'houve_retrabalho': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        obra_id = kwargs.pop('obra_id', None)
        super().__init__(*args, **kwargs)
        if obra_id:
            self.fields['etapa'].queryset = Etapa.objects.filter(obra_id=obra_id)
        self.fields['etapa'].required = False
        self.fields['valor_diaria'].required = False
        self.fields['observacao_ociosidade'].required = False
        self.fields['motivo_retrabalho'].required = False
        self.fields['funcionario'].queryset = Funcionario.objects.filter(ativo=True)


ApontamentoDiarioFormSet = forms.modelformset_factory(
    ApontamentoFuncionario,
    form=ApontamentoDiarioItemForm,
    extra=5,
    can_delete=True,
)


class ApontamentoDiarioCabecalhoForm(forms.Form):
    """Cabeçalho do apontamento diário: obra, data e clima"""
    obra = forms.ModelChoiceField(
        queryset=Obra.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Obra"
    )
    data = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=datetime.date.today,
        label="Data"
    )
    clima = forms.ChoiceField(
        choices=ApontamentoFuncionario.CLIMA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Clima"
    )


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Enhance widgets with placeholders and sizes for better layout
        self.fields['nome_completo'].widget = forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Nome completo'})
        self.fields['cpf'].widget.attrs.update({'placeholder': '000.000.000-00', 'maxlength': '14'})
        self.fields['rg'].widget.attrs.update({'placeholder': 'RG'})
        self.fields['telefone'].widget.attrs.update({'placeholder': '(11) 9xxxx-xxxx'})
        self.fields['email'].widget.attrs.update({'placeholder': 'email@exemplo.com'})
        self.fields['endereco'].widget.attrs.update({'placeholder': 'Rua, número, complemento'})
        self.fields['cidade'].widget.attrs.update({'placeholder': 'Cidade'})
        self.fields['estado'].widget.attrs.update({'placeholder': 'SP'})
        self.fields['cep'].widget.attrs.update({'placeholder': '00000-000', 'maxlength': '9'})
        # file input
        self.fields['foto'].widget = forms.ClearableFileInput(attrs={'class': 'form-control'})

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        # Basic cleanup: keep digits only
        if cpf:
            cleaned = ''.join(ch for ch in cpf if ch.isdigit())
            if len(cleaned) not in (11,):
                raise forms.ValidationError('CPF inválido (deve conter 11 dígitos).')
            return cpf
        return cpf
