from django import forms
from .models import Ferramenta


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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            # Leave file input and select widgets as-is; add bootstrap classes otherwise
            if not isinstance(field.widget, (forms.ClearableFileInput, forms.Select, forms.SelectMultiple)):
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' form-control').strip()
