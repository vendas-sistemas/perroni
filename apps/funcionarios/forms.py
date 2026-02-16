from django import forms
from .models import Funcionario
from .models import ApontamentoFuncionario, FechamentoSemanal
from apps.obras.models import Obra, Etapa
import datetime
from django.core.exceptions import ValidationError


class ApontamentoForm(forms.ModelForm):
    """Formulário simplificado de apontamento individual.
    Campos essenciais visíveis + seção avançada colapsável no template."""
    class Meta:
        model = ApontamentoFuncionario
        fields = [
            'funcionario', 'obra', 'etapa', 'data', 'horas_trabalhadas',
            'clima', 'metragem_executada',
            'houve_ociosidade', 'observacao_ociosidade',
            'houve_retrabalho', 'motivo_retrabalho',
            'observacoes'
        ]
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'horas_trabalhadas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': '0.5', 'max': '24'}),
            'metragem_executada': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'm² executados'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observacao_ociosidade': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descreva o motivo da ociosidade...'}),
            'motivo_retrabalho': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descreva o motivo do retrabalho...'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            # obra will be a hidden field in the form; a text input with autocomplete is provided in the template
            'obra': forms.HiddenInput(),
            'etapa': forms.Select(attrs={'class': 'form-select'}),
            'clima': forms.Select(attrs={'class': 'form-select'}),
            'houve_ociosidade': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'houve_retrabalho': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        obra_id = kwargs.pop('obra_id', None)
        funcionario_id = kwargs.pop('funcionario_id', None)
        super().__init__(*args, **kwargs)

        obras_permitidas = Obra.objects.filter(
            ativo=True,
            status__in=['planejamento', 'em_andamento']
        ).order_by('nome')
        self.fields['obra'].queryset = obras_permitidas
        # Add a helper text field for autocomplete (not saved directly)
        self.fields['obra_nome'] = forms.CharField(
            required=False,
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Informe o nome da obra'}),
            label='Obra'
        )
        # default date to today
        if not self.instance.pk and not self.initial.get('data'):
            self.fields['data'].initial = datetime.date.today()
        # Pre-fill funcionario if provided
        if funcionario_id:
            self.fields['funcionario'].initial = funcionario_id
            self.fields['funcionario'].disabled = True  # Make it read-only
        # If instance has an obra, populate the helper field
        if self.instance and getattr(self.instance, 'obra', None):
            try:
                self.fields['obra_nome'].initial = self.instance.obra.nome
            except Exception:
                pass
        # Filter etapas by obra if provided
        if obra_id:
            self.fields['etapa'].queryset = Etapa.objects.filter(
                obra_id=obra_id,
                status='em_andamento',
            ).order_by('numero_etapa')
        elif self.instance and self.instance.pk and self.instance.obra_id:
            self.fields['etapa'].queryset = Etapa.objects.filter(
                obra_id=self.instance.obra_id,
                status='em_andamento',
            ).order_by('numero_etapa')
        elif self.data and self.data.get('obra'):
            try:
                self.fields['etapa'].queryset = Etapa.objects.filter(
                    obra_id=int(self.data['obra']),
                    status='em_andamento',
                ).order_by('numero_etapa')
            except (ValueError, TypeError):
                self.fields['etapa'].queryset = Etapa.objects.none()
        else:
            self.fields['etapa'].queryset = Etapa.objects.none()
        self.fields['etapa'].required = False
        self.fields['observacao_ociosidade'].required = False
        self.fields['motivo_retrabalho'].required = False

    def clean(self):
        cleaned = super().clean()
        obra = cleaned.get('obra')
        
        if cleaned.get('houve_ociosidade') and not cleaned.get('observacao_ociosidade'):
            self.add_error('observacao_ociosidade', 'Justificativa obrigatória quando há ociosidade.')
        if cleaned.get('houve_retrabalho') and not cleaned.get('motivo_retrabalho'):
            self.add_error('motivo_retrabalho', 'Motivo obrigatório quando há retrabalho.')

        if obra and obra.status not in ('planejamento', 'em_andamento'):
            self.add_error('obra', 'Apontamento permitido somente para obras em Planejamento ou Em Andamento.')

        etapa = cleaned.get('etapa')
        if etapa:
            if obra and etapa.obra_id != obra.id:
                self.add_error('etapa', 'A etapa selecionada não pertence à obra informada.')
            elif etapa.status != 'em_andamento':
                self.add_error('etapa', 'Selecione apenas etapas em andamento para apontamento.')
        
        return cleaned


class ApontamentoDiarioCabecalhoForm(forms.Form):
    """Cabeçalho do apontamento diário: obra, data e clima"""
    obra = forms.ModelChoiceField(
        queryset=Obra.objects.filter(
            ativo=True,
            status__in=['planejamento', 'em_andamento']
        ).order_by('nome'),
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
    """Fechamento flexível por período — usuário escolhe data_inicio e data_fim."""
    class Meta:
        model = FechamentoSemanal
        fields = ['funcionario', 'data_inicio', 'data_fim', 'observacoes']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned = super().clean()
        funcionario = cleaned.get('funcionario')
        data_inicio = cleaned.get('data_inicio')
        data_fim = cleaned.get('data_fim')
        if data_inicio and data_fim and data_fim < data_inicio:
            raise ValidationError('Data fim não pode ser anterior à data início.')
        if funcionario and data_inicio and data_fim:
            qs = FechamentoSemanal.objects.filter(
                funcionario=funcionario,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'Já existe fechamento para {funcionario.nome_completo} '
                    f'no período de {data_inicio.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")}.'
                )
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get('data_inicio'):
            self.fields['data_inicio'].initial = datetime.date.today()
        if not self.instance.pk and not self.initial.get('data_fim'):
            self.fields['data_fim'].initial = datetime.date.today() + datetime.timedelta(days=6)


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
