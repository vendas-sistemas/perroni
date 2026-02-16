from django import forms
from apps.obras.models import Obra, Etapa
from apps.funcionarios.models import Funcionario, ApontamentoFuncionario


class FiltroRelatorioForm(forms.Form):
    """Formulário de filtros para os relatórios de produção."""

    obra = forms.ModelChoiceField(
        queryset=Obra.objects.filter(ativo=True),
        required=False,
        empty_label='Todas as Obras',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    etapa = forms.ModelChoiceField(
        queryset=Etapa.objects.none(),
        required=False,
        empty_label='Todas as Etapas',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.filter(ativo=True),
        required=False,
        empty_label='Todos os Funcionários',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    data_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Data Início',
    )
    data_fim = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Data Fim',
    )
    clima = forms.ChoiceField(
        choices=[('', 'Todos')] + ApontamentoFuncionario.CLIMA_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Clima',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        obra_id = self.data.get('obra') or self.initial.get('obra')
        if obra_id:
            try:
                self.fields['etapa'].queryset = Etapa.objects.filter(obra_id=int(obra_id)).order_by('numero_etapa')
            except (TypeError, ValueError):
                self.fields['etapa'].queryset = Etapa.objects.none()
        else:
            self.fields['etapa'].queryset = Etapa.objects.none()

    def get_filtros(self) -> dict:
        """Retorna dict de filtros limpos para passar ao serviço."""
        if not self.is_valid():
            return {}
        d = self.cleaned_data
        filtros = {}
        if d.get('obra'):
            filtros['obra_id'] = d['obra'].pk
        if d.get('etapa'):
            filtros['etapa_id'] = d['etapa'].pk
        if d.get('funcionario'):
            filtros['funcionario_id'] = d['funcionario'].pk
        if d.get('data_inicio'):
            filtros['data_inicio'] = d['data_inicio']
        if d.get('data_fim'):
            filtros['data_fim'] = d['data_fim']
        if d.get('clima'):
            filtros['clima'] = d['clima']
        return filtros
