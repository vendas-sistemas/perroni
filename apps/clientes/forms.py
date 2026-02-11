from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'cpf', 'endereco', 'data_nascimento', 'telefone', 'email', 'ativo']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            # Boolean fields (checkbox) should use Bootstrap switch
            if isinstance(field, forms.BooleanField):
                field.widget = forms.CheckboxInput(attrs={
                    'class': 'form-check-input',
                    'role': 'switch',
                })
            else:
                field.widget.attrs.setdefault('class', 'form-control')

        # Em formulários de criação, marcar 'ativo' como True por padrão
        if not getattr(self.instance, 'pk', None):
            if 'ativo' in self.fields:
                self.fields['ativo'].initial = True
