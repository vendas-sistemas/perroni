from django import forms

from .models import Fornecedor


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'endereco', 'telefone', 'ativo']
        widgets = {
            'endereco': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.BooleanField):
                field.widget = forms.CheckboxInput(attrs={
                    'class': 'form-check-input',
                    'role': 'switch',
                })
            else:
                field.widget.attrs.setdefault('class', 'form-control')

        if not getattr(self.instance, 'pk', None) and 'ativo' in self.fields:
            self.fields['ativo'].initial = True

