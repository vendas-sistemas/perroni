from django import forms
from .models import Ferramenta
from .models import MovimentacaoFerramenta, ConferenciaFerramenta, ItemConferencia
from django.utils import timezone
from django.forms import ModelForm
import datetime


class FerramentaForm(forms.ModelForm):
    class Meta:
        model = Ferramenta
        fields = [
            'codigo', 'nome', 'descricao', 'categoria', 'status',
            'obra_atual', 'data_aquisicao', 'valor_aquisicao', 'foto', 'ativo'
        ]
        widgets = {
            'data_aquisicao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor_aquisicao': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' form-select').strip()
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs['class'] = 'form-control'
            else:
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' form-control').strip()


class MovimentacaoForm(ModelForm):
    class Meta:
        model = MovimentacaoFerramenta
        fields = ['ferramenta', 'tipo', 'obra_origem', 'obra_destino', 'origem', 'destino', 'observacoes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()


class ConferenciaForm(ModelForm):
    class Meta:
        model = ConferenciaFerramenta
        # Do not expose `data_conferencia` to users; it will be set automatically
        fields = ['obra']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')


class ItemConferenciaForm(ModelForm):
    class Meta:
        model = ItemConferencia
        # Do not include the parent FK `conferencia` in the form used by the
        # inline formset — the formset/parent instance will set this automatically.
        fields = ['ferramenta', 'status', 'observacoes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
